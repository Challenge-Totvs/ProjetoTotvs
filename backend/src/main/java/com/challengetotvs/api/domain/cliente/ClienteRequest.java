package com.challengetotvs.api.domain.cliente;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

public record ClienteRequest(
        @NotBlank String nome,
        TipoCliente tipo,
        @NotBlank String segmento,
        @NotNull @Valid ContatoRequest contato
) {
        public record ContatoRequest(
                @NotBlank String nome,
                @NotBlank String cargo
        ) {
        }
}