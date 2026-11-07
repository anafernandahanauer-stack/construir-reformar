"""
Histórico: quem fez o quê, com a pessoa REAL. Onda 2 da auditoria de segurança
(07/11/2026). Molde: Harvo (`historico`: tabela, registro_id, operacao, antes,
depois, usuario_id, quando).

Dois jeitos de anotar, de propósito:

1. **Por requisição** (`instalar(app)`): todo POST/PUT/PATCH/DELETE vira um
   evento depois da resposta — método, rota, ids da URL, quem (a conta do
   site ou, nas /api/*, a conta do token relida do banco), origem (site ou
   conector), status e o corpo SEM senha, token nem CSRF. É a rede que pega
   toda gravação, inclusive rota nova que alguém esquecer de anotar. Fica numa
   transação própria: se o histórico falhar, a resposta não falha.
2. **Por ação** (`registrar`): mudanças de conta (promover a admin, rebaixar,
   desativar, reativar) e a exclusão de prestador gravam também o ANTES e o
   DEPOIS, na mesma transação da mudança.

Ninguém altera nem apaga o histórico pela tela ou pela API.
"""
import json
import re
from datetime import date, datetime
from decimal import Decimal

from flask import g, request, session

import db

_SEGREDO = re.compile(r"senha|password|token|secret|segredo|_csrf|hash", re.I)
_SEM_ANOTAR = {"/api/vitrine/evento"}  # contagem anônima de uso da vitrine: volume, não autoria
_MAX_TEXTO = 500


def _padrao(v):
    if isinstance(v, (datetime, date)):
        return v.isoformat()
    if isinstance(v, Decimal):
        return float(v)
    return str(v)


def limpar(v):
    """Copia sem nenhum campo de senha/segredo e corta texto comprido."""
    if v is None:
        return None
    if isinstance(v, dict) or hasattr(v, "keys"):
        return {k: limpar(v[k]) for k in v.keys() if not _SEGREDO.search(str(k))}
    if isinstance(v, (list, tuple)):
        return [limpar(x) for x in v]
    if isinstance(v, str) and len(v) > _MAX_TEXTO:
        return v[:_MAX_TEXTO] + "…"
    return v


def _json(v):
    return None if v is None else json.dumps(limpar(v), default=_padrao, ensure_ascii=False)


def registrar(t, *, tabela, operacao, registro_id=None, antes=None, depois=None,
              usuario=None, origem="site", rota=None, status=None, nota=None):
    """Grava um evento. `t` é um db.transacao() aberto (mesma transação da
    mudança) ou None (transação própria). `usuario` é a linha da conta."""
    sql = ("INSERT INTO historico (tabela, registro_id, operacao, antes, depois, usuario_id, usuario, "
           "origem, rota, status, nota, quando) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)")
    params = (
        tabela, None if registro_id is None else str(registro_id), operacao,
        _json(antes), _json(depois),
        usuario["id"] if usuario else None,
        (f"{usuario['nome'] or ''} <{usuario['email']}>".strip() if usuario else "visitante (sem conta)"),
        origem, rota, status, nota,
        datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
    )
    if t is not None:
        t.execute(sql, params)
    else:
        db.execute(sql, params)


def listar(*, tabela=None, registro_id=None, limite=200):
    limite = max(1, min(int(limite or 200), 1000))
    filtros, params = [], []
    if tabela:
        filtros.append("tabela = ?")
        params.append(tabela)
    if registro_id:
        filtros.append("registro_id = ?")
        params.append(str(registro_id))
    onde = ("WHERE " + " AND ".join(filtros)) if filtros else ""
    linhas = db.query(f"SELECT * FROM historico {onde} ORDER BY id DESC LIMIT ?", (*params, limite))
    r = []
    for l in linhas:
        e = dict(l)
        for k in ("antes", "depois"):
            try:
                e[k] = json.loads(e[k]) if e[k] else None
            except (TypeError, ValueError):
                pass
        r.append(e)
    return r


def _tabela_da_rota(path):
    partes = [p for p in path.split("/") if p and not p.isdigit()]
    if partes and partes[0] in ("api", "admin"):
        partes = partes[1:]
    return partes[0] if partes else "site"


def instalar(app, usuario_atual):
    """Liga o registro por requisição. `usuario_atual()` devolve a conta do site."""

    @app.after_request
    def _anotar_escrita(resposta):
        try:
            if request.method in ("GET", "HEAD", "OPTIONS") or request.path in _SEM_ANOTAR:
                return resposta
            api = request.path.startswith("/api/")
            usuario = getattr(g, "api_conta", None) if api else None
            if not api:
                usuario = usuario_atual() if session.get("usuario_id") else None
            corpo = request.get_json(silent=True) if request.is_json else request.form.to_dict()
            if request.files:
                corpo = dict(corpo or {}, _arquivos=[f.filename for f in request.files.values()])
            depois = {"corpo": corpo, "ids": request.view_args or {}}
            agir_como = request.headers.get("X-Agir-Como")
            if agir_como:
                # Declarado pelo conector; NÃO é prova de identidade (quem
                # responde é a conta do token). Fica anotado para conferir.
                depois["agir_como_declarado"] = agir_como[:200]
            ids = request.view_args or {}
            registrar(
                None,
                tabela=_tabela_da_rota(request.path),
                registro_id=next(iter(ids.values()), None),
                operacao=request.method,
                depois=depois,
                usuario=usuario,
                origem="conector" if api else "site",
                rota=f"{request.method} {request.path}",
                status=resposta.status_code,
            )
        except Exception as e:  # o histórico nunca derruba a resposta
            app.logger.error("historico: não anotei %s %s: %s", request.method, request.path, e)
        return resposta
