/* Transcrição de exemplo (Hospital Santa Luzia), com dados fictícios.
   Preenche o formulário de Nova transcrição pelo botão "Usar transcrição de exemplo". */

const AMOSTRA_LINHAS: [number, string][] = [
  [1, "Bom dia, doutor Paulo. Bom dia, Sandra. Obrigado pelo horário."],
  [2, "Bom dia, Kelwin. Vamos direto ao ponto, que a agenda hoje está apertada."],
  [1, "Claro. O contrato vence em dois meses e eu queria alinhar a renovação com vocês."],
  [2, "A gente quer renovar, mas precisa de uma condição melhor para os próximos dois anos."],
  [1, "Posso montar a proposta com reajuste fixo nos dois anos e incluir as licenças da ala nova sem custo de implantação."],
  [2, "Isso ajuda bastante."],
  [3, "Antes de fechar a renovação, preciso registrar uma coisa. O suporte continua demorando para responder os chamados de faturamento."],
  [3, "Tem chamado aberto há duas semanas sem nenhuma resposta, e o fechamento do mês depende disso."],
  [1, "Entendo. Sobre a ala nova, vocês já têm a data de inauguração?"],
  [2, "Fevereiro, se a obra não atrasar."],
  [2, "E a diretoria quer oferecer telemedicina para os pacientes da ala nova. Vocês têm alguma coisa nessa linha?"],
  [1, "Sobre a proposta, o que eu pensei é o seguinte. Reajuste fixo pelos dois anos, para vocês terem previsibilidade no orçamento. As licenças da ala nova entram já no contrato, com implantação sem custo, e a ativação acontece junto com a inauguração. O treinamento das equipes novas fica incluído, no mesmo formato que fizemos na ala principal. E o contrato passa a ter revisão semestral de uso, para ajustar licenças sem precisar esperar a renovação seguinte. Com isso o valor total fica abaixo do que vocês pagariam renovando no modelo atual e contratando a ala nova à parte."],
  [2, "Faz sentido. Mas preciso ser transparente: recebemos uma proposta de outra empresa, com valor menor."],
  [1, "Obrigado pela transparência. O que mais pesou na proposta deles, além do valor?"],
  [2, "Basicamente o valor. Em funcionalidade vocês estão na frente."],
  [1, "Então vou trabalhar a condição comercial. Te envio a proposta de renovação até segunda, com os valores fechados para os dois anos."],
  [2, "Perfeito."],
  [2, "Acho que é isso. Manda a proposta que eu levo para a reunião da diretoria."],
  [1, "Mando sim. Obrigado, doutor Paulo. Obrigado, Sandra."],
  [3, "Obrigada."],
];

export const AMOSTRA_TEXTO = AMOSTRA_LINHAS.map(([l, t]) => `[LOCUTOR ${l}]: ${t}`).join("\n");

/** Cliente, reunião e contato que a amostra usa, para pré-selecionar quando existirem. */
export const AMOSTRA_CLIENTE = "Hospital Santa Luzia";
export const AMOSTRA_REUNIAO = { titulo: "Alinhamento da renovação", hora: "15:00", contato: "Paulo Freitas", duracao: "14" };
