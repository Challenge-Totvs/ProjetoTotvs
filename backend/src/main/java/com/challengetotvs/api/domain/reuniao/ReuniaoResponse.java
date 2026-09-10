package com.challengetotvs.api.domain.reuniao;

import com.challengetotvs.api.domain.cliente.Cliente;
import com.challengetotvs.api.domain.cliente.ClienteResponse;
import com.challengetotvs.api.domain.consultor.Consultor;

import java.time.LocalDateTime;

public record ReuniaoResponse(
        Long id,
        String cliente,
        LocalDateTime dataHora,
        String titulo,
        StatusReuniao status
) {

    public static ReuniaoResponse from (Reuniao reuniao){
        return new ReuniaoResponse(
                reuniao.getId(),
                reuniao.getCliente().getNome(),
                reuniao.getDataHora(),
                reuniao.getTitulo(),
                reuniao.getStatus()
        );

    }
}
