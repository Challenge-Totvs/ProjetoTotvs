package com.challengetotvs.api.domain.inicio.semanal;

import com.challengetotvs.api.domain.reuniao.StatusReuniao;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class CalculadoraSerieSemanalTest {

    private static final LocalDate HOJE = LocalDate.of(2026, 10, 15);   // quinta-feira

    private record Linha(LocalDateTime dataHora, StatusReuniao status, Integer score)
            implements InicioSemanalRepository.ReuniaoSemanalRow {
        @Override public LocalDateTime getDataHora() { return dataHora; }
        @Override public StatusReuniao getStatus() { return status; }
        @Override public Integer getScore() { return score; }
    }

    @Test
    void semReunioesGeraSemanasZeradasNaJanela() {
        var serie = CalculadoraSerieSemanal.agrupar(List.of(), HOJE.minusDays(14), HOJE);

        assertThat(serie).hasSize(3);                                  // semanas de 01/10, 08/10 e 13/10
        assertThat(serie).allSatisfy(p -> {
            assertThat(p.realizadas()).isZero();
            assertThat(p.analisadas()).isZero();
            assertThat(p.engajamentoMedio()).isNull();
        });
    }

    @Test
    void contaRealizadasEAnalisadasPorSemanaESoMediaScoreDasAnalisadas() {
        List<InicioSemanalRepository.ReuniaoSemanalRow> linhas = List.of(
                new Linha(LocalDateTime.of(2026, 10, 6, 10, 0), StatusReuniao.ANALISADA, 80),
                new Linha(LocalDateTime.of(2026, 10, 7, 10, 0), StatusReuniao.ANALISADA, 60),
                new Linha(LocalDateTime.of(2026, 10, 8, 10, 0), StatusReuniao.REALIZADA, null),
                new Linha(LocalDateTime.of(2026, 10, 14, 10, 0), StatusReuniao.ANALISADA, null));   // sem score ainda

        var serie = CalculadoraSerieSemanal.agrupar(linhas, HOJE.minusDays(14), HOJE);

        var semana06 = serie.stream().filter(p -> p.inicioSemana().equals(LocalDate.of(2026, 10, 5))).findFirst().orElseThrow();
        assertThat(semana06.realizadas()).isEqualTo(3);
        assertThat(semana06.analisadas()).isEqualTo(2);
        assertThat(semana06.engajamentoMedio()).isEqualTo(70.0);

        var semana13 = serie.stream().filter(p -> p.inicioSemana().equals(LocalDate.of(2026, 10, 12))).findFirst().orElseThrow();
        assertThat(semana13.realizadas()).isEqualTo(1);
        assertThat(semana13.analisadas()).isEqualTo(1);
        assertThat(semana13.engajamentoMedio()).isNull();               // analisada sem score computado ainda
    }

    @Test
    void janelaMenorQueUmaSemanaDevolveAoMenosASemanaAtual() {
        var serie = CalculadoraSerieSemanal.agrupar(List.of(), HOJE, HOJE);

        assertThat(serie).hasSize(1);
        assertThat(serie.get(0).inicioSemana()).isEqualTo(LocalDate.of(2026, 10, 12));
    }
}
