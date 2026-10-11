package com.challengetotvs.api.domain.transcricao;

import com.challengetotvs.api.domain.transcricao.LeitorTurnos.Turno;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class MetricasConversaTest {

    private static final Map<Integer, String> PAPEIS = Map.of(1, "vendedor", 2, "cliente", 3, "cliente");

    private static Turno t(int n, int locutor, String texto) {
        return new Turno(n, locutor, texto);
    }

    @Test
    void listaVaziaNaoQuebra() {
        var m = MetricasConversa.calcular(List.of(), PAPEIS, 30);

        assertThat(m.totalPalavras()).isEqualTo(0);
        assertThat(m.maiorMonologo()).isEqualTo(null);
        assertThat(m.falaVendedor()).isEqualTo(null);
        assertThat(m.trocasPorMinuto()).isEqualTo(null);
    }

    @Test
    void contaPalavrasPorLocutorEFalaDoVendedor() {
        var m = MetricasConversa.calcular(List.of(
                t(1, 1, "um dois três"),
                t(2, 2, "quatro cinco")), PAPEIS, null);

        assertThat(m.totalPalavras()).isEqualTo(5);
        assertThat(m.falaVendedor()).isEqualTo(0.6);
        assertThat(m.falaPorLocutor().size()).isEqualTo(2);
        assertThat(m.falaPorLocutor().get(0).palavras()).isEqualTo(3);
        assertThat(m.falaPorLocutor().get(0).papel()).isEqualTo("vendedor");
    }

    @Test
    void locutorForaDoMapaContaComoCliente() {
        var m = MetricasConversa.calcular(List.of(
                t(1, 1, "oi tudo bem"),
                t(2, 9, "tudo certo")), Map.of(1, "vendedor"), null);

        assertThat(m.falaPorLocutor().get(1).locutor()).isEqualTo(9);
        assertThat(m.falaPorLocutor().get(1).papel()).isEqualTo("cliente");
    }

    @Test
    void turnosSeguidosDoMesmoPapelViramUmBloco() {
        var m = MetricasConversa.calcular(List.of(
                t(1, 1, "pergunta curta"),
                t(2, 2, "resposta de um locutor"),
                t(3, 3, "continuação de outro locutor do cliente"),
                t(4, 1, "ok")), PAPEIS, null);

        assertThat(m.maiorFalaCliente().palavras()).isEqualTo(4 + 6);   // turno 2 + turno 3, mesmo papel
        assertThat(m.maiorFalaCliente().turno()).isEqualTo(2);          // o bloco começa no turno 2
        assertThat(m.maiorMonologo().papel()).isEqualTo("cliente");
    }

    @Test
    void semPapeisUsaOLocutorENaoTemFalaDoVendedor() {
        var m = MetricasConversa.calcular(List.of(
                t(1, 1, "a b c"),
                t(2, 2, "d e")), Map.of(), 30);

        assertThat(m.comPapeis()).isEqualTo(false);
        assertThat(m.falaVendedor()).isEqualTo(null);
        assertThat(m.maiorFalaCliente()).isEqualTo(null);
        assertThat(m.maiorMonologo().locutor()).isEqualTo(1);
        assertThat(m.maiorMonologo().papel()).isEqualTo(null);
    }

    @Test
    void trocasPorMinutoSoComDuracao() {
        var turnos = List.of(t(1, 1, "a"), t(2, 2, "b"), t(3, 1, "c"), t(4, 2, "d"));

        assertThat(MetricasConversa.calcular(turnos, PAPEIS, 40).trocasPorMinuto()).isEqualTo(3.0 / 40);
        assertThat(MetricasConversa.calcular(turnos, PAPEIS, null).trocasPorMinuto()).isEqualTo(null);
    }

    @Test
    void contaPerguntasPorPapel() {
        var m = MetricasConversa.calcular(List.of(
                t(1, 1, "Como vai?"),
                t(2, 2, "Bem."),
                t(3, 1, "E o suporte? Ajudou?"),
                t(4, 2, "Não sei?")), PAPEIS, null);

        assertThat(m.perguntas().get("vendedor")).isEqualTo(2);   // 2 turnos com "?", não 3 pontos de interrogação
        assertThat(m.perguntas().get("cliente")).isEqualTo(1);
    }
}