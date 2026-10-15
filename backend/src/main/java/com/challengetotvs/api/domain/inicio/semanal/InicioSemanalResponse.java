package com.challengetotvs.api.domain.inicio.semanal;

import java.time.LocalDate;
import java.util.List;

public record InicioSemanalResponse(int janelaDias, List<PontoSemanalResponse> semanas) {

    public record PontoSemanalResponse(
            LocalDate inicioSemana, int realizadas, int analisadas, Double engajamentoMedio) {
    }
}
