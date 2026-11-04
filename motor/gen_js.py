# -*- coding: utf-8 -*-
"""Gera o topo do dados.js (taxonomia + palavras ignoradas) a partir da fonte
única: sistema/categorias-agrupadas.json e sistema/busca_sinonimos.py.

A vitrine e o sistema usam a mesma taxonomia. Mudou uma categoria ou um
sinônimo? Edite só o JSON do sistema e rode:

    python3 motor/gen_js.py          # regrava dados.js
    python3 motor/gen_js.py --check  # falha se dados.js estiver desatualizado

Só as linhas de dados (DADOS, CATS, STOP) são regravadas; a lógica de busca em
JavaScript, abaixo delas, fica como está.
"""
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "sistema"))
import busca_sinonimos  # noqa: E402

FONTE = RAIZ / "sistema" / "categorias-agrupadas.json"
ALVO = RAIZ / "dados.js"


def gerar():
    d = json.loads(FONTE.read_text(encoding="utf-8"))
    grupos, cats = [], {}
    for g in d["grupos"]:
        grupos.append({"n": g["n"], "titulo": g["titulo"],
                       "itens": [{"label": i["label"], "novo": bool(i.get("novo"))} for i in g["itens"]]})
        for i in g["itens"]:
            b = i.get("busca", {})
            cats[i["slug"]] = {"label": i["label"], "grupo": g["titulo"], "grupo_n": g["n"],
                               "forte": b.get("forte", []), "fraco": b.get("fraco", []),
                               "tags": i.get("tags", [])}
    j = lambda o: json.dumps(o, ensure_ascii=False)
    topo = [
        "// gerado por motor/gen_js.py a partir de sistema/categorias-agrupadas.json — nao editar a mao",
        "// espelha a logica de busca_sinonimos.py para a previa no browser",
        "const DADOS = " + j({"grupos": grupos}) + ";",
        "const CATS = " + j(cats) + ";",
        "const STOP = new Set(" + j(sorted(busca_sinonimos._STOP)) + ");",
    ]
    resto = ALVO.read_text(encoding="utf-8").split("\n")[5:]
    termos = [t for c in cats.values() for t in c["forte"] + c["fraco"]]
    return "\n".join(topo + resto), {"grupos": len(grupos), "categorias": len(cats), "termos": len(termos)}


if __name__ == "__main__":
    novo, n = gerar()
    if "--check" in sys.argv:
        if ALVO.read_text(encoding="utf-8") != novo:
            sys.exit("dados.js desatualizado: rode python3 motor/gen_js.py")
        print("dados.js em dia", n)
    else:
        ALVO.write_text(novo, encoding="utf-8")
        print("dados.js regravado", n)
