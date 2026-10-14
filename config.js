/* Construir & Reformar — configuração da vitrine.
   É o ÚNICO arquivo que precisa ser editado para ligar a vitrine ao sistema.
   Ver INTEGRACAO.md e LANCAMENTO.md.                                        */
window.CONFIG = {
  // SISTEMA — endereço do sistema Flask no Cloud Run, sem barra no fim.
  // Ex.: 'https://construir-reformar-xxxxx.a.run.app'
  // Só com ele preenchido, o botão de cadastro vai para <sistema>/cadastro
  // e as fichas reais vêm de <sistema>/api/vitrine/prestadores.json.
  sistemaUrl: '',

  // Opcionais — só preencha para fugir do padrão acima:
  cadastroUrl: '',       // outro formulário de cadastro
  whatsappCadastro: '',  // ou WhatsApp da equipe (só números, com DDI e DDD)
  emailCadastro: '',     // ou e-mail da equipe
  prestadoresUrl: ''     // outra lista JSON de prestadores
};
(function (C) {
  var s = (C.sistemaUrl || '').replace(/\/+$/, '');
  if (s) {
    if (!C.cadastroUrl) C.cadastroUrl = s + '/cadastro';
    if (!C.prestadoresUrl) C.prestadoresUrl = s + '/api/vitrine/prestadores.json';
  }
})(window.CONFIG);
