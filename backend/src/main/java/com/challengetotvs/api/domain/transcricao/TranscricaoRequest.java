package com.challengetotvs.api.domain.transcricao;

import com.challengetotvs.api.domain.reuniao.Reuniao;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.LocalDateTime;

public record TranscricaoRequest(
        @NotBlank
        String conteudo,
        @NotBlank
        String formatoOrigem
) {
}
