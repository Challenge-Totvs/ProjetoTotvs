package com.challengetotvs.api.domain.consultor;

import jakarta.validation.constraints.*;


public record LoginRequest(

        @Email
        @NotBlank
        String email,
        @NotBlank
        String senha

) {
}
