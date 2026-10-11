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
├── config.js           → ÚNICO arquivo a editar: canal de cadastro e lista de fichas reais
├── INTEGRACAO.md       → como a vitrine se liga ao sistema Flask
├── LANCAMENTO.md       → roteiro de abertura: quem faz o quê, em que ordem
├── privacidade.html    → o que a vitrine coleta (nada) e o que fica no aparelho
├── 404.html            → página de endereço inexistente, com volta ao início
├── fonts/              → Outfit, Plus Jakarta Sans e Space Grotesk servidas pelo próprio site (licença OFL)
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

Abra `config.js` e preencha `sistemaUrl` com o endereço do sistema no Render: o cadastro e as fichas reais se ligam juntos. Para usar outro canal de cadastro, preencha **um** destes — o primeiro preenchido vence:

| Campo | Exemplo | Quando usar |
|---|---|---|
| `cadastroUrl` | `https://construir-reformar.onrender.com/cadastro` | Formulário do sistema com servidor |
| `whatsappCadastro` | `5566999999999` | A equipe recebe o pedido no WhatsApp |
| `emailCadastro` | `cadastro@seudominio.com.br` | A equipe recebe por e-mail |

Com os três vazios, o botão aparece desativado com a nota “Os cadastros abrem em breve”.

## Ligar as fichas reais

`prestadoresUrl` no `config.js` aponta para uma lista JSON de prestadores. Com ela, as
fichas de exemplo somem e entram as reais; se o servidor não responder, o site segue com
os exemplos. O formato e uma rota pronta para o Flask estão em **INTEGRACAO.md** — testada
contra o sistema real: 12 de 12 prestadores carregados, busca “luz” abrindo Elétrica Sorriso.

## Como a busca leva até o prestador

Digite → a categoria certa aparece → toque nela e a lista de prestadores já vem filtrada.
Categoria sem ninguém mostra o convite para se cadastrar ou indicar alguém pelo WhatsApp.
Cada categoria tem endereço próprio para compartilhar: `…/#cat=eletricista`.

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

**Ao republicar:** suba a versão em `service-worker.js` (hoje `cr-v3` → `cr-v4`). Isso invalida o cache de quem já instalou.

## Privacidade

A vitrine não usa cookies, não envia a busca para servidor nenhum e não carrega nada de
terceiros: fontes, ícones e scripts vêm do próprio endereço. Detalhes em `privacidade.html`.

## Próximos passos para virar produto completo

Em ordem de prioridade:

1. **Abrir** — seguir o **LANCAMENTO.md**: merge do PR #3 no sistema, dois campos no Render, uma linha (`sistemaUrl`) no `config.js` e a liberação.
3. **Avaliação em 5 métricas** — Atendimento, Qualidade e quantidade, Inspeção e segurança, Resolveu a demanda, Indicaria. O layout está pronto; a gravação e a moderação são do servidor.
4. **Domínio próprio** — e, com ele, o endereço absoluto da imagem de compartilhamento (`og:image`) para o link ficar bonito no WhatsApp.
5. **Termos de uso e política de privacidade (LGPD)** — obrigatórios antes de publicar dados de pessoas reais.
