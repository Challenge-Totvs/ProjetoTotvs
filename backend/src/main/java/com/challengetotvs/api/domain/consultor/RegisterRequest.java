package com.challengetotvs.api.domain.consultor;

import jakarta.validation.constraints.*;

public record RegisterRequest(

        @NotBlank
        String nome,
        @Email
        @NotBlank
        String email,
        @NotBlank
        @Size(min = 8)
        String senha

) {
}
