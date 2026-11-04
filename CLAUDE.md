# Construir & Reformar

Um repositório, duas peças:

| Pasta | O que é | Publica onde |
| --- | --- | --- |
| raiz | Vitrine pública: HTML + JS estático, busca por sinônimos, PWA | GitHub Pages (branch `main`, raiz) |
| `sistema/` | Flask + Postgres: cadastro, login, painel, moderação, `/api/*` do conector MCP | Cloud Run `construir-reformar`, `southamerica-east1`, projeto `central-vzp` — **manual**, de dentro de `sistema/` (ver `sistema/DEPLOY.md`) |

As duas se ligam só pelo `sistemaUrl` do `config.js`. Detalhes em `INTEGRACAO.md`.

O sistema morava em `vitorzanchetpereira/vzp-construir-reformar-app-web` até
14/10/2026; veio para cá com o histórico inteiro (`git log -- sistema/`), e o
antigo foi arquivado.

**Taxonomia única:** as categorias e os sinônimos da busca moram só em
`sistema/categorias-agrupadas.json` (7 grupos, 39 categorias). O sistema lê esse
arquivo direto (`taxonomia.py`, `busca_sinonimos.py`); a vitrine usa o `dados.js`,
gerado dele por `python3 motor/gen_js.py`. Mudou o JSON? Rode o gerador e suba a
versão do `service-worker.js`. `npm test` falha se o `dados.js` ficar para trás.

## Antes de mexer em qualquer tela

Toda tela daqui — da vitrine e do sistema — segue a skill **`desenvolver-app-vzp`**
(plugin `vzp-engenharia`). Carregue-a antes de criar ou mexer em tela. O que ela
decide não se pergunta: PWA com botão de instalar, botão de voltar em toda tela,
nada de `target="_blank"` nem `window.open`, explicação por mouse/dedo/foco, lista
vazia que ensina, e caber de 320 px até a TV sem rolagem horizontal. As regras
específicas do sistema estão em `sistema/CLAUDE.md`.
