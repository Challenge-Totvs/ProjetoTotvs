package com.challengetotvs.api.domain.reuniao;

import jakarta.validation.constraints.Future;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.LocalDateTime;

public record ReuniaoRequest(

        @NotNull
        Long clienteId,
        @NotNull
        @Future
        LocalDateTime dataHora,
        @NotBlank
        String titulo
) {
}
