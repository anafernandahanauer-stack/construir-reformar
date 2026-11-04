"""
Medição de uso, anônima e agregada: quantas buscas, quais termos não acharam
nada e quantas pessoas chamaram cada prestador no WhatsApp.

Guarda só contadores por dia (dia, tipo, chave, n) — nada de IP, cookie,
navegador ou quem clicou. Termos que pareçam dado pessoal (telefone, e-mail)
são descartados antes de gravar.
"""
import re
import unicodedata
from datetime import datetime, timedelta, timezone

import db

# Cuiabá não tem horário de verão desde 2019: UTC-4 fixo, sem depender de tzdata.
_FUSO = timezone(timedelta(hours=-4))
TIPOS = {"busca", "busca_vazia", "whatsapp", "ficha"}


def _hoje():
    return datetime.now(_FUSO).date().isoformat()


def limpar_termo(termo):
    termo = unicodedata.normalize("NFKD", termo or "")
    termo = "".join(c for c in termo if not unicodedata.combining(c)).lower()
    termo = re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", termo)).strip()[:60]
    if not termo or "@" in (termo or "") or re.search(r"\d{4,}", termo):
        return ""
    return termo


def contar(tipo, chave=""):
    """Soma 1 no contador do dia. Nunca quebra a página: medição é acessório."""
    if tipo not in TIPOS:
        return
    try:
        db.execute(
            "INSERT INTO uso_diario (dia, tipo, chave, n) VALUES (?,?,?,1) "
            "ON CONFLICT (dia, tipo, chave) DO UPDATE SET n = uso_diario.n + 1",
            (_hoje(), tipo, str(chave)[:60]), retornar_id=False,
        )
    except Exception as e:  # pragma: no cover
        print("AVISO: medição de uso não gravou:", e)


def _desde(dias):
    return (datetime.now(_FUSO).date() - timedelta(days=dias - 1)).isoformat()


def resumo(dias=30):
    desde = _desde(dias)
    tot = {r["tipo"]: int(r["n"]) for r in db.query(
        "SELECT tipo, SUM(n) AS n FROM uso_diario WHERE dia >= ? GROUP BY tipo", (desde,))}
    vazias = db.query(
        "SELECT chave, SUM(n) AS n FROM uso_diario WHERE dia >= ? AND tipo = 'busca_vazia' "
        "GROUP BY chave ORDER BY SUM(n) DESC, chave LIMIT 30", (desde,))
    cliques = db.query(
        "SELECT p.id, p.nome, SUM(u.n) AS n FROM uso_diario u JOIN prestadores p "
        "ON CAST(p.id AS TEXT) = u.chave WHERE u.dia >= ? AND u.tipo = 'whatsapp' "
        "GROUP BY p.id, p.nome ORDER BY SUM(u.n) DESC, p.nome LIMIT 30", (desde,))
    return {"dias": dias, "totais": tot, "vazias": vazias, "cliques": cliques}


def cliques_prestador(pid, dias=30):
    r = db.query("SELECT COALESCE(SUM(n),0) AS n FROM uso_diario WHERE dia >= ? AND tipo = 'whatsapp' AND chave = ?",
                 (_desde(dias), str(pid)), one=True)
    return int(r["n"] or 0)
