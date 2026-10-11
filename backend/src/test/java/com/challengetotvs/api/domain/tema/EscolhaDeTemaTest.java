package com.challengetotvs.api.domain.tema;

import com.challengetotvs.api.domain.tema.EscolhaDeTema.Candidato;
import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class EscolhaDeTemaTest {

    private static final LocalDate HOJE = LocalDate.of(2026, 10, 10);   // data fixa: o teste não depende do dia em que roda
    private static final int JANELA = 30;

    // Citação feita "diasAtras" dias antes de HOJE; tratado: true = respondido, false = sem resposta
    private static CitacaoEntrada c(int diasAtras, Boolean tratado) {
        LocalDateTime quando = HOJE.minusDays(diasAtras).atTime(LocalTime.of(10, 0));
        return new CitacaoEntrada(quando, (long) diasAtras, 1, tratado);
    }

    // Candidato sem "tratei fora" (dataFora = null)
    private static Candidato cand(long id, boolean oportunidade, boolean naoProcede, CitacaoEntrada... citacoes) {
        return new Candidato(id, List.of(citacoes), oportunidade, null, naoProcede);
    }

    @Test
    void semCandidatosNaoHaTemaAtivo() {
        assertThat(EscolhaDeTema.ativo(List.of(), JANELA, HOJE).isPresent()).isEqualTo(false);
    }

    @Test
    void temaComCitacaoRecenteEstaAtivo() {
        var ativo = EscolhaDeTema.ativo(List.of(cand(1, false, false, c(5, false))), JANELA, HOJE);

        assertThat(ativo.get().id()).isEqualTo(1L);
    }

    @Test
    void temaForaDePautaNaoEstaAtivo() {
        // risco respondido há 56 dias: assunto encerrado
        var ativo = EscolhaDeTema.ativo(List.of(cand(1, false, false, c(56, true))), JANELA, HOJE);

        assertThat(ativo.isPresent()).isEqualTo(false);
    }

    @Test
    void riscoSemRespostaAntigoContinuaAtivo() {
        // risco sem resposta nunca sai de pauta, mesmo com 60 dias
        var ativo = EscolhaDeTema.ativo(List.of(cand(1, false, false, c(60, false))), JANELA, HOJE);

        assertThat(ativo.get().id()).isEqualTo(1L);
    }

    @Test
    void oportunidadePerdidaContinuaAtiva() {
        // oportunidade perdida ainda aparece, o vendedor precisa ver o que perdeu
        var ativo = EscolhaDeTema.ativo(List.of(cand(1, true, false, c(42, false))), JANELA, HOJE);

        assertThat(ativo.get().id()).isEqualTo(1L);
    }

    @Test
    void naoProcedeEIgnoradoEPegaOSeguinte() {
        var ativo = EscolhaDeTema.ativo(List.of(
                cand(1, false, true, c(5, false)),      // marcado "não procede"
                cand(2, false, false, c(4, false))), JANELA, HOJE);

        assertThat(ativo.get().id()).isEqualTo(2L);
    }

    @Test
    void pulaOForaDePautaEPegaOPrimeiroAtivo() {
        var ativo = EscolhaDeTema.ativo(List.of(
                cand(1, false, false, c(56, true)),     // fora de pauta
                cand(2, false, false, c(3, false))), JANELA, HOJE);

        assertThat(ativo.get().id()).isEqualTo(2L);
    }

    @Test
    void temaQueFicouSemCitacaoNumaReanaliseEReaproveitado() {
        var ativo = EscolhaDeTema.ativo(List.of(cand(7, false, false)), JANELA, HOJE);   // sem citações

        assertThat(ativo.get().id()).isEqualTo(7L);
    }

    @Test
    void registroForaValidoTambemMantemOTemaAtivo() {
        // última citação há 40 dias, mas o vendedor registrou "tratei fora" há 5: tratado fora, ainda ativo
        var candidato = new Candidato(1L, List.of(c(40, false)), false, HOJE.minusDays(5), false);

        var ativo = EscolhaDeTema.ativo(List.of(candidato), JANELA, HOJE);

        assertThat(ativo.get().id()).isEqualTo(1L);
    }

    @Test
    void anteriorEOUltimoQueNaoEhNaoProcede() {
        var anterior = EscolhaDeTema.anterior(List.of(
                cand(1, false, false, c(90, true)),
                cand(2, false, false, c(60, true)),
                cand(3, false, true, c(50, false))));   // "não procede": não conta

        assertThat(anterior.get().id()).isEqualTo(2L);
    }

    @Test
    void semCandidatosNaoHaAnterior() {
        assertThat(EscolhaDeTema.anterior(List.of()).isPresent()).isEqualTo(false);
    }
}