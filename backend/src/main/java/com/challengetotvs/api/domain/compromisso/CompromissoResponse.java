package com.challengetotvs.api.domain.compromisso;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.Comparator;

public record CompromissoResponse(
        Long id,
        Long clienteId,
        String clienteNome,
        Long reuniaoId,
        int turno,
        String texto,
        LocalDate prazo,
        String estado,
        Integer atraso,
        boolean cumprido,
        LocalDate cumpridoEm) {

    public static CompromissoResponse de(Compromisso c, LocalDate hoje) {
        Integer atraso = c.getPrazo() == null ? null : (int) ChronoUnit.DAYS.between(c.getPrazo(), hoje);
        String estado;
        if (c.cumprido()) {
            estado = "cumprido";
        } else if (atraso == null) {
            estado = "sem_prazo";
        } else if (atraso > 0) {
            estado = "vencido";
        } else if (atraso == 0) {
            estado = "hoje";
        } else {
            estado = "no_prazo";
        }
        return new CompromissoResponse(
                c.getId(), c.getCliente().getId(), c.getCliente().getNome(),
                c.getReuniao().getId(), c.getTurno(), c.getTexto(),
                c.getPrazo(), estado, atraso, c.cumprido(),
                c.getCumpridoEm() == null ? null : c.getCumpridoEm().toLocalDate());
    }

    private static int peso(String estado) {
        return switch (estado) {
            case "vencido" -> 0;
            case "hoje" -> 1;
            case "no_prazo" -> 2;
            case "sem_prazo" -> 3;
            default -> 4; // cumprido
        };
    }

    public static final Comparator<CompromissoResponse> ORDEM = Comparator
            .comparingInt((CompromissoResponse c) -> peso(c.estado()))
            .thenComparing(CompromissoResponse::prazo, Comparator.nullsLast(Comparator.naturalOrder()))
            .thenComparing(CompromissoResponse::id);
}