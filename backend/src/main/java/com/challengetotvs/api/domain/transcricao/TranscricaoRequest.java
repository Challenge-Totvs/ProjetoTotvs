package com.challengetotvs.api.domain.transcricao;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

public record TranscricaoRequest(
        @NotBlank String conteudo,
        @NotBlank @Pattern(regexp = "COLADO|ARQUIVO", message = "deve ser COLADO ou ARQUIVO") String formatoOrigem,
        String nomeArquivo
) {
}