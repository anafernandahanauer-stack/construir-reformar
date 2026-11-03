"""
Camada de acesso ao banco — funciona em dois back-ends:
  • SQLite  (local, padrão)         — arquivo hub.db
  • Postgres (produção)             — quando a variável de ambiente DATABASE_URL
                                       começa com postgres:// ou postgresql://

O código da aplicação usa sempre placeholders com '?'; aqui traduzimos para '%s'
quando o back-end é Postgres.
"""
import os
from pathlib import Path

_DB_URL = os.environ.get("DATABASE_URL", "")
BACKEND = "postgres" if _DB_URL.startswith(("postgres://", "postgresql://")) else "sqlite"
_SCHEMA = os.environ.get("DB_SCHEMA", "").strip()

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "hub.db"

# ---------------------------------------------------------------- DDL por dialeto
_DDL_SQLITE = """
CREATE TABLE IF NOT EXISTS categorias (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    nome  TEXT NOT NULL UNIQUE,
    slug  TEXT NOT NULL UNIQUE,
    icone TEXT NOT NULL DEFAULT '🔧'
);
CREATE TABLE IF NOT EXISTS regioes (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    nome  TEXT NOT NULL,
    uf    TEXT NOT NULL,
    slug  TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS prestadores (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    nome         TEXT NOT NULL,
    categoria_id INTEGER NOT NULL REFERENCES categorias(id),
    regiao_id    INTEGER REFERENCES regioes(id),
    telefone     TEXT, whatsapp TEXT, descricao TEXT,
    foto_url     TEXT,
    verificado   INTEGER NOT NULL DEFAULT 0,
    criado_em    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS prestador_fotos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    prestador_id INTEGER NOT NULL REFERENCES prestadores(id) ON DELETE CASCADE,
    url          TEXT NOT NULL,
    criado_em    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS usuarios (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    nome         TEXT,
    email        TEXT NOT NULL UNIQUE,
    senha_hash   TEXT NOT NULL,
    papel        TEXT NOT NULL DEFAULT 'prestador',
    prestador_id INTEGER REFERENCES prestadores(id) ON DELETE CASCADE,
    criado_em    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS avaliacoes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    prestador_id INTEGER NOT NULL REFERENCES prestadores(id) ON DELETE CASCADE,
    usuario_id   INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    autor        TEXT NOT NULL,
    nota         INTEGER NOT NULL CHECK (nota BETWEEN 1 AND 5),
    comentario   TEXT,
    foto_url     TEXT,
    status       TEXT NOT NULL DEFAULT 'pendente',
    criado_em    TEXT NOT NULL DEFAULT (datetime('now','localtime'))
);
CREATE TABLE IF NOT EXISTS uso_diario (
    dia    TEXT NOT NULL,
    tipo   TEXT NOT NULL,
    chave  TEXT NOT NULL,
    n      INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (dia, tipo, chave)
);
CREATE INDEX IF NOT EXISTS idx_prestadores_categoria ON prestadores(categoria_id);
CREATE INDEX IF NOT EXISTS idx_avaliacoes_prestador ON avaliacoes(prestador_id);
CREATE INDEX IF NOT EXISTS idx_avaliacoes_status ON avaliacoes(status);
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
"""
# idx_prestadores_regiao fica de fora daqui de propósito: em bancos que já tinham
# a tabela prestadores (upgrade), a coluna regiao_id só existe depois de
# _migrar_colunas() rodar — criar o índice aqui, no mesmo lote do CREATE TABLE
# IF NOT EXISTS (que é no-op numa tabela já existente), falha com
# "column regiao_id does not exist".

_DDL_POSTGRES = """
CREATE TABLE IF NOT EXISTS categorias (
    id    SERIAL PRIMARY KEY,
    nome  TEXT NOT NULL UNIQUE,
    slug  TEXT NOT NULL UNIQUE,
    icone TEXT NOT NULL DEFAULT '🔧'
);
CREATE TABLE IF NOT EXISTS regioes (
    id    SERIAL PRIMARY KEY,
    nome  TEXT NOT NULL,
    uf    TEXT NOT NULL,
    slug  TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS prestadores (
    id           SERIAL PRIMARY KEY,
    nome         TEXT NOT NULL,
    categoria_id INTEGER NOT NULL REFERENCES categorias(id),
    regiao_id    INTEGER REFERENCES regioes(id),
    telefone     TEXT, whatsapp TEXT, descricao TEXT,
    foto_url     TEXT,
    verificado   INTEGER NOT NULL DEFAULT 0,
    criado_em    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS prestador_fotos (
    id           SERIAL PRIMARY KEY,
    prestador_id INTEGER NOT NULL REFERENCES prestadores(id) ON DELETE CASCADE,
    url          TEXT NOT NULL,
    criado_em    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS usuarios (
    id           SERIAL PRIMARY KEY,
    nome         TEXT,
    email        TEXT NOT NULL UNIQUE,
    senha_hash   TEXT NOT NULL,
    papel        TEXT NOT NULL DEFAULT 'prestador',
    prestador_id INTEGER REFERENCES prestadores(id) ON DELETE CASCADE,
    criado_em    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS avaliacoes (
    id           SERIAL PRIMARY KEY,
    prestador_id INTEGER NOT NULL REFERENCES prestadores(id) ON DELETE CASCADE,
    usuario_id   INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    autor        TEXT NOT NULL,
    nota         INTEGER NOT NULL CHECK (nota BETWEEN 1 AND 5),
    comentario   TEXT,
    foto_url     TEXT,
    status       TEXT NOT NULL DEFAULT 'pendente',
    criado_em    TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS uso_diario (
    dia    TEXT NOT NULL,
    tipo   TEXT NOT NULL,
    chave  TEXT NOT NULL,
    n      INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (dia, tipo, chave)
);
CREATE INDEX IF NOT EXISTS idx_prestadores_categoria ON prestadores(categoria_id);
CREATE INDEX IF NOT EXISTS idx_avaliacoes_prestador ON avaliacoes(prestador_id);
CREATE INDEX IF NOT EXISTS idx_avaliacoes_status ON avaliacoes(status);
CREATE INDEX IF NOT EXISTS idx_usuarios_email ON usuarios(email);
"""
# (idx_prestadores_regiao: ver comentário acima do bloco _DDL_POSTGRES — mesma razão,
# criado depois da migração de colunas, não aqui.)

# ---------------------------------------------------------------- migração incremental
# Bancos criados antes desta versão têm prestadores.cidade (texto livre) e não têm
# as colunas/tabelas novas. As checagens abaixo são idempotentes: rodam a cada
# startup e só alteram o que ainda não existe, para não quebrar produção.
_COLUNAS_NOVAS = {
    "prestadores": [("regiao_id", "INTEGER"), ("foto_url", "TEXT"),
                    # oferta/voucher criado pelo próprio prestador (validade em AAAA-MM-DD)
                    ("oferta_texto", "TEXT"), ("oferta_validade", "TEXT")],
    "usuarios": [("nome", "TEXT"), ("aceite_termos_em", "TEXT"), ("aceite_termos_versao", "TEXT")],
    # as 5 métricas da avaliação (1 a 5); 'nota' continua sendo a média arredondada
    "avaliacoes": [("usuario_id", "INTEGER"), ("foto_url", "TEXT"),
                   ("m_atendimento", "INTEGER"), ("m_qualidade", "INTEGER"), ("m_seguranca", "INTEGER"),
                   ("m_resolveu", "INTEGER"), ("m_indicaria", "INTEGER")],
}


def _colunas_existentes(cur, tabela):
    if BACKEND == "sqlite":
        cur.execute(f"PRAGMA table_info({tabela})")
        return {row[1] for row in cur.fetchall()}
    # Filtra pelo schema em uso: sem isso, colunas de uma tabela homônima no
    # 'public' fazem a migração achar que a coluna já existe no schema de
    # produção, pular o ALTER e o cadastro quebrar com "column ... does not exist".
    cur.execute(
        "SELECT column_name FROM information_schema.columns "
        "WHERE table_schema = current_schema() AND table_name = %s",
        (tabela,),
    )
    return {row["column_name"] for row in cur.fetchall()}


def _migrar_colunas(cur):
    for tabela, colunas in _COLUNAS_NOVAS.items():
        existentes = _colunas_existentes(cur, tabela)
        for nome, tipo in colunas:
            if nome not in existentes:
                cur.execute(f"ALTER TABLE {tabela} ADD COLUMN {nome} {tipo}")


def _migrar_cidade_para_regiao(cur):
    """Prestadores antigos tinham só o texto 'cidade'; até hoje essa era sempre
    'Sorriso/MT', então o backfill aponta todos os órfãos para essa região."""
    existentes = _colunas_existentes(cur, "prestadores")
    if "cidade" not in existentes:
        return  # já migrado
    cur.execute(_prep("SELECT id FROM regioes WHERE slug = ?"), ("sorriso-mt",))
    row = cur.fetchone()
    if not row:
        cur.execute(
            _prep("INSERT INTO regioes (nome, uf, slug) VALUES (?,?,?)"),
            ("Sorriso", "MT", "sorriso-mt"),
        )
        cur.execute(_prep("SELECT id FROM regioes WHERE slug = ?"), ("sorriso-mt",))
        row = cur.fetchone()
    regiao_id = row["id"] if BACKEND == "postgres" else row[0]
    cur.execute(
        _prep("UPDATE prestadores SET regiao_id = ? WHERE regiao_id IS NULL"),
        (regiao_id,),
    )
    try:
        cur.execute("ALTER TABLE prestadores DROP COLUMN cidade")
    except Exception:
        # SQLite < 3.35 não suporta DROP COLUMN; a coluna fica órfã e sem uso,
        # sem risco — o código da aplicação não lê nem escreve mais nela.
        pass


# ---------------------------------------------------------------- conexão
# Postgres: pool de conexões por processo. Antes, cada consulta abria uma conexão
# nova (TLS + autenticação, ~5 por página). O pool reaproveita conexões abertas.
#
# O search_path vai com SET LOCAL no começo de cada transação, e não uma vez por
# conexão: funciona igual no pooler do Supabase em modo sessão ou transação, e
# nunca deixa uma conexão reaproveitada cair no schema errado.
_POOL_MAX = int(os.environ.get("DB_POOL_MAX", "4") or 4)


class _Pool:
    """Pool mínimo: abre conexão só quando falta, guarda até _POOL_MAX paradas e,
    com todas em uso, faz a requisição esperar a vez (em vez de dar erro).
    (O ThreadedConnectionPool do psycopg2 fecha toda conexão acima do mínimo ao
    devolvê-la — na prática voltaria a abrir uma por consulta.)"""

    def __init__(self, maximo):
        import threading
        self.vagas = threading.BoundedSemaphore(maximo)
        self.trava = threading.Lock()
        self.paradas = []
        self.pid = os.getpid()

    def pegar(self):
        if not self.vagas.acquire(timeout=30):
            raise RuntimeError("banco ocupado: nenhuma conexão livre em 30 s")
        with self.trava:
            conn = self.paradas.pop() if self.paradas else None
        if conn is None:
            try:
                import psycopg2
                from psycopg2.extras import RealDictCursor
                conn = psycopg2.connect(_DB_URL, cursor_factory=RealDictCursor)
            except Exception:
                self.vagas.release()
                raise
        return conn

    def esvaziar(self):
        with self.trava:
            paradas, self.paradas = self.paradas, []
        for conn in paradas:
            try:
                conn.close()
            except Exception:
                pass

    def devolver(self, conn, fechar=False):
        try:
            if fechar or conn.closed:
                try:
                    conn.close()
                except Exception:
                    pass
            else:
                with self.trava:
                    self.paradas.append(conn)
        finally:
            self.vagas.release()


_POOL = None


def _pool():
    global _POOL
    # gunicorn --preload abre o app no processo mestre e depois faz fork: um
    # pool herdado compartilharia sockets entre processos. Um pool por PID.
    if _POOL is None or _POOL.pid != os.getpid():
        _POOL = _Pool(_POOL_MAX)
    return _POOL


def _preparar(conn):
    """Abre a transação com o schema certo. Serve também de teste de vida da
    conexão: se o servidor a derrubou enquanto ela estava parada no pool, o erro
    aparece aqui, antes de qualquer gravação."""
    if _SCHEMA:
        with conn.cursor() as cur:
            cur.execute('SET LOCAL search_path TO "%s", public' % _SCHEMA.replace('"', ""))


def _pegar_conn():
    import psycopg2
    pool = _pool()
    for tentativa in range(3):
        conn = pool.pegar()
        try:
            if conn.closed:
                raise psycopg2.InterfaceError("conexão fechada")
            _preparar(conn)
            return conn
        except (psycopg2.OperationalError, psycopg2.InterfaceError):
            # Uma conexão morta costuma vir com as irmãs (o pooler reiniciou, a
            # instância dormiu): descarta todas as paradas e abre uma nova.
            pool.devolver(conn, fechar=True)
            pool.esvaziar()
            if tentativa == 2:
                raise
    raise RuntimeError("sem conexão com o banco")


def _devolver(conn, erro=False):
    if BACKEND == "sqlite":
        conn.close()
        return
    fechar = bool(conn.closed)
    try:
        if not conn.closed and conn.status != 1:  # 1 = STATUS_READY
            conn.rollback()
    except Exception:
        fechar = True  # conexão em estado duvidoso não volta para o pool
    _pool().devolver(conn, fechar=fechar)


def get_conn():
    """Conexão avulsa (usada por scripts). Feche com conn.close() — no Postgres
    ela vem fora do pool."""
    if BACKEND == "sqlite":
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        return conn
    import psycopg2
    from psycopg2.extras import RealDictCursor
    conn = psycopg2.connect(_DB_URL, cursor_factory=RealDictCursor)
    # O pooler do Supabase descarta o parametro 'options' da URL, entao o
    # search_path da connection string nao chega ao servidor: sem isto o app
    # cai no schema 'public' e nao enxerga os dados. Fixamos na conexao.
    if _SCHEMA:
        with conn.cursor() as cur:
            cur.execute('SET search_path TO "%s", public' % _SCHEMA.replace('"', ""))
        conn.commit()
    return conn


def _abrir():
    return get_conn() if BACKEND == "sqlite" else _pegar_conn()


def _prep(sql):
    return sql if BACKEND == "sqlite" else sql.replace("?", "%s")


def init_db():
    conn = _abrir()
    try:
        cur = conn.cursor()
        if BACKEND == "sqlite":
            cur.executescript(_DDL_SQLITE)
        else:
            cur.execute(_DDL_POSTGRES)
        _migrar_colunas(cur)
        _migrar_cidade_para_regiao(cur)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_prestadores_regiao ON prestadores(regiao_id)")
        conn.commit()
        cur.close()
    except Exception:
        _devolver(conn, erro=True)
        raise
    _devolver(conn)


class _Transacao:
    """Várias gravações que só valem juntas: ou todas entram, ou nenhuma.

        with db.transacao() as t:
            pid = t.execute("INSERT INTO prestadores ...", (...))
            t.execute("INSERT INTO usuarios ...", (..., pid))
    """

    def __init__(self):
        self.conn = None

    def __enter__(self):
        self.conn = _abrir()
        return self

    def __exit__(self, tipo, valor, tb):
        if tipo is None:
            try:
                self.conn.commit()
            except Exception:
                _devolver(self.conn, erro=True)
                raise
            _devolver(self.conn)
        else:
            try:
                self.conn.rollback()
            except Exception:
                pass
            _devolver(self.conn, erro=True)
        return False

    def query(self, sql, params=(), one=False):
        return _query_em(self.conn, sql, params, one)

    def execute(self, sql, params=(), retornar_id=True):
        return _execute_em(self.conn, sql, params, retornar_id)


def transacao():
    return _Transacao()


def _query_em(conn, sql, params=(), one=False):
    cur = conn.cursor()
    cur.execute(_prep(sql), params)
    rows = cur.fetchall()
    cur.close()
    return (rows[0] if rows else None) if one else rows


def _execute_em(conn, sql, params=(), retornar_id=True):
    cur = conn.cursor()
    new_id = None
    is_insert = retornar_id and sql.lstrip()[:6].upper() == "INSERT"
    if BACKEND == "postgres" and is_insert and "RETURNING" not in sql.upper():
        sql = sql.rstrip().rstrip(";") + " RETURNING id"
    cur.execute(_prep(sql), params)
    if BACKEND == "postgres":
        if is_insert:
            row = cur.fetchone()
            new_id = row["id"] if row else None
    elif is_insert:
        new_id = cur.lastrowid
    cur.close()
    return new_id


def query(sql, params=(), one=False):
    conn = _abrir()
    try:
        r = _query_em(conn, sql, params, one)
        if BACKEND == "postgres":
            conn.commit()  # fecha a transação de leitura aberta pelo SET LOCAL
    except Exception:
        _devolver(conn, erro=True)
        raise
    _devolver(conn)
    return r


def execute(sql, params=(), retornar_id=True):
    """retornar_id=False para INSERT em tabela sem coluna id (ex.: uso_diario)."""
    with transacao() as t:
        return t.execute(sql, params, retornar_id)
