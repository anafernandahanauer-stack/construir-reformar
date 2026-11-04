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


def slug_vitrine(slug, nome=""):
    """Slug da taxonomia para uma categoria do banco. Categorias criadas à mão
    no painel (fora da taxonomia) caem na categoria que o motor de busca achar
    pelo nome; sem nenhuma correspondência, devolve None."""
    if slug in ITENS:
        return slug
    if slug in ALIAS:
        return ALIAS[slug]
    if nome:
        import busca_sinonimos
        achados = busca_sinonimos.buscar(nome)
        if achados and achados[0]["slug"] in ITENS:
            return achados[0]["slug"]
    return None


def sincronizar(db):
    """Garante no banco uma categoria para cada item da taxonomia, sem duplicar,
    renomear nem trocar slug do que já existe — assim uma volta para a versão
    anterior do sistema continua funcionando:
      1. já existe com o slug da taxonomia, com o slug antigo (ALIAS) ou com o
         mesmo nome -> fica como está; slug_vitrine() faz a correspondência;
      2. não existe -> é criada com o rótulo e o slug da taxonomia.
    Idempotente: roda a cada boot."""
    existentes = db.query("SELECT id, nome, slug FROM categorias")
    slugs = {c["slug"] for c in existentes}
    nomes = {c["nome"].strip().lower() for c in existentes}
    antigo = {novo: velho for velho, novo in ALIAS.items()}
    criadas = 0
    for slug, item in ITENS.items():
        if slug in slugs or antigo.get(slug) in slugs or item["label"].lower() in nomes:
            continue
        db.execute("INSERT INTO categorias (nome, slug, icone) VALUES (?,?,?)",
                   (item["label"], slug, ICONES.get(slug, "🔧")))
        slugs.add(slug)
        nomes.add(item["label"].lower())
        criadas += 1
    return criadas


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
