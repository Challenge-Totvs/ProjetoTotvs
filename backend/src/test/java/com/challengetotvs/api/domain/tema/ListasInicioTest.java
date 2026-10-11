package com.challengetotvs.api.domain.tema;

import org.junit.jupiter.api.Test;

import java.util.List;

import static com.challengetotvs.api.domain.tema.TemaFixture.*;
import static org.assertj.core.api.Assertions.assertThat;

class ListasInicioTest {

    private static List<Long> ids(List<TemaResponse> lista) {
        return lista.stream().map(TemaResponse::id).toList();
    }

    @Test
    void riscosSoTrazSemRetornoEPerdidaESaiDosOutros() {
        var temas = List.of(
                simples(1, "risco", Situacao.SEM_RETORNO, cit(5, false)),
                simples(2, "risco", Situacao.TRATADO_CONVERSA, cit(5, true)),
                simples(3, "oportunidade", Situacao.SEM_RETORNO, cit(5, false)),
                simples(4, "risco", Situacao.NAO_PROCEDE, cit(5, false)));

        assertThat(ids(ListasInicio.riscos(temas))).isEqualTo(List.of(1L));
    }

    @Test
    void riscosRecorrentesPrimeiroDepoisOsSemRespostaHaMaisTempo() {
        var temas = List.of(
                simples(1, "risco", Situacao.SEM_RETORNO, cit(5, false)),
                simples(2, "risco", Situacao.SEM_RETORNO, cit(20, false)),
                tema(3, List.of("risco"), Situacao.SEM_RETORNO, true, null, null, null, cit(2, false)));

        assertThat(ids(ListasInicio.riscos(temas))).isEqualTo(List.of(3L, 2L, 1L));
    }

    @Test
    void temaDuploApareceNasDuasListas() {
        var duplo = tema(1, List.of("risco", "oportunidade"), Situacao.SEM_RETORNO, false, 20, null, null, cit(10, false));

        assertThat(ids(ListasInicio.riscos(List.of(duplo)))).isEqualTo(List.of(1L));
        assertThat(ids(ListasInicio.oportunidades(List.of(duplo)))).isEqualTo(List.of(1L));
    }

    @Test
    void oportunidadesPerdidasPrimeiroDaMaisRecenteParaAMaisAntigaDepoisSemRetornoPorQuemPerdeAntes() {
        var temas = List.of(
                tema(1, List.of("oportunidade"), Situacao.SEM_RETORNO, false, 22, null, null, cit(9, false)),
                tema(2, List.of("oportunidade"), Situacao.OPORTUNIDADE_PERDIDA, false, null, HOJE.minusDays(20), null, cit(51, false)),
                tema(3, List.of("oportunidade"), Situacao.SEM_RETORNO, false, 4, null, null, cit(27, false)),
                tema(4, List.of("oportunidade"), Situacao.OPORTUNIDADE_PERDIDA, false, null, HOJE.minusDays(6), null, cit(37, false)));

        assertThat(ids(ListasInicio.oportunidades(temas))).isEqualTo(List.of(4L, 2L, 3L, 1L));
    }
}