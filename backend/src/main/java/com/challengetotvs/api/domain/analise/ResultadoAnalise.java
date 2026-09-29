package com.challengetotvs.api.domain.analise;

import java.util.List;

public record ResultadoAnalise (
        List<ItemAnalise> pontosInteresse,
        List<ItemAnalise> pontosDesinteresse,
        List<ItemAnalise> oportunidadesVenda,
        int scoreEngajamento,
        SentimentoGeral sentimentoGeral,
        String recomendacaoProximosPassos,
        MotorUtilizado motorUtilizado
){
}
