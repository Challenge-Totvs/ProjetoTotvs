package com.challengetotvs.api.domain.reuniao;

import jakarta.validation.constraints.Max;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

import java.time.OffsetDateTime;

public record ReuniaoRequest(
        @NotNull Long clienteId,
        @NotBlank String titulo,
        @NotNull OffsetDateTime dataHora,
        @Min(1) @Max(600) Integer duracaoMin,
        Long contatoId,
        @NotNull StatusReuniao status
) {
}