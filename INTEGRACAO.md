# Integração vitrine ↔ sistema (Flask)

A vitrine (este repositório) não tem banco. Quem tem é o sistema
da pasta `sistema/` deste mesmo repositório (Flask + Postgres, no Google Cloud Run), que já faz cadastro,
login, painel do prestador e moderação. As duas peças se ligam por **dois campos** do
`config.js` e nada mais.

## A decisão que falta: qual é a casa e qual é a vitrine

| Caminho | Como fica | A favor | Contra |
|---|---|---|---|
| **A — Vitrine na frente** *(recomendado para lançar)* | Este site é a porta de entrada. O Flask fica com cadastro, login, painel e moderação. | Lança já: só preencher o `config.js` e colar uma rota no Flask. A busca nova e o layout novo vão ao ar sem reescrever templates. | Dois endereços para manter (vitrine e sistema). |
| **B — Tudo no Flask** | O layout e a busca desta vitrine são levados para dentro dos templates do Flask. | Um endereço só. | Reescrever os templates leva dias, e o lançamento espera por isso. |

O caminho A não impede o B depois: a vitrine pode ser absorvida pelo Flask a qualquer momento.

## Caminho A em 2 passos

### 1. Aprovar o PR no Flask
A rota pública de fichas, os Termos, a Privacidade e a limpeza dos dados de demonstração
já estão em `sistema/` (vieram do **PR #3** do antigo repositório
`vitorzanchetpereira/vzp-construir-reformar-app-web`, hoje arquivado),
testados em SQLite e Postgres, já preparados para o Cloud Run. Revisar, fazer o merge e definir as
variáveis do serviço (seção Cloud Run do `DEPLOY.md` do sistema).

### 2. Uma linha no `config.js` da vitrine
```js
sistemaUrl: 'https://SEU-SERVICO.run.app',
```
Com ela, o botão **Cadastrar meu negócio** vai para `<sistema>/cadastro` e as fichas reais
passam a vir de `<sistema>/api/vitrine/prestadores.json`. Suba a versão do
`service-worker.js` ao republicar.

### O que a rota entrega
`GET <sistema>/api/vitrine/prestadores.json` (código em `sistema/app.py`) devolve só o
que já é público na ficha — nome, categoria, região, WhatsApp, descrição, selo, nº de avaliações
aprovadas, média e link da ficha — com CORS liberado apenas para `VITRINE_ORIGEM`. Categorias
criadas no painel admin entram na vitrine se o slug for um dos 36 da taxonomia
(`motor/categorias-agrupadas.json`); as outras são ignoradas sem erro. Se o sistema estiver fora
do ar, a vitrine continua com os exemplos.

## Formato aceito pela vitrine

Uma lista JSON (ou `{ "prestadores": [...] }`). Campos por ficha:

| Campo | Obrigatório | Exemplo |
|---|---|---|
| `slug` | sim — um dos 36 da taxonomia | `"eletricista"` |
| `marca` | sim | `"Elétrica Sorriso"` |
| `resp` | não — entra entre parênteses | `"Luiza"` |
| `cidade` | não | `"Sorriso/MT"` |
| `slogan`, `escopo`, `cnae`, `end` | não — some do card quando vazio | |
| `whats` | não — só números com DDI | `"5566999999999"` |
| `email`, `insta`, `linkedin`, `site` | não | |
| `verif` | não | `true` |
| `voucher` | não — texto da oferta | `"Frete grátis acima de R$ 800"` |
| `n` + `media` | não — total de avaliações aprovadas e média | `12`, `4.7` |
| `notas` | não — as 5 métricas, quando o sistema passar a gravá-las | `[5, 4.8, 5, 4.9, 5]` |
| `indica` | não — % que indicariam | `96` |

## Antes de abrir de verdade (no Flask)
Resolvido no PR #3: dados de demonstração removidos no deploy (`SEED_DEMO=0`), sem senha
padrão de admin, Termos e Privacidade com aceite gravado e app preparado para o Cloud Run.
Falta definir no Cloud Run o Postgres (`DATABASE_URL`), os segredos e `CONTROLADOR_CNPJ` /
`CONTATO_PRIVACIDADE`. O passo a passo completo está em **LANCAMENTO.md**.
