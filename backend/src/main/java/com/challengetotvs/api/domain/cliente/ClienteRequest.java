package com.challengetotvs.api.domain.cliente;

import jakarta.validation.constraints.NotBlank;

public record ClienteRequest(
        @NotBlank
        String nome,
        @NotBlank
        String empresa,
        @NotBlank
        String segmento
) {
}
