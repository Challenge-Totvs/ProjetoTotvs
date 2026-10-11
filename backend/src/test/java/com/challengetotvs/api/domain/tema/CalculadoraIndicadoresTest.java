package com.challengetotvs.api.domain.tema;

import com.challengetotvs.api.domain.tema.CalculadoraIndicadores.Item;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.time.LocalTime;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class CalculadoraIndicadoresTest {

    private static final LocalDate HOJE = LocalDate.of(2026, 10, 10);

    private static CitacaoEntrada c(int diasAtras, Boolean tratado) {
        return new CitacaoEntrada(HOJE.minusDays(diasAtras).atTime(LocalTime.of(10, 0)), (long) diasAtras, 1, tratado);
    }

    private static Item item(boolean risco, boolean oportunidade, boolean naoProcede, CitacaoEntrada... citacoes) {
        var r = CalculadoraSituacao.calcular(List.of(citacoes), oportunidade, null, naoProcede, 30, HOJE);
        return new Item(risco, oportunidade, r);
    }

    @Test
    void semTemasTudoZero() {
        assertThat(CalculadoraIndicadores.calcular(List.of())).isEqualTo(Indicadores.zerados());
    }

    @Test
    void contaCadaSituacaoNoSeuIndicador() {
        var itens = List.of(
                item(true, false, false, c(20, false), c(2, false)),   // risco sem retorno e recorrente
                item(false, true, false, c(42, false)),                // oportunidade perdida
                item(false, true, false, c(5, false)),                 // oportunidade sem retorno
                item(true, false, false, c(9, true)),                  // tratado na conversa
                item(true, false, false, c(56, true)),                 // fora de pauta
                item(true, false, true, c(20, false)));                // não procede

        var i = CalculadoraIndicadores.calcular(itens);

        assertThat(i.emPauta()).isEqualTo(4);
        assertThat(i.riscosSemRetorno()).isEqualTo(1);
        assertThat(i.riscosRecorrentes()).isEqualTo(1);
        assertThat(i.oportPerdidas()).isEqualTo(1);
        assertThat(i.oportSemRetorno()).isEqualTo(1);
        assertThat(i.tratadosConversa()).isEqualTo(1);
        assertThat(i.tratadosFora()).isEqualTo(0);
        assertThat(i.foraDePauta()).isEqualTo(1);
        assertThat(i.naoProcede()).isEqualTo(1);
        assertThat(i.recorrentes()).isEqualTo(1);
        assertThat(i.atencao()).isEqualTo(3);
    }

    @Test
    void temaDuploPerdidoContaComoRiscoSemRetornoEComoOportunidadePerdida() {
        var i = CalculadoraIndicadores.calcular(List.of(item(true, true, false, c(40, false))));

        assertThat(i.riscosSemRetorno()).isEqualTo(1);
        assertThat(i.oportPerdidas()).isEqualTo(1);
    }
}