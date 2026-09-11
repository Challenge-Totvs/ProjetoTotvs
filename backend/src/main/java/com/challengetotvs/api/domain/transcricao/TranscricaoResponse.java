package com.challengetotvs.api.domain.transcricao;

import java.time.LocalDateTime;

public record TranscricaoResponse(
        Long id,
        Long reuniaoId,
        String conteudo,
        String formatoOrigem,
        LocalDateTime criadoEm
) {

    public static TranscricaoResponse from (Transcricao transcricao){
        return new TranscricaoResponse(
                transcricao.getId(),
                transcricao.getReuniao().getId(),
                transcricao.getConteudo(),
                transcricao.getFormatoOrigem(),
                transcricao.getCriadoEm()
        );
    }
}
