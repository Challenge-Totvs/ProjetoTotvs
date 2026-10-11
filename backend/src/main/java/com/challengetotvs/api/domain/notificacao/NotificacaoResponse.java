package com.challengetotvs.api.domain.notificacao;

import java.time.LocalDateTime;
import java.util.List;

public record NotificacaoResponse(long naoLidas, List<Item> itens) {

    public record VendedorRef(Long id, String nome) {
    }

    public record ClienteRef(Long id, String nome) {
    }

    public record TemaRef(Long id, String titulo, List<String> tipos, Boolean ultimaTratado) {
    }

    public record Item(
            Long id,
            VendedorRef de,
            ClienteRef cliente,
            TemaRef tema,
            String mensagem,
            LocalDateTime criadoEm,
            boolean lida
    ) {
    }
}