package com.challengetotvs.api.domain.tema;

import com.challengetotvs.api.domain.tema.TemaResponse.RegistroFora;
import org.junit.jupiter.api.Test;

import java.util.List;

import static com.challengetotvs.api.domain.tema.TemaFixture.*;
import static org.assertj.core.api.Assertions.assertThat;

class CalculadoraDesempenhoTest {

    @Test
    void semTemasTudoZeroENuloNaTaxa() {
        var r = CalculadoraDesempenho.calcular(List.of(), 30, HOJE);

        assertThat(r.temasCitados()).isEqualTo(0);
        assertThat(r.taxaConversa()).isEqualTo(null);
        assertThat(r.oportIdentificadas()).isEqualTo(0);
    }

    @Test
    void taxaDeConversaConsideraSoOsCitadosNaJanelaComLeitura() {
        var temas = List.of(
                simples(1, "risco", Situacao.TRATADO_CONVERSA, cit(5, true)),    // respondido
                simples(2, "risco", Situacao.SEM_RETORNO, cit(8, false)),        // sem resposta
                simples(3, "risco", Situacao.SEM_LEITURA, cit(3, null)),         // sem leitura: fora da conta
                simples(4, "risco", Situacao.TRATADO_CONVERSA, cit(40, true)));  // fora da janela

        var r = CalculadoraDesempenho.calcular(temas, 30, HOJE);

        assertThat(r.temasCitados()).isEqualTo(3);
        assertThat(r.taxaConversa()).isEqualTo(0.5);                             // 1 de 2 com leitura
    }

    @Test
    void oportunidadesTratadasContamRespondidaEOTratadoFora() {
        var fora = new RegistroFora("proposta", "email", HOJE.minusDays(1), null, "Kelwin");
        var temas = List.of(
                simples(1, "oportunidade", Situacao.TRATADO_CONVERSA, cit(5, true)),
                tema(2, List.of("oportunidade"), Situacao.TRATADO_FORA, false, null, null, fora, cit(6, false)),
                simples(3, "oportunidade", Situacao.SEM_RETORNO, cit(4, false)),
                simples(4, "risco", Situacao.TRATADO_CONVERSA, cit(4, true)));   // risco não entra em oportunidades

        var r = CalculadoraDesempenho.calcular(temas, 30, HOJE);

        assertThat(r.oportIdentificadas()).isEqualTo(3);
        assertThat(r.oportTratadas()).isEqualTo(2);
        assertThat(r.tratadosFora()).isEqualTo(1);
    }

    @Test
    void naoProcedeFicaDeFora() {
        var temas = List.of(simples(1, "risco", Situacao.NAO_PROCEDE, cit(3, false)));

        var r = CalculadoraDesempenho.calcular(temas, 30, HOJE);

        assertThat(r.temasCitados()).isEqualTo(0);
        assertThat(r.riscosSemRetorno()).isEqualTo(0);
    }

    @Test
    void riscosSemRetornoEOportunidadesPerdidasSaoDaSituacaoAtualSemRecorteDeJanela() {
        var temas = List.of(
                simples(1, "risco", Situacao.SEM_RETORNO, cit(60, false)),      // antigo, mas segue sem retorno
                simples(2, "oportunidade", Situacao.OPORTUNIDADE_PERDIDA, cit(45, false)),
                tema(3, List.of("risco", "oportunidade"), Situacao.OPORTUNIDADE_PERDIDA, false, null, HOJE.minusDays(3), null, cit(34, false)));

        var r = CalculadoraDesempenho.calcular(temas, 30, HOJE);

        assertThat(r.riscosSemRetorno()).isEqualTo(2);     // o 1 e o duplo perdido (risco em situação perdida)
        assertThat(r.oportPerdidas()).isEqualTo(2);
    }
}