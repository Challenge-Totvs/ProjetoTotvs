package com.challengetotvs.api.domain.inicio.semanal;

import com.challengetotvs.api.domain.reuniao.StatusReuniao;

import java.time.DayOfWeek;
import java.time.LocalDate;
import java.time.temporal.TemporalAdjusters;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/**
 * Agrupa reuniões por semana (segunda-feira como início) dentro da janela, sem tocar em
 * {@code InicioService.montar} nem em {@code MontadorTemas}.
 *
 * Engajamento médio = média de {@code Analise.score} (0 a 100) das reuniões ANALISADAs da semana.
 * É o mesmo dado que o contrato v1 chamava de {@code scoreEngajamento} (ver contrato-v3.md §A, tabela
 * de migração) — dado real já calculado pelo motor de análise, nunca um valor de demonstração.
 */
public final class CalculadoraSerieSemanal {

    private CalculadoraSerieSemanal() {
    }

    public record PontoSemanal(LocalDate inicioSemana, int realizadas, int analisadas, Double engajamentoMedio) {
    }

    public static List<PontoSemanal> agrupar(
            List<InicioSemanalRepository.ReuniaoSemanalRow> linhas, LocalDate inicioJanela, LocalDate hoje) {

        Map<LocalDate, int[]> contagens = new LinkedHashMap<>();   // [realizadas, analisadas]
        Map<LocalDate, int[]> somaScore = new LinkedHashMap<>();   // [soma, quantidade]

        for (LocalDate semana = inicioSemanaDe(inicioJanela); !semana.isAfter(inicioSemanaDe(hoje));
                semana = semana.plusWeeks(1)) {
            contagens.put(semana, new int[2]);
            somaScore.put(semana, new int[2]);
        }

        for (var linha : linhas) {
            LocalDate semana = inicioSemanaDe(linha.getDataHora().toLocalDate());
            var c = contagens.computeIfAbsent(semana, k -> new int[2]);
            c[0]++;
            if (linha.getStatus() == StatusReuniao.ANALISADA) {
                c[1]++;
                if (linha.getScore() != null) {
                    var s = somaScore.computeIfAbsent(semana, k -> new int[2]);
                    s[0] += linha.getScore();
                    s[1]++;
                }
            }
        }

        List<PontoSemanal> serie = new ArrayList<>();
        for (var entrada : contagens.entrySet()) {
            LocalDate semana = entrada.getKey();
            int realizadas = entrada.getValue()[0];
            int analisadas = entrada.getValue()[1];
            int[] score = somaScore.getOrDefault(semana, new int[2]);
            Double engajamentoMedio = score[1] == 0 ? null : (double) score[0] / score[1];
            serie.add(new PontoSemanal(semana, realizadas, analisadas, engajamentoMedio));
        }
        serie.sort((a, b) -> a.inicioSemana().compareTo(b.inicioSemana()));
        return serie;
    }

    private static LocalDate inicioSemanaDe(LocalDate data) {
        return data.with(TemporalAdjusters.previousOrSame(DayOfWeek.MONDAY));
    }
}
