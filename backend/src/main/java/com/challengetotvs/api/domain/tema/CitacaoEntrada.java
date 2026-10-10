package com.challengetotvs.api.domain.tema;

import java.time.LocalDateTime;

public record CitacaoEntrada(
        LocalDateTime dataHora,
        Long reuniaoId,
        int turno,
        Boolean tratado) {
}