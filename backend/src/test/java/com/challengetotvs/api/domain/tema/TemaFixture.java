package com.challengetotvs.api.domain.tema;

import com.challengetotvs.api.domain.tema.TemaResponse.CitacaoResponse;
import com.challengetotvs.api.domain.tema.TemaResponse.RegistroFora;

import java.time.LocalDate;
import java.util.List;

final class TemaFixture {

    static final LocalDate HOJE = LocalDate.of(2026, 10, 10);

    private TemaFixture() {
    }

    // Citação de "diasAtras" dias antes de HOJE; tratado: true = respondida, false = sem resposta, null = sem leitura
    static CitacaoResponse cit(int diasAtras, Boolean tratado) {
        return new CitacaoResponse(1L, "Reunião", HOJE.minusDays(diasAtras), 1, tratado, "texto", 1, null, List.of());
    }

    // As citações são passadas da MAIS RECENTE para a mais antiga, como o MontadorTemas devolve
    static TemaResponse tema(long id, List<String> tipos, Situacao situacao, boolean recorrente,
                             Integer venceEm, LocalDate perdidaEm, RegistroFora fora, CitacaoResponse... citacoes) {
        long diasUltima = citacoes.length == 0 ? 0 : HOJE.toEpochDay() - citacoes[0].reuniaoData().toEpochDay();
        return new TemaResponse(id, 7L, "Cliente " + id, "p", "Padrão", "Tema " + id, tipos, situacao,
                true, true, recorrente, 1, true, diasUltima, HOJE, venceEm, perdidaEm, "",
                List.of(citacoes), fora, null, null, null, List.of());
    }

    // Atalho: tema simples de um tipo só
    static TemaResponse simples(long id, String tipo, Situacao situacao, CitacaoResponse... citacoes) {
        return tema(id, List.of(tipo), situacao, false, null, null, null, citacoes);
    }
}