# Construir & Reformar

Diretorio de prestadores de servico e fornecedores de material da construcao
civil, por tipo de servico e regiao.

**Python (Flask), nao Node** — `app.py`, `db.py`, `requirements.txt`,
`Procfile`. Telas estaticas em `static/` (`manifest.json`, `sw.js` ali tambem).
Publicacao descrita em `DEPLOY.md`.

## Antes de mexer em qualquer tela

Toda tela daqui segue a skill **`desenvolver-app-vzp`** (plugin
`vzp-engenharia`, marketplace do grupo). Carregue-a antes de criar tela nova,
mexer em tela que existe ou consertar layout.

Ela nao e sugestao — **essas decisoes ja estao tomadas e nao se pergunta por
elas**: PWA com botao de instalar, botao de voltar em toda tela, nada de
`target="_blank"` nem `window.open`, explicacao por mouse, dedo e foco, lista
vazia que ensina, e caber de 320 px ate a TV sem rolagem horizontal.

O que se pergunta e o que so o Vitor decide: o que o programa faz, que numero
importa, como o trabalho acontece.

Se alguma dessas regras nao couber neste trabalho, **diga qual e por que** —
nao a pule calado.

A skill fala em Node + Express porque e o molde da casa. **Aqui o servidor e
Python** — as regras de tela valem inteiras; o que muda e onde o HTML e servido
e como o carimbo de versao entra no endereco do arquivo. Faca o equivalente, nao
copie o codigo.

## Contas, admin e historico (Onda 2 da auditoria, 07/11/2026)

Regua do Vitor: ninguem age em nome de outra pessoa.

- **Admin nao cria conta com senha que ele digitou, nao define nem ve senha
  de ninguem (nem de outro admin).** Quem vai ser admin cria a propria conta
  em `/conta/cadastro`, com a propria senha; em `/admin/convidar` (Equipe
  admin) o admin so **promove** essa conta, **tira de admin**, **desativa** ou
  **reativa**. O sistema nao envia e-mail, entao nao ha "pedir redefinicao".
- `usuarios.ativo` (1/0). Conta desativada nao entra e cai na hora: a sessao
  e relida a cada pedido (`usuario_atual`), e o token de 30 dias do conector
  tambem (`api_admin_required` rele a conta e exige `ativo` e papel admin a
  cada chamada — o token nao carrega mais a autorizacao).
- **Historico** (`historico.py`, tabela `historico`, criada pelo `init_db`):
  1. *por requisicao*: todo POST/PUT/PATCH/DELETE vira evento (metodo, rota,
     ids, quem, origem site|conector, status, corpo sem senha/token/CSRF; o
     `X-Agir-Como` do conector fica anotado como *declarado*). Pega rota nova
     sem ninguem lembrar. Transacao propria: falha do historico nao derruba a
     resposta. So `/api/vitrine/evento` (contagem anonima) fica de fora.
  2. *por acao, com antes e depois, na mesma transacao*: promover, tirar de
     admin, desativar, reativar e a exclusao de prestador (que segue fisica,
     mas guarda antes o retrato inteiro: cadastro, fotos, contas, avaliacoes).
  Leitura: `/admin/historico` (tela) e `/api/historico` (conector), so admin.
- A tela/rota de **entrar** e o `/api/login` nao foram mexidos nesta rodada
  (outra frente esta pondo Entrar com Google/Microsoft).
