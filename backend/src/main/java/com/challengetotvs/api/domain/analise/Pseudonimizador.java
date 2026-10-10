package com.challengetotvs.api.domain.analise;

import java.util.Collections;
import java.util.Comparator;
import java.util.EnumMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.stream.Collectors;

public final class Pseudonimizador {

    public enum Tipo {
        PESSOA,
        EMPRESA,
        LOCAL
    }

    public record Entidade(String termo, Tipo tipo) {
    }

    private static final Pattern PSEUDONIMO = Pattern.compile("\\[(?:PESSOA|EMPRESA|LOCAL)_\\d+]");

    private final Map<String, String> pseudonimoPorTermo = new LinkedHashMap<>();
    private final Map<String, String> originalPorPseudonimo = new LinkedHashMap<>();
    private final Pattern termos;

    public Pseudonimizador(List<Entidade> entidades) {
        Map<Tipo, Integer> contador = new EnumMap<>(Tipo.class);
        for (Entidade e : entidades) {
            String termo = e.termo() == null ? "" : e.termo().strip();
            if (termo.isEmpty() || pseudonimoPorTermo.containsKey(termo)) {
                continue;
            }
            int numero = contador.merge(e.tipo(), 1, Integer::sum);
            String pseudonimo = "[" + e.tipo().name() + "_" + numero + "]";
            pseudonimoPorTermo.put(termo, pseudonimo);
            originalPorPseudonimo.put(pseudonimo, termo);
        }

        if (pseudonimoPorTermo.isEmpty()) {
            this.termos = null;
            return;
        }
        String alternativas = pseudonimoPorTermo.keySet().stream()
                .sorted(Comparator.comparingInt(String::length).reversed())
                .map(Pattern::quote)
                .collect(Collectors.joining("|"));
        this.termos = Pattern.compile("(?<!\\p{L})(?:" + alternativas + ")(?!\\p{L})");
    }

    public String pseudonimizar(String texto) {
        if (texto == null || termos == null) {
            return texto;
        }
        return termos.matcher(texto)
                .replaceAll(m -> Matcher.quoteReplacement(pseudonimoPorTermo.get(m.group())));
    }

    public String restaurar(String texto) {
        if (texto == null) {
            return null;
        }
        return PSEUDONIMO.matcher(texto)
                .replaceAll(m -> Matcher.quoteReplacement(
                        originalPorPseudonimo.getOrDefault(m.group(), m.group())));
    }

    public Map<String, String> mapa() {
        return Collections.unmodifiableMap(originalPorPseudonimo);
    }
}