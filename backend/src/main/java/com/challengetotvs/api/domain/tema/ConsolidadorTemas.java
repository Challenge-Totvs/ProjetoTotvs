package com.challengetotvs.api.domain.tema;

import com.challengetotvs.api.domain.analise.ContratoV3.TemaResposta;

import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class ConsolidadorTemas {

    private ConsolidadorTemas() {
    }

    public record TemaConsolidado(
            String padrao, String titulo, boolean risco, boolean oportunidade,
            int turno, Integer turnoFim, Boolean tratado, String texto) {
    }

    public static List<TemaConsolidado> consolidar(List<TemaResposta> temas, Map<String, TipoPadrao> tipoPorPadrao) {
        Map<String, List<TemaResposta>> porPadrao = new LinkedHashMap<>();
        for (TemaResposta t : temas) {
            if (t.padrao() == null || !tipoPorPadrao.containsKey(t.padrao())) {
                continue;
            }
            if (t.texto() == null || t.texto().isBlank()) {
                continue;
            }
            porPadrao.computeIfAbsent(t.padrao(), chave -> new ArrayList<>()).add(t);
        }

        List<TemaConsolidado> saida = new ArrayList<>();
        for (Map.Entry<String, List<TemaResposta>> grupo : porPadrao.entrySet()) {
            String padrao = grupo.getKey();
            List<TemaResposta> lista = grupo.getValue();

            TemaResposta escolhida = lista.stream()
                    .filter(t -> Boolean.FALSE.equals(t.tratado()))
                    .findFirst()
                    .orElse(lista.get(0));

            boolean risco = lista.stream()
                    .anyMatch(t -> t.tipos().stream().anyMatch("risco"::equalsIgnoreCase));
            boolean oportunidade = lista.stream()
                    .anyMatch(t -> t.tipos().stream().anyMatch("oportunidade"::equalsIgnoreCase));
            if (!risco && !oportunidade) {       // a LLM não disse: vale o tipo do padrão
                if (tipoPorPadrao.get(padrao) == TipoPadrao.RISCO) {
                    risco = true;
                } else {
                    oportunidade = true;
                }
            }

            saida.add(new TemaConsolidado(padrao, lista.get(0).titulo(), risco, oportunidade,
                    escolhida.turno(), escolhida.turnoFim(), escolhida.tratado(), escolhida.texto()));
        }
        return saida;
    }
}