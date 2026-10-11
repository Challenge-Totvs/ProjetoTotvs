package com.challengetotvs.api.domain.tema;

import org.junit.jupiter.api.Test;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class TemaResponseOrdemTest {

    private static TemaResponse tema(long id, Situacao situacao, boolean recorrente, LocalDate ultimaAtividade) {
        return new TemaResponse(id, 1L, "p", "P", "t", List.of("risco"), situacao, true, false, recorrente, 1, true,
                0, ultimaAtividade, null, null, "", List.of(), null, null, null, null, List.of());
    }

    @Test
    void ordenaPorGrupoDepoisRecorrenteDepoisAtividadeMaisRecente() {
        var lista = new ArrayList<>(List.of(
                tema(1, Situacao.NAO_PROCEDE, false, LocalDate.of(2026, 10, 9)),
                tema(2, Situacao.FORA_DE_PAUTA, false, LocalDate.of(2026, 10, 9)),
                tema(3, Situacao.TRATADO_CONVERSA, false, LocalDate.of(2026, 10, 9)),
                tema(4, Situacao.SEM_RETORNO, false, LocalDate.of(2026, 10, 8)),
                tema(5, Situacao.SEM_RETORNO, false, LocalDate.of(2026, 10, 9)),
                tema(6, Situacao.OPORTUNIDADE_PERDIDA, true, LocalDate.of(2026, 9, 1))));

        lista.sort(TemaResponse.ORDEM);

        assertThat(lista.stream().map(TemaResponse::id).toList()).isEqualTo(List.of(6L, 5L, 4L, 3L, 2L, 1L));
    }
}