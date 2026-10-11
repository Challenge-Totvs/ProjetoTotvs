package com.challengetotvs.api.domain.tema;

import com.challengetotvs.api.domain.tema.DetectorMudancas.Mudanca;
import com.challengetotvs.api.domain.tema.TemaResponse.RegistroFora;
import org.junit.jupiter.api.Test;

import java.util.List;

import static com.challengetotvs.api.domain.tema.TemaFixture.*;
import static org.assertj.core.api.Assertions.assertThat;

class DetectorMudancasTest {

    private static List<String> tipos(String... t) {
        return List.of(t);
    }

    private static String tipoDaUnica(TemaResponse t) {
        List<Mudanca> r = DetectorMudancas.detectar(List.of(t), HOJE);
        assertThat(r.size()).isEqualTo(1);
        return r.get(0).tipo();
    }

    @Test
    void temaNovoDependeDosTipos() {
        assertThat(tipoDaUnica(simples(1, "risco", Situacao.SEM_RETORNO, cit(3, false)))).isEqualTo("novo_risco");
        assertThat(tipoDaUnica(simples(2, "oportunidade", Situacao.SEM_RETORNO, cit(3, false)))).isEqualTo("nova_oportunidade");
        var duplo = tema(3, tipos("risco", "oportunidade"), Situacao.SEM_RETORNO, false, 20, null, null, cit(3, false));
        assertThat(tipoDaUnica(duplo)).isEqualTo("novo_tema");
    }

    @Test
    void ultimaRespondidaEAnteriorSemRespostaEhTratadoNaConversa() {
        var t = simples(1, "risco", Situacao.TRATADO_CONVERSA, cit(3, true), cit(30, false));
        assertThat(tipoDaUnica(t)).isEqualTo("tratado_conversa");
    }

    @Test
    void ultimaRespondidaEAnteriorRespondidaOuSemLeituraEhVoltouAAparecer() {
        assertThat(tipoDaUnica(simples(1, "risco", Situacao.TRATADO_CONVERSA, cit(3, true), cit(30, true))))
                .isEqualTo("voltou_a_aparecer");
        assertThat(tipoDaUnica(simples(2, "risco", Situacao.TRATADO_CONVERSA, cit(3, true), cit(30, null))))
                .isEqualTo("voltou_a_aparecer");
    }

    @Test
    void ultimaSemRespostaEAnteriorRespondidaEhVoltouSemResposta() {
        assertThat(tipoDaUnica(simples(1, "risco", Situacao.SEM_RETORNO, cit(3, false), cit(20, true))))
                .isEqualTo("voltou_sem_resposta");
    }

    @Test
    void ultimaSemRespostaEAnteriorTambemOuSemLeituraEhCitadoDeNovo() {
        assertThat(tipoDaUnica(simples(1, "risco", Situacao.SEM_RETORNO, cit(3, false), cit(20, false))))
                .isEqualTo("citado_de_novo_sem_resposta");
        assertThat(tipoDaUnica(simples(2, "risco", Situacao.SEM_RETORNO, cit(3, false), cit(20, null))))
                .isEqualTo("citado_de_novo_sem_resposta");
    }

    @Test
    void ultimaSemLeituraNaoSendoAPrimeiraEhCitadoSemLeitura() {
        assertThat(tipoDaUnica(simples(1, "risco", Situacao.SEM_LEITURA, cit(3, null), cit(20, false))))
                .isEqualTo("citado_sem_leitura");
    }

    @Test
    void citacaoForaDos14DiasNaoGeraEvento() {
        assertThat(DetectorMudancas.detectar(List.of(simples(1, "risco", Situacao.SEM_RETORNO, cit(15, false))), HOJE)
                .isEmpty()).isEqualTo(true);
    }

    @Test
    void exatos14DiasAindaContam() {
        assertThat(tipoDaUnica(simples(1, "risco", Situacao.SEM_RETORNO, cit(14, false)))).isEqualTo("novo_risco");
    }

    @Test
    void virouOportunidadePerdidaPelaDataDaPerda() {
        // citada há 40 dias, perdida há 9 (31 dias depois da citação com janela 30)
        var t = tema(1, tipos("oportunidade"), Situacao.OPORTUNIDADE_PERDIDA, false, null,
                HOJE.minusDays(9), null, cit(40, false));

        var r = DetectorMudancas.detectar(List.of(t), HOJE);

        assertThat(r.size()).isEqualTo(1);                       // a citação é antiga: só o evento da perda
        assertThat(r.get(0).tipo()).isEqualTo("virou_oportunidade_perdida");
        assertThat(r.get(0).data()).isEqualTo(HOJE.minusDays(9));
    }

    @Test
    void registroForaRecenteGeraTratadoFora() {
        var fora = new RegistroFora("proposta", "email", HOJE.minusDays(2), null, "Kelwin");
        var t = tema(1, tipos("oportunidade"), Situacao.TRATADO_FORA, false, null, null, fora, cit(30, false));

        var r = DetectorMudancas.detectar(List.of(t), HOJE);

        assertThat(r.size()).isEqualTo(1);
        assertThat(r.get(0).tipo()).isEqualTo("tratado_fora");
    }

    @Test
    void temaNaoProcedeNaoGeraEvento() {
        var t = simples(1, "risco", Situacao.NAO_PROCEDE, cit(2, false));

        assertThat(DetectorMudancas.detectar(List.of(t), HOJE).isEmpty()).isEqualTo(true);
    }

    @Test
    void umTemaPodeGerarMaisDeUmEventoEAListaVemDoMaisRecenteParaOMaisAntigo() {
        var fora = new RegistroFora("proposta", "email", HOJE.minusDays(1), null, "Kelwin");
        var t1 = tema(1, tipos("oportunidade"), Situacao.TRATADO_FORA, false, null, null, fora, cit(5, false), cit(40, false));
        var t2 = simples(2, "risco", Situacao.SEM_RETORNO, cit(3, false));

        var r = DetectorMudancas.detectar(List.of(t1, t2), HOJE);

        assertThat(r.size()).isEqualTo(3);
        assertThat(r.get(0).tipo()).isEqualTo("tratado_fora");                 // ontem
        assertThat(r.get(1).tipo()).isEqualTo("novo_risco");                   // há 3 dias
        assertThat(r.get(2).tipo()).isEqualTo("citado_de_novo_sem_resposta");  // há 5 dias
    }
}