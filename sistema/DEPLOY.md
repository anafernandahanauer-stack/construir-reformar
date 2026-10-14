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

```bash
gcloud run deploy construir-reformar --source . --project central-vzp --region southamerica-east1 --quiet
```

Constrói a imagem a partir da cópia local e troca a revisão. As variáveis de
ambiente do serviço ficam como estão — `gcloud run deploy` não mexe nelas.

## Variáveis de ambiente

Vivem **só** no Cloud Run. Nunca no repositório.

| Variável | Para quê |
| --- | --- |
| `DATABASE_URL` | Postgres do Supabase (pooler de São Paulo) |
| `DB_SCHEMA` | **`construir_reformar`** — leia a armadilha abaixo |
| `SECRET_KEY` | sessão do Flask |
| `ADMIN_EMAIL` / `ADMIN_SENHA` | conta que modera avaliações |
| `CLOUDINARY_URL` | upload de fotos; sem ela o site roda, só sem imagem |
| `CR_API_SECRET` | autentica as rotas `/api/*` (é o que o conector MCP usa) |

| `SEED_DEMO` | `0` = produção limpa: remove os dados de demonstração do seed (filtra por nome **e** WhatsApp do seed) |
| `VITRINE_ORIGEM` | endereço da vitrine que pode ler `/api/vitrine/prestadores.json` (CORS) |
| `CONTROLADOR_NOME` / `CONTROLADOR_CNPJ` | quem responde pelos dados (LGPD) — aparece em `/termos` e `/privacidade` |
| `CONTATO_PRIVACIDADE` | e-mail para pedidos de titulares de dados (LGPD art. 18) |

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

## Semeadura

`seed.run()` roda em todo boot, mas só planta a demonstração se **não houver
nenhum prestador**. Com o schema certo, ele não faz nada. `SEED_DEMO=0` desliga
de vez, se preferir cinto e suspensório.

## Por que São Paulo

O `db.py` abre uma conexão nova por consulta — cerca de cinco por página. Com o
app em `us-central1` e o banco em São Paulo, cada uma custava um aperto de mão
atravessando o hemisfério: a home levava **6 segundos** com a instância quente.
Na mesma região caiu para **0,5s**.

Um pool de conexões derrubaria mais um pedaço e é a correção estrutural — a
mudança de região só tornou o problema barato. Se um dia o site crescer, é por
aí que se mexe.
