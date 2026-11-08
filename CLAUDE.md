# Construir & Reformar

Um repositório, duas peças:

| Pasta | O que é | Publica onde |
| --- | --- | --- |
| raiz | Vitrine pública: HTML + JS estático, busca por sinônimos, PWA | GitHub Pages (branch `main`, raiz) |
| repo privado `vzp-engenharia/construir-reformar-sistema` (desde 08/11/2026) | Flask + Postgres: cadastro, login, painel, moderação, `/api/*` do conector MCP | Cloud Run `construir-reformar`, `southamerica-east1`, projeto `central-vzp` — **manual**, da raiz do repo privado (ver `DEPLOY.md` de lá) |

As duas se ligam só pelo `sistemaUrl` do `config.js`. Detalhes no `docs/INTEGRACAO.md` do repo privado.

**Nada do sistema volta para cá.** Este repositório é público: código do servidor,
taxonomia, motor de busca e notas internas ficam só no privado. A licença
(`LICENCA.md`) reserva todos os direitos à VZP Engenharia.

O sistema morava em `vitorzanchetpereira/vzp-construir-reformar-app-web` até
14/10/2026; veio para cá com o histórico inteiro e o antigo foi arquivado; em 08/11/2026
saiu daqui para o repo privado, de novo com o histórico.

**Taxonomia única:** as categorias e os sinônimos da busca moram só em
`categorias-agrupadas.json` do repo privado (7 grupos, 39 categorias). O sistema lê esse
arquivo direto (`taxonomia.py`, `busca_sinonimos.py`); a vitrine usa o `dados.js`,
gerado dele pelo `motor/gen_js.py` de lá. Mudou o JSON? Rode o gerador e suba a
versão do `service-worker.js`. O teste do gerador roda no privado.

## Marca

Símbolo oficial: **Lente de cobogó tecida**. O manual de marca (cores, tipografia,
símbolo, assinatura, texturas, voz) é a referência de toda tela. Os arquivos de
origem estão em `icons/simbolo.svg` (principal) e `icons/favicon.svg` (32 px, para
qualquer uso abaixo de 40 px); os PNGs de `icons/` e `static/icons/` (no privado) são
gerados deles. Vitrine e sistema usam as mesmas cores (`--azul`, `--laranja-txt`,
`--laranja-btn`…) e as mesmas três fontes, servidas pelo próprio site.

## Antes de mexer em qualquer tela

Toda tela daqui — da vitrine e do sistema — segue a skill **`desenvolver-app-vzp`**
(plugin `vzp-engenharia`). Carregue-a antes de criar ou mexer em tela. O que ela
decide não se pergunta: PWA com botão de instalar, botão de voltar em toda tela,
nada de `target="_blank"` nem `window.open`, explicação por mouse/dedo/foco, lista
vazia que ensina, e caber de 320 px até a TV sem rolagem horizontal. As regras
específicas do sistema estão no `CLAUDE.md` do repo privado.
