# Roteiro de abertura — Construir & Reformar

Tudo que trava o lançamento já foi resolvido em código. O que sobra são **decisões e campos
que só vocês podem preencher**, nesta ordem. Tempo total: cerca de 30 minutos, mais a leitura jurídica.

| # | Quem | O quê | Onde | Tempo |
|---|---|---|---|---|
| 1 | Vitor | Revisar e fazer o merge do **PR #3** (produção limpa, Termos/Privacidade, rota da vitrine) | GitHub · `vzp-construir-reformar-app-web` | 15 min |
| 2 | Vitor | No Render, preencher `CONTROLADOR_CNPJ` e `CONTATO_PRIVACIDADE`; conferir `SEED_DEMO=0` e `ADMIN_SENHA` forte | Render · web service → Environment | 5 min |
| 3 | Jurídico | Ler `/termos` e `/privacidade` do sistema | Site do sistema | 1 leitura |
| 4 | Duana | Colar o endereço do sistema em `sistemaUrl` no `config.js` e subir `cr-v3` → `cr-v4` no `service-worker.js` | Este repositório | 2 min |
| 5 | Duana | **Liberar** | — | 1 decisão |

## Conferência rápida antes de anunciar (5 minutos, no celular)

- [ ] Abrir a vitrine: as fichas mostram prestadores reais, nenhuma marcada "Ficha de exemplo".
- [ ] Buscar "sem luz" → tocar em Eletricista → aparece a lista da categoria.
- [ ] Tocar em **Cadastrar meu negócio** → abre o cadastro do sistema, com o aceite dos Termos.
- [ ] Fazer um cadastro de teste, conferir que aparece na vitrine em até 5 minutos e apagar pelo painel admin.
- [ ] No sistema, `/privacidade` mostra CNPJ e e-mail de contato.
- [ ] Instalar o app pelo botão **Instalar app** e abrir sem internet.

## Se algo der errado

- **Fichas reais não aparecem:** o servidor gratuito do Render "dorme"; a primeira visita pode
  levar até um minuto e, enquanto isso, a vitrine mostra os exemplos. Persistindo, confira se
  `VITRINE_ORIGEM` no Render é `https://anafernandahanauer-stack.github.io`.
- **Voltar atrás:** apague o valor de `sistemaUrl` no `config.js` — a vitrine volta a mostrar
  só os exemplos e o cadastro fica como "abre em breve".
