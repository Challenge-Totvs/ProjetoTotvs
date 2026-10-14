package com.challengetotvs.api.domain.reuniao;

import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.time.OffsetDateTime;

import static org.assertj.core.api.Assertions.assertThat;

class ReuniaoServiceHoraTest {

    @Test
    void horaComFusoDeBrasiliaFicaComoVeio() {
        var enviada = OffsetDateTime.parse("2026-10-13T20:00:00-03:00");

        assertThat(ReuniaoService.horaLocal(enviada)).isEqualTo(LocalDateTime.of(2026, 10, 13, 20, 0));
    }

    @Test
    void noiteDeBrasiliaEmUtcNaoViraDiaSeguinte() {
        // o Jackson normaliza para UTC: 22:30 de 13/10 em Brasília chega como 01:30Z de 14/10
        var emUtc = OffsetDateTime.parse("2026-10-14T01:30:00Z");

        assertThat(ReuniaoService.horaLocal(emUtc)).isEqualTo(LocalDateTime.of(2026, 10, 13, 22, 30));
    }
}
