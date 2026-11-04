"""
Taxonomia única do Construir & Reformar: as mesmas categorias no cadastro do
sistema e na vitrine (dados.js é gerado deste mesmo JSON por motor/gen_js.py).

Fonte: categorias-agrupadas.json (grupos na ordem da obra, cada item com slug,
rótulo e sinônimos de busca).
"""
import json
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
_DADOS = json.loads((_AQUI / "categorias-agrupadas.json").read_text(encoding="utf-8"))

GRUPOS = [
    {"n": g["n"], "titulo": g["titulo"],
     "itens": [{"slug": i["slug"], "label": i["label"]} for i in g["itens"]]}
    for g in _DADOS["grupos"]
]
ITENS = {i["slug"]: {**i, "grupo": g["titulo"], "grupo_n": g["n"]} for g in GRUPOS for i in g["itens"]}
ORDEM = {slug: n for n, slug in enumerate(ITENS)}

# Slugs que o sistema usou antes da taxonomia (seed antigo) -> slug da taxonomia.
ALIAS = {
    "locacao": "locacao-equipamentos",
    "gesso": "gesso-drywall",
    "engenharia": "projeto-engenharia",
    "materiais": "materiais-construcao",
    "limpeza": "limpeza-pos-obra",
}

ICONES = {
    "topografia": "📏", "analise-de-solo": "🧪", "terraplenagem": "🚜", "pedreiro": "🧱",
    "gesso-drywall": "🧰", "serralheiro": "🔩", "impermeabilizacao": "💧", "mestre-de-obra": "👷",
    "eletricista": "⚡", "encanador": "🚿", "sistema-de-gas": "🔥", "sistema-de-ar": "❄️",
    "energia-solar": "☀️", "automacao": "🤖", "ti-internet-redes": "📶", "pintor": "🎨",
    "azulejista": "🔲", "marmoraria": "🪨", "marceneiro": "🪚", "vidracaria": "🪟",
    "projeto-engenharia": "📐", "gerenciamento-obra": "📋", "construtoras": "🏗️",
    "locacao-equipamentos": "🏗️", "manutencao-equipamentos": "🛠️", "operador-de-maquinas": "🚧",
    "frete": "🚚", "chapa-carga-descarga": "📦", "limpeza-pos-obra": "🧹",
    "jardinagem-paisagismo": "🌿", "manutencao-piscinas": "🏊", "gas-revenda": "🛢️",
    "materiais-construcao": "🏬", "tornearia": "⚙️", "seguranca-do-trabalho": "🦺",
    "seguranca-eletronica": "📹", "treinamentos": "🎓", "mineradoras": "⛰️",
    "estagio-jovem-aprendiz": "🧑‍🎓",
}


def _nucleo(nome):
    """'Instalações • Eletricista' -> 'Eletricista': o prefixo de grupo que a
    equipe usa nos nomes não ajuda a reconhecer a categoria."""
    return (nome or "").split("•")[-1].strip()


def slug_vitrine(slug, nome=""):
    """Slug da taxonomia para uma categoria do banco. Categorias com slug antigo
    ou criadas à mão no painel (inclusive com prefixo de grupo no nome) caem na
    categoria que o motor de busca achar pelo nome; sem correspondência, None."""
    if slug in ITENS:
        return slug
    if slug in ALIAS:
        return ALIAS[slug]
    if nome:
        import busca_sinonimos
        achados = busca_sinonimos.buscar(_nucleo(nome))
        if achados and achados[0]["slug"] in ITENS:
            return achados[0]["slug"]
    return None


def sincronizar(db):
    """Garante no banco uma categoria para cada item da taxonomia, sem duplicar,
    renomear nem trocar slug do que já existe — assim uma volta para a versão
    anterior do sistema continua funcionando. Um item conta como existente se
    alguma categoria do banco já corresponde a ele, pelo slug, pelo slug antigo
    (ALIAS) ou pelo nome (com ou sem prefixo de grupo, ex. 'Instalações • Eletricista').
    Idempotente: roda a cada boot."""
    existentes = db.query("SELECT id, nome, slug FROM categorias")
    cobertos = {slug_vitrine(c["slug"], c["nome"]) for c in existentes}
    nomes = {c["nome"].strip().lower() for c in existentes}
    criadas = 0
    for slug, item in ITENS.items():
        if slug in cobertos or item["label"].lower() in nomes:
            continue
        db.execute("INSERT INTO categorias (nome, slug, icone) VALUES (?,?,?)",
                   (item["label"], slug, ICONES.get(slug, "🔧")))
        cobertos.add(slug)
        nomes.add(item["label"].lower())
        criadas += 1
    return criadas


def limpar_copias(db):
    """Desfaz as cópias que a versão de 03/11/2026 criou por não reconhecer os
    nomes com prefixo de grupo. Só apaga a categoria que tem, ao mesmo tempo:
      • o slug e o rótulo exatos da taxonomia (a assinatura do que o seed criou);
      • nenhum prestador;
      • outra categoria no banco que corresponde ao mesmo item.
    Se a cópia já tiver prestador, fica e entra na lista de avisos."""
    cats = db.query(
        "SELECT c.id, c.nome, c.slug, (SELECT COUNT(*) FROM prestadores p WHERE p.categoria_id = c.id) AS n "
        "FROM categorias c")
    mapa = {c["id"]: slug_vitrine(c["slug"], c["nome"]) for c in cats}
    apagadas, com_prestador = [], []
    for c in cats:
        item = ITENS.get(c["slug"])
        if not item or c["nome"] != item["label"]:
            continue
        gemeas = [d for d in cats if d["id"] != c["id"] and mapa[d["id"]] == c["slug"]]
        if not gemeas:
            continue
        if int(c["n"] or 0):
            com_prestador.append(f'{c["nome"]} ({int(c["n"])} prestador(es); mover para "{gemeas[0]["nome"]}")')
            continue
        db.execute("DELETE FROM categorias WHERE id = ?", (c["id"],))
        apagadas.append(c["nome"])
    return apagadas, com_prestador


def repetidas(categorias):
    """Grupos de categorias do banco que correspondem ao mesmo item da
    taxonomia — para o painel admin avisar e a equipe juntar."""
    por_item = {}
    for c in categorias:
        slug = slug_vitrine(c["slug"], c["nome"])
        if slug:
            por_item.setdefault(slug, []).append(c["nome"])
    return [sorted(nomes) for nomes in por_item.values() if len(nomes) > 1]


def agrupar(categorias):
    """Organiza as categorias do banco nos grupos da taxonomia, na ordem da obra,
    para o <select> do cadastro. O que estiver fora da taxonomia vai para 'Outras'."""
    por_grupo = {g["n"]: [] for g in GRUPOS}
    outras = []
    for c in categorias:
        item = ITENS.get(slug_vitrine(c["slug"], c["nome"]) or "")
        if item:
            por_grupo[item["grupo_n"]].append((ORDEM[item["slug"]], c["nome"], c))
        else:
            outras.append(c)
    saida = []
    for g in GRUPOS:
        itens = [c for _o, _n, c in sorted(por_grupo[g["n"]], key=lambda t: (t[0], t[1]))]
        if itens:
            saida.append({"titulo": f'{g["n"]}. {g["titulo"]}', "categorias": itens})
    if outras:
        saida.append({"titulo": "Outras", "categorias": sorted(outras, key=lambda c: c["nome"])})
    return saida
