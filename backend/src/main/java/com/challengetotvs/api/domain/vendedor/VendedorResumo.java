package com.challengetotvs.api.domain.vendedor;

import com.challengetotvs.api.domain.inicio.InicioResponse;

public record VendedorResumo(
        Long id,
        String nome,
        String email,
        InicioResponse.Desempenho metricas) {
}