package com.challengetotvs.api.domain.tema;

import org.junit.jupiter.api.Test;

import java.time.LocalDate;

import static org.assertj.core.api.Assertions.assertThat;

class RegrasAcaoTemaTest {

    private static final LocalDate HOJE = LocalDate.of(2026, 10, 10);

    @Test
    void acaoDeOportunidadeSoValeParaTemaDeOportunidade() {
        assertThat(RegrasAcaoTema.acaoValida("proposta", false, true)).isEqualTo(true);
        assertThat(RegrasAcaoTema.acaoValida("proposta", true, false)).isEqualTo(false);
    }

    @Test
    void acaoDeRiscoSoValeParaTemaDeRisco() {
        assertThat(RegrasAcaoTema.acaoValida("suporte", true, false)).isEqualTo(true);
        assertThat(RegrasAcaoTema.acaoValida("suporte", false, true)).isEqualTo(false);
    }

    @Test
    void temaDuploAceitaAsDuasListas() {
        assertThat(RegrasAcaoTema.acaoValida("proposta", true, true)).isEqualTo(true);
        assertThat(RegrasAcaoTema.acaoValida("condicao", true, true)).isEqualTo(true);
    }

    @Test
    void acaoInventadaOuNulaNaoVale() {
        assertThat(RegrasAcaoTema.acaoValida("qualquer", true, true)).isEqualTo(false);
        assertThat(RegrasAcaoTema.acaoValida(null, true, true)).isEqualTo(false);
    }

    @Test
    void canalPrecisaSerDaLista() {
        assertThat(RegrasAcaoTema.canalValido("whatsapp")).isEqualTo(true);
        assertThat(RegrasAcaoTema.canalValido("pombo")).isEqualTo(false);
        assertThat(RegrasAcaoTema.canalValido(null)).isEqualTo(false);
    }

    @Test
    void motivoEOpcionalMasSeVierPrecisaSerDaLista() {
        assertThat(RegrasAcaoTema.motivoValido(null)).isEqualTo(true);
        assertThat(RegrasAcaoTema.motivoValido("  ")).isEqualTo(true);
        assertThat(RegrasAcaoTema.motivoValido("fora_contexto")).isEqualTo(true);
        assertThat(RegrasAcaoTema.motivoValido("porque sim")).isEqualTo(false);
    }

    @Test
    void dataDeHojeNaoEFuturaMasAmanhaE() {
        assertThat(RegrasAcaoTema.dataFutura(HOJE, HOJE)).isEqualTo(false);
        assertThat(RegrasAcaoTema.dataFutura(HOJE.plusDays(1), HOJE)).isEqualTo(true);
    }

    @Test
    void registroNoMesmoDiaDaCitacaoValeMasAnteriorNao() {
        assertThat(RegrasAcaoTema.anteriorAUltimaCitacao(HOJE, HOJE)).isEqualTo(false);
        assertThat(RegrasAcaoTema.anteriorAUltimaCitacao(HOJE.minusDays(1), HOJE)).isEqualTo(true);
    }
}