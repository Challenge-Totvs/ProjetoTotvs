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
        String contato,
        /** Nome do vendedor dono do cliente; null quando não carregado (listagem do próprio vendedor não precisa dele). */
        String vendedorNome
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
                reuniao.getContato() == null ? null : reuniao.getContato().getNome(),
                null
        );
    }

    /** Para a listagem da gestão, com o vendedor dono do cliente já carregado. */
    public static ReuniaoResponse comVendedor(Reuniao reuniao) {
        return new ReuniaoResponse(
                reuniao.getId(),
                reuniao.getCliente().getId(),
                reuniao.getCliente().getNome(),
                reuniao.getTitulo(),
                reuniao.getDataHora(),
                reuniao.getDuracaoMin(),
                reuniao.getStatus(),
                reuniao.foiConfirmada(),
                reuniao.getContato() == null ? null : reuniao.getContato().getNome(),
                reuniao.getCliente().getVendedor().getNome()
        );
    }
}