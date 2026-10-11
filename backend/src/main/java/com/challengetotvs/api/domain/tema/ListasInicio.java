package com.challengetotvs.api.domain.tema;

import java.util.Comparator;
import java.util.List;

public final class ListasInicio {

    private ListasInicio() {
    }

    private static boolean semTratamento(Situacao s) {
        return s == Situacao.SEM_RETORNO || s == Situacao.OPORTUNIDADE_PERDIDA;
    }

    public static List<TemaResponse> riscos(List<TemaResponse> temas) {
        return temas.stream()
                .filter(t -> t.tipos().contains("risco") && semTratamento(t.situacao()))
                .sorted(Comparator.comparing((TemaResponse t) -> !t.recorrente())
                        .thenComparing(TemaResponse::diasUltimaCitacao, Comparator.reverseOrder()))
                .toList();
    }

    public static List<TemaResponse> oportunidades(List<TemaResponse> temas) {
        return temas.stream()
                .filter(t -> t.tipos().contains("oportunidade") && semTratamento(t.situacao()))
                .sorted(Comparator
                        .comparing((TemaResponse t) -> t.situacao() != Situacao.OPORTUNIDADE_PERDIDA)   // perdidas primeiro
                        .thenComparing(TemaResponse::perdidaEm, Comparator.nullsLast(Comparator.reverseOrder()))
                        .thenComparing(TemaResponse::venceEm, Comparator.nullsLast(Comparator.naturalOrder())))
                .toList();
    }
}