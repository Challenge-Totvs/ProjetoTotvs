package com.challengetotvs.api.domain.compromisso;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.temporal.TemporalAdjusters;

public final class PrazoPorRegra {

    private PrazoPorRegra() {
    }

    public static LocalDate calcular(String regra, LocalDate dataReuniao) {
        if (regra == null || dataReuniao == null) {
            return null;
        }
        return switch (regra) {
            case "sexta" -> dataReuniao.with(TemporalAdjusters.next(DayOfWeek.FRIDAY));
            case "segunda" -> dataReuniao.with(TemporalAdjusters.next(DayOfWeek.MONDAY));
            case "sexta_semana_que_vem" -> dataReuniao.with(TemporalAdjusters.next(DayOfWeek.MONDAY)).plusDays(4);
            case "mesmo_dia" -> dataReuniao;
            case "mais2" -> dataReuniao.plusDays(2);
            default -> null;
        };
    }
}