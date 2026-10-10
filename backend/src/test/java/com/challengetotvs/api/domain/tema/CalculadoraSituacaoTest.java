package com.challengetotvs.api.domain.tema;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.Arguments;
import org.junit.jupiter.params.provider.MethodSource;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.LocalTime;
import java.util.List;
import java.util.stream.Stream;

import static com.challengetotvs.api.domain.tema.Situacao.*;
import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.junit.jupiter.params.provider.Arguments.arguments;

class CalculadoraSituacaoTest {

    private static final LocalDate HOJE = LocalDate.of(2026, 10, 10);

    private static final Boolean RESPONDIDO = true;
    private static final Boolean SEM_RESPOSTA = false;
    private static final Boolean DESCONHECIDO = null;

    enum Tipos {
        RISCO(false),
        OPORTUNIDADE(true),
        AMBOS(true);

        final boolean oportunidade;

        Tipos(boolean oportunidade) {
            this.oportunidade = oportunidade;
        }
    }

    private static CitacaoEntrada c(int diasAtras, Boolean tratado) {
        LocalDateTime quando = HOJE.minusDays(diasAtras).atTime(LocalTime.of(10, 0));
        return new CitacaoEntrada(quando, (long) diasAtras, 1, tratado);
    }

    record Caso(Tipos tipos, int janela, List<CitacaoEntrada> citacoes,
                Integer foraHa, boolean naoProcede,
                Situacao situacao, boolean recorrente, Integer venceEm, Integer perdidaHa) {
    }

    private static Caso caso(Tipos tipos, int janela, List<CitacaoEntrada> citacoes,
                             Integer foraHa, boolean naoProcede,
                             Situacao situacao, boolean recorrente, Integer venceEm, Integer perdidaHa) {
        return new Caso(tipos, janela, citacoes, foraHa, naoProcede, situacao, recorrente, venceEm, perdidaHa);
    }

    static Stream<Arguments> casos() {
        return Stream.of(
                arguments("#1 risco: sem retorno e recorrente",
                        caso(Tipos.RISCO, 30, List.of(c(56, SEM_RESPOSTA), c(23, RESPONDIDO), c(2, SEM_RESPOSTA)), null, false,
                                SEM_RETORNO, true, null, null)),
                arguments("#2 risco respondido há 56 dias sai de pauta",
                        caso(Tipos.RISCO, 30, List.of(c(56, RESPONDIDO)), null, false,
                                FORA_DE_PAUTA, false, null, null)),
                arguments("#3 oportunidade de 42 dias com janela 30 está perdida há 11 dias",
                        caso(Tipos.OPORTUNIDADE, 30, List.of(c(42, SEM_RESPOSTA)), null, false,
                                OPORTUNIDADE_PERDIDA, false, null, 11)),
                arguments("#4 mesma oportunidade com janela 45 perde em 4 dias",
                        caso(Tipos.OPORTUNIDADE, 45, List.of(c(42, SEM_RESPOSTA)), null, false,
                                SEM_RETORNO, false, 4, null)),
                arguments("#5 oportunidade de 2 dias perde em 29 dias",
                        caso(Tipos.OPORTUNIDADE, 30, List.of(c(2, SEM_RESPOSTA)), null, false,
                                SEM_RETORNO, false, 29, null)),
                arguments("#6 duas citações, só uma na janela de 30: não é recorrente",
                        caso(Tipos.RISCO, 30, List.of(c(37, SEM_RESPOSTA), c(9, SEM_RESPOSTA)), null, false,
                                SEM_RETORNO, false, null, null)),
                arguments("#7 as mesmas citações com janela 45: recorrente",
                        caso(Tipos.RISCO, 45, List.of(c(37, SEM_RESPOSTA), c(9, SEM_RESPOSTA)), null, false,
                                SEM_RETORNO, true, null, null)),
                arguments("#8 última citação respondida: tratado na conversa",
                        caso(Tipos.RISCO, 30, List.of(c(37, SEM_RESPOSTA), c(9, RESPONDIDO)), null, false,
                                TRATADO_CONVERSA, false, null, null)),
                arguments("#9 citação de exatos 30 dias ainda conta na janela",
                        caso(Tipos.RISCO, 30, List.of(c(30, RESPONDIDO), c(6, SEM_RESPOSTA)), null, false,
                                SEM_RETORNO, true, null, null)),
                arguments("#10 as mesmas citações com janela 14: não recorrente",
                        caso(Tipos.RISCO, 14, List.of(c(30, RESPONDIDO), c(6, SEM_RESPOSTA)), null, false,
                                SEM_RETORNO, false, null, null)),
                arguments("#11 tema duplo de 6 dias perde em 25 dias",
                        caso(Tipos.AMBOS, 30, List.of(c(6, SEM_RESPOSTA)), null, false,
                                SEM_RETORNO, false, 25, null)),
                arguments("#12 oportunidade de 27 dias perde em 4 dias",
                        caso(Tipos.OPORTUNIDADE, 30, List.of(c(27, SEM_RESPOSTA)), null, false,
                                SEM_RETORNO, false, 4, null)),
                arguments("#13 oportunidade de 27 dias com janela 14 está perdida",
                        caso(Tipos.OPORTUNIDADE, 14, List.of(c(27, SEM_RESPOSTA)), null, false,
                                OPORTUNIDADE_PERDIDA, false, null, 12)),
                arguments("#14 oportunidade de 31 dias é perdida hoje",
                        caso(Tipos.OPORTUNIDADE, 30, List.of(c(31, SEM_RESPOSTA)), null, false,
                                OPORTUNIDADE_PERDIDA, false, null, 0)),
                arguments("#15 oportunidade de 30 dias perde amanhã",
                        caso(Tipos.OPORTUNIDADE, 30, List.of(c(30, SEM_RESPOSTA)), null, false,
                                SEM_RETORNO, false, 1, null)),
                arguments("#16 oportunidade citada hoje perde em 31 dias",
                        caso(Tipos.OPORTUNIDADE, 30, List.of(c(0, SEM_RESPOSTA)), null, false,
                                SEM_RETORNO, false, 31, null)),
                arguments("#17 risco sem resposta de 60 dias não sai de pauta",
                        caso(Tipos.RISCO, 30, List.of(c(60, SEM_RESPOSTA)), null, false,
                                SEM_RETORNO, false, null, null)),
                arguments("#18 duas citações fora da janela: não recorrente",
                        caso(Tipos.RISCO, 30, List.of(c(40, SEM_RESPOSTA), c(35, SEM_RESPOSTA)), null, false,
                                SEM_RETORNO, false, null, null)),
                arguments("#19 não procede vence qualquer outra regra",
                        caso(Tipos.RISCO, 30, List.of(c(20, SEM_RESPOSTA)), null, true,
                                NAO_PROCEDE, false, null, null)),
                arguments("#20 sem resposta e depois respondido: tratado na conversa e recorrente",
                        caso(Tipos.RISCO, 30, List.of(c(18, SEM_RESPOSTA), c(3, RESPONDIDO)), null, false,
                                TRATADO_CONVERSA, true, null, null)),
                arguments("#21 respondido há 30 dias ainda está na janela",
                        caso(Tipos.RISCO, 30, List.of(c(30, RESPONDIDO)), null, false,
                                TRATADO_CONVERSA, false, null, null)),
                arguments("#22 respondido há 31 dias sai de pauta",
                        caso(Tipos.RISCO, 30, List.of(c(31, RESPONDIDO)), null, false,
                                FORA_DE_PAUTA, false, null, null)),
                arguments("#23 respondido há 41 dias com janela 45 segue tratado",
                        caso(Tipos.RISCO, 45, List.of(c(41, RESPONDIDO)), null, false,
                                TRATADO_CONVERSA, false, null, null)),
                arguments("#23b respondido há 41 dias com janela 30 sai de pauta",
                        caso(Tipos.RISCO, 30, List.of(c(41, RESPONDIDO)), null, false,
                                FORA_DE_PAUTA, false, null, null)),
                arguments("#24 registro fora há 5 dias: tratado fora",
                        caso(Tipos.OPORTUNIDADE, 30, List.of(c(10, SEM_RESPOSTA)), 5, false,
                                TRATADO_FORA, false, null, null)),
                arguments("#25 registro fora há 35 dias, além da janela: fora de pauta",
                        caso(Tipos.OPORTUNIDADE, 30, List.of(c(40, SEM_RESPOSTA)), 35, false,
                                FORA_DE_PAUTA, false, null, null)),
                arguments("#26 registro anterior à última citação deixa de valer",
                        caso(Tipos.RISCO, 30, List.of(c(20, SEM_RESPOSTA), c(3, SEM_RESPOSTA)), 10, false,
                                SEM_RETORNO, true, null, null)),
                arguments("#27 registro no mesmo dia da citação vale",
                        caso(Tipos.RISCO, 30, List.of(c(3, SEM_RESPOSTA)), 3, false,
                                TRATADO_FORA, false, null, null)),
                arguments("#28 sem leitura de quem falou",
                        caso(Tipos.RISCO, 30, List.of(c(5, DESCONHECIDO)), null, false,
                                SEM_LEITURA, false, null, null)),
                arguments("#29 sem leitura há 40 dias sai de pauta",
                        caso(Tipos.RISCO, 30, List.of(c(40, DESCONHECIDO)), null, false,
                                FORA_DE_PAUTA, false, null, null)),
                arguments("#30 oportunidade recorrente perde em 26 dias",
                        caso(Tipos.OPORTUNIDADE, 30, List.of(c(20, RESPONDIDO), c(5, SEM_RESPOSTA)), null, false,
                                SEM_RETORNO, true, 26, null)),
                arguments("#31 oportunidade respondida na última citação: tratado na conversa",
                        caso(Tipos.OPORTUNIDADE, 30, List.of(c(45, SEM_RESPOSTA), c(10, RESPONDIDO)), null, false,
                                TRATADO_CONVERSA, false, null, null)),
                arguments("#32 tema duplo de 40 dias: oportunidade perdida há 9 dias",
                        caso(Tipos.AMBOS, 30, List.of(c(40, SEM_RESPOSTA)), null, false,
                                OPORTUNIDADE_PERDIDA, false, null, 9))
        );
    }

    @ParameterizedTest(name = "{0}")
    @MethodSource("casos")
    void calculaASituacaoDoHandoff(String nome, Caso caso) {
        LocalDate dataFora = caso.foraHa() == null ? null : HOJE.minusDays(caso.foraHa());

        ResultadoSituacao r = CalculadoraSituacao.calcular(
                caso.citacoes(), caso.tipos().oportunidade, dataFora,
                caso.naoProcede(), caso.janela(), HOJE);

        LocalDate perdidaEsperada = caso.perdidaHa() == null ? null : HOJE.minusDays(caso.perdidaHa());

        assertThat(r.situacao()).isEqualTo(caso.situacao());
        assertThat(r.recorrente()).isEqualTo(caso.recorrente());
        assertThat(r.venceEm()).isEqualTo(caso.venceEm());
        assertThat(r.perdidaEm()).isEqualTo(perdidaEsperada);
    }

    @Test
    void naDataIgualValeOTurnoMaisAlto() {
        LocalDateTime mesmoMomento = HOJE.minusDays(2).atTime(10, 0);
        List<CitacaoEntrada> citacoes = List.of(
                new CitacaoEntrada(mesmoMomento, 1L, 9, RESPONDIDO),      // turno 9: é a última
                new CitacaoEntrada(mesmoMomento, 1L, 4, SEM_RESPOSTA));   // turno 4: vem antes

        ResultadoSituacao r = CalculadoraSituacao.calcular(citacoes, false, null, false, 30, HOJE);

        assertThat(r.situacao()).isEqualTo(TRATADO_CONVERSA);
    }

    @Test
    void duasCitacoesDaMesmaReuniaoContamUmaVez() {
        LocalDateTime quando = HOJE.minusDays(3).atTime(10, 0);
        List<CitacaoEntrada> citacoes = List.of(
                new CitacaoEntrada(quando, 7L, 2, SEM_RESPOSTA),
                new CitacaoEntrada(quando, 7L, 8, SEM_RESPOSTA));

        ResultadoSituacao r = CalculadoraSituacao.calcular(citacoes, false, null, false, 30, HOJE);

        assertThat(r.reunioesNaJanela()).isEqualTo(1);
        assertThat(r.recorrente()).isEqualTo(false);
    }

    @Test
    void temaSemCitacaoEhErro() {
        assertThatThrownBy(() -> CalculadoraSituacao.calcular(List.of(), false, null, false, 30, HOJE))
                .isInstanceOf(IllegalArgumentException.class);
    }
}