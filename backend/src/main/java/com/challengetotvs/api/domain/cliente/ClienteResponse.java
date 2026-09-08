package com.challengetotvs.api.domain.cliente;

import jakarta.validation.constraints.NotNull;

public record ClienteResponse(
        Long id,
        String nome,
        String empresa,
        String segmento
) {
}
