package com.challengetotvs.api.domain.tema;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;

import java.time.LocalDate;

public record TratadoForaRequest(
        @NotBlank String acao,
        String canal,
        LocalDate data,
        @Size(max = 500) String observacao) {
}