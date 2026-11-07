# Publicar o Construir & Reformar

Roda no **Cloud Run**, região `southamerica-east1` (São Paulo), projeto
`central-vzp`. O banco é **Supabase**, também em São Paulo — app e banco na mesma
região de propósito, ver "Por que São Paulo" no fim.

> **Saímos do Render em 19/08/2026** e os serviços de lá foram apagados. O
> `render.yaml` foi removido deste repositório no mesmo dia: enquanto existisse,
> apontar o Render para cá recriaria o serviço **e um Postgres novo e vazio** —
> foi exatamente assim que o site passou um dia mostrando 12 cadastros de
> demonstração no lugar dos 209 reais. **Nada é publicado no Render.**

## Publicar

Rode **de dentro da pasta `sistema/`** — o `--source .` empacota a pasta atual,
e da raiz ele levaria a vitrine junto e não acharia o `Dockerfile`.

```bash
gcloud run deploy construir-reformar --source . --project central-vzp --region southamerica-east1 --quiet
```

Constrói a imagem a partir da cópia local e troca a revisão. As variáveis de
ambiente do serviço ficam como estão — `gcloud run deploy` não mexe nelas.

Para publicar **e** mudar variáveis no mesmo passo, use `--update-env-vars`
(acrescenta ou troca só as que você citar):

```bash
gcloud run deploy construir-reformar --source . --project central-vzp --region southamerica-east1 --quiet \
  --update-env-vars SEED_DEMO=0,CONTROLADOR_CNPJ=00.000.000/0001-00,CONTATO_PRIVACIDADE=privacidade@exemplo.com.br
```

**Nunca `--set-env-vars`:** ele apaga todas as variáveis que não estiverem na
linha — inclusive `DATABASE_URL` e `DB_SCHEMA` — e o site sobe vazio.

Depois de publicar, confira `/saude` (ver abaixo) e faça um cadastro de teste.

### Voltar para a revisão anterior

As migrações só **acrescentam** (colunas e a tabela `uso_diario`) e as categorias
antigas mantêm nome e slug, então a revisão anterior continua abrindo no mesmo
banco. Para voltar: Cloud Run → `construir-reformar` → Revisões → mandar 100% do
tráfego para a anterior.

## Variáveis de ambiente

Vivem **só** no Cloud Run. Nunca no repositório.

| Variável | Para quê |
| --- | --- |
| `DATABASE_URL` | Postgres do Supabase (pooler de São Paulo) |
| `DB_SCHEMA` | **`construir_reformar`** — leia a armadilha abaixo |
| `SECRET_KEY` | sessão do Flask |
| `ADMIN_EMAIL` / `ADMIN_SENHA` | só criam o primeiro admin num banco vazio. Em produção `ADMIN_SENHA` saiu em 07/11/2026 (os admins já existem); admin novo é conta que a própria pessoa criou e outro admin promoveu em Equipe admin |
| `CLOUDINARY_URL` | upload de fotos; sem ela o site roda, só sem imagem |
| `CR_API_SECRET` | autentica as rotas `/api/*` (é o que o conector MCP usa) |
| `SEED_DEMO` | `0` = produção limpa: remove os dados de demonstração do seed (filtra por nome **e** WhatsApp do seed) |
| `VITRINE_ORIGEM` | endereço da vitrine que pode ler `/api/vitrine/prestadores.json` (CORS) |
| `CONTROLADOR_NOME` / `CONTROLADOR_CNPJ` | quem responde pelos dados (LGPD) — aparece em `/termos` e `/privacidade` |
| `CONTATO_PRIVACIDADE` | e-mail para pedidos de titulares de dados (LGPD art. 18) |
| `DB_POOL_MAX` | opcional — conexões guardadas por instância (padrão `4`). Some as instâncias do Cloud Run × este número e confira que cabe no limite do pooler do Supabase |

Modelo das variáveis comuns em `cloudrun/env.exemplo.yaml`. Sem `ADMIN_SENHA`,
nenhuma conta admin é criada em produção — não existe senha padrão. Sem Postgres
(`DATABASE_URL`) no Cloud Run, o app abre mas mantém o **cadastro fechado**, para
nenhuma ficha se perder no disco descartável do contêiner. Confira em `/saude`:
`"banco": "postgres"` e `"cadastro_aberto": true`.

### A armadilha do schema

Os dados moram no schema `construir_reformar`, não no `public`. **Não adianta
passar o schema na connection string** (`?options=-csearch_path=...`): o pooler
do Supabase descarta o parâmetro `options`, o app cai no `public`, não encontra
tabela nenhuma, cria tudo do zero e o `seed.run()` planta dados de demonstração.

Por isso o `get_conn()` em `db.py` executa `SET search_path` depois de conectar,
lendo a variável `DB_SCHEMA`. **Sem `DB_SCHEMA` definida, o site sobe apontando
para o lugar errado e parece que os cadastros sumiram.**

## O que roda a cada boot

`seed.run()` (chamado pelo `app.py`) faz, sempre, só o que é idempotente:

1. cria tabelas e colunas que faltarem **no schema em uso** (`DB_SCHEMA`) — a
   checagem filtra por `current_schema()`, então uma tabela homônima no `public`
   não engana mais a migração;
2. garante as categorias da taxonomia (`categorias-agrupadas.json`, a mesma da
   vitrine): cria as que faltam e **não renomeia nem duplica** as que já existem —
   reconhece também os nomes com prefixo de grupo ("Instalações • Eletricista").
   Remove ainda as cópias vazias que a versão de 03/11/2026 criou por não
   reconhecer esses prefixos; cópia com cadastro fica e aparece como aviso no
   painel admin, para a equipe mover o prestador e excluir a sobra;
3. garante a região Sorriso/MT e a conta admin (`ADMIN_EMAIL` / `ADMIN_SENHA`).

Dados de demonstração: no Postgres e no Cloud Run o padrão é `SEED_DEMO=0`, que
**remove** os prestadores do seed (mesmo nome **e** mesmo WhatsApp da lista em
`seed.py` — cadastro real nunca bate nos dois) e as duas contas demo. Só no
SQLite local, sem a variável, a demonstração é plantada quando o banco está vazio.

## Por que São Paulo

Até 10/2026 o `db.py` abria uma conexão nova por consulta — cerca de cinco por página. Com o
app em `us-central1` e o banco em São Paulo, cada uma custava um aperto de mão
atravessando o hemisfério: a home levava **6 segundos** com a instância quente.
Na mesma região caiu para **0,5s**.

Desde 11/2026 o `db.py` tem um **pool de conexões** por processo: a conexão é
aberta uma vez e reaproveitada, e o `search_path` vai com `SET LOCAL` em cada
transação (funciona com o pooler do Supabase em modo sessão ou transação). Se o
servidor derrubar as conexões paradas, o pool descarta todas e abre uma nova sem
erro para quem está navegando.
