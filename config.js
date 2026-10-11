/* Construir & Reformar — configuração da vitrine.
   É o ÚNICO arquivo que precisa ser editado para ligar a vitrine ao sistema.
   Ver INTEGRACAO.md para os detalhes de cada campo.                        */
window.CONFIG = {
  // CADASTRO — preencha UM dos três (o primeiro preenchido vence):
  // 1) Formulário de cadastro, ex.: 'https://construir-reformar.onrender.com/cadastro'
  cadastroUrl: '',
  // 2) WhatsApp da equipe que recebe os cadastros — só números, com DDI e DDD: '5566999999999'
  whatsappCadastro: '',
  // 3) E-mail que recebe os cadastros
  emailCadastro: '',

  // FICHAS REAIS — endereço de uma lista JSON de prestadores (formato em INTEGRACAO.md).
  // Vazio = o site mostra as fichas de exemplo.
  prestadoresUrl: ''
};
