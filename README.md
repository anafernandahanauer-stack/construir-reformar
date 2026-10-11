# Construir & Reformar

*Escreva do seu jeito. Encontre quem faz.*

Diretório de obra de Mato Grosso: a pessoa descreve o problema como fala — “sem luz”, “cano estourado”, “não gela”, até escrito errado — e o site leva à categoria certa entre **6 grupos e 36 categorias**, organizadas na ordem da obra. Site estático, também instalável como aplicativo (PWA) em celular, tablet ou computador.

Uma iniciativa VZP Engenharia / Base Empreendimentos.

**Importante antes de começar:** esta é a **vitrine pública**. A busca por linguagem do dia a dia funciona de verdade (1.054 termos informais, 132 de 132 casos de teste passando), mas não há banco de dados aqui: as fichas de prestador exibidas são **exemplos fictícios** de como o cadastro vai aparecer. As fichas reais e as avaliações vêm do sistema com servidor (ver “Próximos passos”).

## O que tem em cada arquivo

```
construir-reformar/
├── index.html          → o site inteiro (HTML + CSS + JavaScript em um único arquivo)
├── dados.js            → taxonomia e motor de busca por sinônimos (gerado a partir de motor/)
├── config.js           → ÚNICO arquivo a editar: para onde vai o botão "Cadastrar meu negócio"
├── manifest.json       → ficha de identidade do app para o sistema poder "instalá-lo"
├── service-worker.js   → permite abrir o app já instalado mesmo sem internet
├── icons/              → ícone do app em todos os tamanhos + imagem de compartilhamento (og-image)
├── motor/              → fonte da verdade da busca: categorias-agrupadas.json, busca_sinonimos.py,
│                         nomes_cards.py (padrão "Marca (Responsável)") e teste_busca.py
├── package.json        → atalhos para rodar localmente e testar a busca (não é obrigatório)
├── robots.txt / .nojekyll
└── .gitignore
```

Não há dependências para instalar, não há passo de build. `index.html` funciona sozinho.

## Como abrir localmente

**Rápido, só para olhar:** dê duplo clique em `index.html`. A única limitação é que o navegador não permite “instalar como aplicativo” quando o arquivo é aberto direto do disco.

**Recomendado, para testar como app de verdade:**

```bash
# Com Node.js:
npm start

# Sem Node, com Python:
python3 -m http.server 5173
```

Depois abra `http://localhost:5173`.

**Testar o motor de busca:** `python3 motor/teste_busca.py` (ou `npm test`).

## Ligar o cadastro

Abra `config.js` e preencha **um** dos três campos — o primeiro preenchido vence:

| Campo | Exemplo | Quando usar |
|---|---|---|
| `cadastroUrl` | `https://construir-reformar.onrender.com/cadastro` | Formulário do sistema com servidor |
| `whatsappCadastro` | `5566999999999` | A equipe recebe o pedido no WhatsApp |
| `emailCadastro` | `cadastro@seudominio.com.br` | A equipe recebe por e-mail |

Com os três vazios, o botão aparece desativado com a nota “Os cadastros abrem em breve”.

## Como instalar como aplicativo (PWA)

- **Chrome ou Edge no computador:** botão **Instalar app** no topo do site (ou o ícone na barra de endereço).
- **Android (Chrome):** botão **Instalar app**, ou menu ⋮ → “Instalar aplicativo”.
- **iPhone/iPad (Safari):** compartilhar → “Adicionar à Tela de Início”.

## Como publicar como site de verdade

É 100% estático, então qualquer um destes serve:

- **GitHub Pages:** Settings → Pages → *Deploy from a branch* → `main` / `(root)`. O endereço fica `https://SEU_USUARIO.github.io/construir-reformar/`.
- **Netlify:** arraste a pasta para [app.netlify.com/drop](https://app.netlify.com/drop).
- **Vercel:** `npx vercel` dentro da pasta.

Todos dão HTTPS, que é pré-requisito do navegador para instalar o app.

**Ao republicar:** suba a versão em `service-worker.js` (`cr-v1` → `cr-v2`). Isso invalida o cache de quem já instalou.

## Próximos passos para virar produto completo

Em ordem de prioridade:

1. **Ligar o cadastro** — preencher `config.js` (5 minutos). Sem isso, o site funciona, mas não capta prestador.
2. **Fichas reais no lugar dos exemplos** — a lista `PREST` em `index.html` passa a vir do sistema com servidor (`vzp-construir-reformar-app-web`, Flask + Postgres), que já tem cadastro, login, painel do prestador e moderação.
3. **Avaliação em 5 métricas** — Atendimento, Qualidade e quantidade, Inspeção e segurança, Resolveu a demanda, Indicaria. O layout está pronto; a gravação e a moderação são do servidor.
4. **Domínio próprio** — e, com ele, o endereço absoluto da imagem de compartilhamento (`og:image`) para o link ficar bonito no WhatsApp.
5. **Termos de uso e política de privacidade (LGPD)** — obrigatórios antes de publicar dados de pessoas reais.
