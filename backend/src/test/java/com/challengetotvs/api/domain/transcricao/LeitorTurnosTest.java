package com.challengetotvs.api.domain.transcricao;

import org.junit.jupiter.api.Test;


import static org.assertj.core.api.Assertions.assertThat;

class LeitorTurnosTest {

    @Test
    void numeraTurnosEGuardaOLocutorDoTexto() {
        var turnos = LeitorTurnos.ler("[LOCUTOR 3] Bom dia.\r\n[LOCUTOR 1]: Olá, tudo bem?\n");

        assertThat(turnos).hasSize(2);
        assertThat(turnos.get(0)).isEqualTo(new LeitorTurnos.Turno(1, 3, "Bom dia."));
        assertThat(turnos.get(1)).isEqualTo(new LeitorTurnos.Turno(2, 1, "Olá, tudo bem?"));
    }

    @Test
    void linhasSoltasSaoAnexadasAoTurnoAnterior() {
        var turnos = LeitorTurnos.ler("[LOCUTOR 1] Primeira parte\ncontinua aqui\n\n  e aqui  \n[LOCUTOR 2] Resposta");

        assertThat(turnos).hasSize(2);
        assertThat(turnos.get(0).texto()).isEqualTo("Primeira parte continua aqui e aqui");
    }

    @Test
    void linhasAntesDaPrimeiraMarcacaoSaoDescartadas() {
        var turnos = LeitorTurnos.ler("cabeçalho solto\nreunião x\n[LOCUTOR 1] Oi");

        assertThat(turnos).hasSize(1);
        assertThat(turnos.get(0).texto()).isEqualTo("Oi");
    }

    @Test
    void turnosVaziosSaoRemovidosENumeracaoRecomeca() {
        var turnos = LeitorTurnos.ler("[LOCUTOR 1] \n[LOCUTOR 2] Oi\n[locutor 7]   \n[LOCUTOR 4] Fim");

        assertThat(turnos).extracting(LeitorTurnos.Turno::n).containsExactly(1, 2);
        assertThat(turnos).extracting(LeitorTurnos.Turno::locutor).containsExactly(2, 4);
    }

    @Test
    void textoSemMarcacaoGeraZeroTurnos() {
        assertThat(LeitorTurnos.ler("Sem nenhuma marcação\nsó texto")).isEmpty();
        assertThat(LeitorTurnos.ler("")).isEmpty();
        assertThat(LeitorTurnos.ler(null)).isEmpty();
    }

    @Test
    void aceitaMarcacaoEmMinusculasESemEspaco() {
        var turnos = LeitorTurnos.ler("[Locutor12]texto colado");

        assertThat(turnos).hasSize(1);
        assertThat(turnos.get(0).locutor()).isEqualTo(12);
        assertThat(turnos.get(0).texto()).isEqualTo("texto colado");
    }
}