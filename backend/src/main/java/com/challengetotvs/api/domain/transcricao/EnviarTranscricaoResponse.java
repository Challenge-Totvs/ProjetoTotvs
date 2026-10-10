package com.challengetotvs.api.domain.transcricao;

public record EnviarTranscricaoResponse(Long transcricaoId, int caracteres, int turnos, int locutores) {
}