package com.challengetotvs.api.domain.motor;

import com.challengetotvs.api.domain.motor.StatusMotores.MotorRecebido;
import org.junit.jupiter.api.Test;

import java.time.OffsetDateTime;
import java.util.Arrays;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class StatusMotoresTest {

    private static final OffsetDateTime QUANDO = OffsetDateTime.parse("2026-10-10T22:00:00-03:00");

    private static List<String> nomes(List<MotorStatus> lista) {
        return lista.stream().map(MotorStatus::motor).toList();
    }

    @Test
    void semDetalheNaoInventaStatus() {
        assertThat(StatusMotores.normalizar(null, QUANDO).isEmpty()).isEqualTo(true);
        assertThat(StatusMotores.normalizar(List.of(), QUANDO).isEmpty()).isEqualTo(true);
    }

    @Test
    void devolveOsQuatroMotoresNaOrdemFixaMesmoSeChegaremEmOutraOrdem() {
        var lista = StatusMotores.normalizar(List.of(
                new MotorRecebido("regras", true), new MotorRecebido("llm1", false),
                new MotorRecebido("local", true), new MotorRecebido("llm2", true)), QUANDO);

        assertThat(nomes(lista)).isEqualTo(List.of("llm1", "llm2", "local", "regras"));
        assertThat(lista.get(0).ok()).isEqualTo(false);
        assertThat(lista.get(1).ok()).isEqualTo(true);
    }

    @Test
    void motorQueNaoVeioNoHealthContaComoForaDoAr() {
        var lista = StatusMotores.normalizar(List.of(new MotorRecebido("llm1", true)), QUANDO);

        assertThat(lista.size()).isEqualTo(4);
        assertThat(lista.get(0).ok()).isEqualTo(true);
        assertThat(lista.get(1).ok()).isEqualTo(false);
    }

    @Test
    void okNuloContaComoFora() {
        var lista = StatusMotores.normalizar(List.of(new MotorRecebido("llm1", null)), QUANDO);

        assertThat(lista.get(0).ok()).isEqualTo(false);
    }

    @Test
    void motorDesconhecidoVaiParaOFimEItemNuloEIgnorado() {
        var lista = StatusMotores.normalizar(Arrays.asList(
                new MotorRecebido("llm1", true), null, new MotorRecebido("novo", true)), QUANDO);

        assertThat(nomes(lista)).isEqualTo(List.of("llm1", "llm2", "local", "regras", "novo"));
    }

    @Test
    void foraDoArMarcaOsQuatroComoFora() {
        var lista = StatusMotores.foraDoAr(QUANDO);

        assertThat(nomes(lista)).isEqualTo(List.of("llm1", "llm2", "local", "regras"));
        assertThat(lista.stream().anyMatch(MotorStatus::ok)).isEqualTo(false);
        assertThat(lista.get(0).verificadoEm()).isEqualTo(QUANDO);
    }
}