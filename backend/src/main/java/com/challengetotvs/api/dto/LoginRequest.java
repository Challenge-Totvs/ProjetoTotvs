package com.challengetotvs.api.dto;

import jakarta.validation.constraints.*;


public record LoginRequest(

        @Email
        @NotBlank
        String email,
        @NotBlank
        String senha

) {
}
