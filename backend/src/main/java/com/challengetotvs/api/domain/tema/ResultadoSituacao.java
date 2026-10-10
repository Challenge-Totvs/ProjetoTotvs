package com.challengetotvs.api.domain.tema;

import java.time.LocalDate;

public record ResultadoSituacao(
        Situacao situacao,
        boolean emPauta,
        boolean recorrente,
        int reunioesNaJanela,
        boolean atencao,
        Integer venceEm,
        LocalDate perdidaEm,
        LocalDate ultimaAtividade) {
}