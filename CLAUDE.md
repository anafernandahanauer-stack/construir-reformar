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

**Cuidado:** `motor/` (vitrine) e `sistema/` têm cada um seu
`categorias-agrupadas.json` e `busca_sinonimos.py`, e hoje **divergem**. A
taxonomia da vitrine é a fonte nova (36 categorias); unificar é trabalho
pendente, não presuma que mudar um muda o outro.

## Antes de mexer em qualquer tela

Toda tela daqui — da vitrine e do sistema — segue a skill **`desenvolver-app-vzp`**
(plugin `vzp-engenharia`). Carregue-a antes de criar ou mexer em tela. O que ela
decide não se pergunta: PWA com botão de instalar, botão de voltar em toda tela,
nada de `target="_blank"` nem `window.open`, explicação por mouse/dedo/foco, lista
vazia que ensina, e caber de 320 px até a TV sem rolagem horizontal. As regras
específicas do sistema estão em `sistema/CLAUDE.md`.
