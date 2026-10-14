package com.challengetotvs.api.domain.evidencia;

import java.time.LocalDateTime;
import java.util.List;

/** Resposta de GET /api/clientes/{id}/evidencias. O aviso vem preenchido quando a lista está vazia por falha ou falta de dados. */
public record EvidenciaResponse(List<Evidencia> evidencias, String aviso) {

    public record Evidencia(String texto, Long reuniaoId, int turno, LocalDateTime data, double score) {
    }

    static EvidenciaResponse vazia(String aviso) {
        return new EvidenciaResponse(List.of(), aviso);
    }
}
