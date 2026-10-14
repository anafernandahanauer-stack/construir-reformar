# Publicar o Construir & Reformar no Google Cloud Run

> Produção atual: **Cloud Run** (o serviço do Render ficou inativo em 19/08/2026).
> A seção do Render, mais abaixo, fica só como referência.

O app roda no Cloud Run pelo `Dockerfile`. Três regras de produção:
1. **Banco Postgres é obrigatório** (`DATABASE_URL`). O disco do contêiner é descartável:
   sem Postgres, o app abre, mas **mantém o cadastro fechado** para nenhuma ficha se perder.
   Confira em `/saude` → `"banco": "postgres"` e `"cadastro_aberto": true`.
2. **Segredos no Secret Manager**: `DATABASE_URL`, `SECRET_KEY`, `ADMIN_SENHA`.
3. **Variáveis comuns** em `cloudrun/env.yaml` (modelo em `cloudrun/env.exemplo.yaml`).

## 1. Banco de dados (se ainda não houver um)
Qualquer Postgres serve. No próprio Google (Cloud SQL, tem custo mensal):
```bash
REGIAO=southamerica-east1          # use a região do serviço atual
PROJETO=$(gcloud config get-value project)
gcloud services enable run.googleapis.com sqladmin.googleapis.com secretmanager.googleapis.com
gcloud sql instances create construir-reformar-db --database-version=POSTGRES_16 --region=$REGIAO --tier=db-f1-micro
gcloud sql databases create construir_reformar --instance=construir-reformar-db
gcloud sql users create construir_reformar --instance=construir-reformar-db --password='SENHA_FORTE_DO_BANCO'
```
Alternativa sem servidor próprio: um Postgres gerenciado (Neon, Supabase…) — basta a URL de conexão.

## 2. Segredos
```bash
# Cloud SQL (conexão por socket):
printf 'postgresql://construir_reformar:SENHA_FORTE_DO_BANCO@/construir_reformar?host=/cloudsql/'$PROJETO':'$REGIAO':construir-reformar-db' \
  | gcloud secrets create DATABASE_URL --data-file=-
openssl rand -hex 32 | gcloud secrets create SECRET_KEY --data-file=-
printf 'SENHA_FORTE_DO_ADMIN' | gcloud secrets create ADMIN_SENHA --data-file=-

# a conta de serviço do Cloud Run precisa ler os segredos:
SA=$(gcloud run services describe construir-reformar --region $REGIAO --format='value(spec.template.spec.serviceAccountName)')
for s in DATABASE_URL SECRET_KEY ADMIN_SENHA; do
  gcloud secrets add-iam-policy-binding $s --member="serviceAccount:$SA" --role=roles/secretmanager.secretAccessor
done
```
(Se o comando `SA=` vier vazio, o serviço usa a conta padrão do Compute: `NUMERO-compute@developer.gserviceaccount.com`.)

## 3. Deploy
```bash
cp cloudrun/env.exemplo.yaml cloudrun/env.yaml   # e preencha
gcloud run deploy construir-reformar --source . --region $REGIAO --allow-unauthenticated \
  --add-cloudsql-instances $PROJETO:$REGIAO:construir-reformar-db \
  --env-vars-file cloudrun/env.yaml \
  --set-secrets DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=SECRET_KEY:latest,ADMIN_SENHA=ADMIN_SENHA:latest
```
Se o deploy contínuo pelo GitHub (Cloud Build) já estiver ligado, o merge na `main` refaz a
imagem sozinho — as variáveis e segredos acima só precisam ser definidos uma vez no serviço.

## 4. Conferir
- `https://SEU-SERVICO.run.app/saude` → `{"banco": "postgres", "cadastro_aberto": true, ...}`
- `/termos` e `/privacidade` mostram CNPJ e contato.
- Com `SEED_DEMO=0`, os dados de demonstração somem no primeiro arranque.
- Endereço `https://…run.app` vai no `sistemaUrl` do `config.js` da vitrine.

---

# (Referência) Publicar no Render

O código já está pronto para produção: banco **Postgres** (via `DATABASE_URL`),
servidor **gunicorn**, `SECRET_KEY` e admin por variável de ambiente, e o
`render.yaml` que cria tudo conectado. Siga os passos.

## 1. Criar o repositório no GitHub
Crie um repositório **vazio** (sem README/licença) em <https://github.com/new>.
Sugestão de nome: `construir-reformar` · visibilidade **Private**.

## 2. Enviar o código (rode na pasta do projeto)
```bash
cd C:\Users\vitor\vzp-hub
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/construir-reformar.git
git push -u origin main
```
> Se pedir login, o Git abre o navegador / usa suas credenciais já salvas.

## 3. Criar os serviços no Render (Blueprint)
1. Render → **New +** → **Blueprint**.
2. Conecte a conta GitHub e escolha o repositório `construir-reformar`.
3. O Render lê o `render.yaml` e propõe criar **1 web service + 1 Postgres**.
4. Ele vai pedir os valores marcados como `sync: false`:
   - **ADMIN_EMAIL** — o e-mail de login do admin (o seu).
   - **ADMIN_SENHA** — uma senha forte (essa é a conta que modera avaliações).
   - **CLOUDINARY_URL** — opcional, para fotos de perfil/portfólio e das indicações
     funcionarem. Pegue em [cloudinary.com](https://cloudinary.com) (conta grátis) →
     Settings → API Keys → "API Environment variable". Pode deixar em branco por
     enquanto — o site funciona normal, só sem upload de imagem.
5. Clique em **Apply**. O Render instala, cria o banco, sobe o app e semeia os dados.

## 4. Pronto
- A URL fica tipo `https://construir-reformar.onrender.com`.
- Entre em `/admin` com o ADMIN_EMAIL/ADMIN_SENHA que você definiu.
- O `SECRET_KEY` foi gerado automaticamente pelo Render.

## Observações
- **Plano free do Render**: o web service "dorme" após ~15 min sem acesso (a
  primeira visita depois disso demora alguns segundos). O Postgres free tem
  validade limitada — o Render avisa; dá para migrar para um plano pago quando validar.
- **Atualizar o site depois**: basta `git push` — o Render redeploya sozinho.
  Como agora é Postgres, os dados **não** se perdem entre deploys.

## Antes do lançamento real
- `SEED_DEMO` já vem `0` no `render.yaml`: no próximo deploy, os prestadores, avaliações e contas
  de demonstração criados pelo seed são removidos sozinhos (só eles — o filtro é nome **e** WhatsApp do seed).
- Preencha no painel do Render: `CONTROLADOR_CNPJ` e `CONTATO_PRIVACIDADE` (aparecem em /termos e /privacidade).
- Sem `ADMIN_SENHA`, nenhuma conta admin é criada em produção — não existe senha padrão.
- A vitrine pública (GitHub Pages) lê `/api/vitrine/prestadores.json`; a origem liberada é `VITRINE_ORIGEM`.
