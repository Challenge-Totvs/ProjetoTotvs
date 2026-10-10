package com.challengetotvs.api.domain.reuniao;

import java.time.LocalDateTime;

public record ReuniaoResponse(
        Long id,
        Long clienteId,
        String cliente,
        String titulo,
        LocalDateTime dataHora,
        Integer duracaoMin,
        StatusReuniao status,
        boolean confirmada,
        String contato
) {

    public static ReuniaoResponse from(Reuniao reuniao) {
        return new ReuniaoResponse(
                reuniao.getId(),
                reuniao.getCliente().getId(),
                reuniao.getCliente().getNome(),
                reuniao.getTitulo(),
                reuniao.getDataHora(),
                reuniao.getDuracaoMin(),
                reuniao.getStatus(),
                reuniao.foiConfirmada(),
                reuniao.getContato() == null ? null : reuniao.getContato().getNome()
        );
    }
}