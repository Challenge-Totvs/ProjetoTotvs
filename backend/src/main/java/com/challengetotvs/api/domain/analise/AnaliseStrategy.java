package com.challengetotvs.api.domain.analise;

public interface AnaliseStrategy {

    ContratoV3.Resposta analisar(ContratoV3.Pedido pedido);
}