package com.challengetotvs.api.domain.tema;

import com.challengetotvs.api.domain.tema.ExplicadorTema.Entrada;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class ExplicadorTemaTest {

    private static final LocalDate HOJE = LocalDate.of(2026, 10, 10);
    private static final int JANELA = 30;

    private static CitacaoEntrada c(int diasAtras, Boolean tratado) {
        return new CitacaoEntrada(HOJE.minusDays(diasAtras).atTime(LocalTime.of(10, 0)), (long) diasAtras, 1, tratado);
    }

    // Monta a entrada a partir da própria CalculadoraSituacao, como o serviço faz de verdade
    private static Entrada entrada(List<CitacaoEntrada> citacoes, boolean risco, boolean oportunidade,
                                   Integer foraHa, boolean naoProcede) {
        LocalDate dataFora = foraHa == null ? null : HOJE.minusDays(foraHa);
        var r = CalculadoraSituacao.calcular(citacoes, oportunidade, dataFora, naoProcede, JANELA, HOJE);
        int diasUltima = citacoes.stream().mapToInt(x -> (int) (HOJE.toEpochDay() - x.dataHora().toLocalDate().toEpochDay()))
                .min().getAsInt();
        return new Entrada(r, risco, oportunidade, JANELA, HOJE, "Acompanhamento trimestral",
                HOJE.minusDays(diasUltima),
                "Kelwin Bastos", "proposta", "email", dataFora,
                "Bruno Melo", "fora_contexto", HOJE.minusDays(19));
    }

    @Test
    void riscoSemRetornoRecorrenteUsaAFraseDoHandoff() {
        var e = entrada(List.of(c(20, false), c(2, false)), true, false, null, false);

        assertThat(ExplicadorTema.explicar(e)).isEqualTo(
                "Na última reunião em que apareceu, há 2 dias, em \"Acompanhamento trimestral\" (08/10), "
                        + "ficou sem resposta. Citado em 2 reuniões nos últimos 30 dias.");
    }

    @Test
    void oportunidadeSemRetornoAvisaQuandoVaiPerder() {
        var e = entrada(List.of(c(9, false)), false, true, null, false);

        assertThat(ExplicadorTema.explicar(e)).isEqualTo(
                "Citada há 9 dias, em \"Acompanhamento trimestral\" (01/10), e ainda sem tratamento. "
                        + "Vira oportunidade perdida em 22 dias se não for tratada.");
    }

    @Test
    void oportunidadePerdidaDizHaQuantoTempoPassouDaJanela() {
        var e = entrada(List.of(c(37, false)), false, true, null, false);

        assertThat(ExplicadorTema.explicar(e)).isEqualTo(
                "Citada há 37 dias, em \"Acompanhamento trimestral\" (03/09), sem tratamento na reunião nem nas seguintes. "
                        + "Passou da janela de 30 dias há 6 dias.");
    }

    @Test
    void temaDuploPerdidoLembraDoRiscoSemResposta() {
        var e = entrada(List.of(c(40, false)), true, true, null, false);

        assertThat(ExplicadorTema.explicar(e)).endsWith(" O risco ligado a ela também segue sem resposta.");
    }

    @Test
    void tratadoNaConversa() {
        var e = entrada(List.of(c(9, true)), true, false, null, false);

        assertThat(ExplicadorTema.explicar(e)).isEqualTo(
                "Respondido na própria reunião, há 9 dias, em \"Acompanhamento trimestral\" (01/10).");
    }

    @Test
    void semLeituraExplicaOLimiteDoMotor() {
        var e = entrada(List.of(c(5, null)), true, false, null, false);

        assertThat(ExplicadorTema.explicar(e)).startsWith("O motor que analisou a reunião não identifica quem falou");
    }

    @Test
    void tratadoForaMostraQuemFezOQueEPorOndeEQuando() {
        var e = entrada(List.of(c(10, false)), false, true, 3, false);

        assertThat(ExplicadorTema.explicar(e)).isEqualTo("Kelwin Bastos registrou: proposta enviada, por e-mail, em 07/10.");
    }

    @Test
    void foraDePautaExplicaOHistorico() {
        var e = entrada(List.of(c(56, true)), true, false, null, false);

        assertThat(ExplicadorTema.explicar(e)).isEqualTo(
                "Não aparece há 56 dias, mais que a janela de 30. Sai do resumo e fica no histórico; "
                        + "se voltar, recomeça como tema novo ligado a este.");
    }

    @Test
    void naoProcedeMostraQuemMarcouEOMotivo() {
        var e = entrada(List.of(c(20, false)), true, false, null, true);

        assertThat(ExplicadorTema.explicar(e)).isEqualTo(
                "Marcado como não procede por Bruno Melo há 19 dias. Motivo: fora de contexto. "
                        + "Vira contraexemplo para as próximas análises.");
    }

    @Test
    void citacaoDeHojeDizHoje() {
        var e = entrada(List.of(c(0, false)), true, false, null, false);

        assertThat(ExplicadorTema.explicar(e)).startsWith("Na última reunião em que apareceu, hoje, em ");
    }
}