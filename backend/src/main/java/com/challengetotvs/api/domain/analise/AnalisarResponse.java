package com.challengetotvs.api.domain.analise;

import java.util.List;

public record AnalisarResponse(
        Long reuniaoId,
        String motor,
        List<ContratoV3.Tentativa> tentativas,
        int novos,
        int atualizados,
        int compromissos) {
}