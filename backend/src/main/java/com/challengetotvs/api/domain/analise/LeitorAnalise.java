package com.challengetotvs.api.domain.analise;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import tools.jackson.databind.ObjectMapper;

import java.util.Arrays;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Component
@RequiredArgsConstructor
public class LeitorAnalise {

    private final ObjectMapper objectMapper;

    public Map<Integer, String> papeis(String json) {
        if (json == null || json.isBlank()) {
            return Map.of();
        }
        try {
            Map<?, ?> bruto = objectMapper.readValue(json, Map.class);
            Map<Integer, String> papeis = new HashMap<>();
            bruto.forEach((chave, valor) -> {
                if (valor != null) {
                    papeis.put(Integer.parseInt(chave.toString()), valor.toString());
                }
            });
            return papeis;
        } catch (RuntimeException e) {
            return Map.of();
        }
    }

    public Map<String, String> entidades(String json) {
        if (json == null || json.isBlank()) {
            return Map.of();
        }
        try {
            Map<?, ?> bruto = objectMapper.readValue(json, Map.class);
            Map<String, String> entidades = new LinkedHashMap<>();
            bruto.forEach((chave, valor) -> {
                if (valor != null) {
                    entidades.put(chave.toString(), valor.toString());
                }
            });
            return entidades;
        } catch (RuntimeException e) {
            return Map.of();
        }
    }

    public <T> List<T> lista(String json, Class<T[]> tipo) {
        if (json == null || json.isBlank()) {
            return List.of();
        }
        try {
            return Arrays.asList(objectMapper.readValue(json, tipo));
        } catch (RuntimeException e) {
            return List.of();
        }
    }

    public List<double[]> serie(String json) {
        if (json == null || json.isBlank()) {
            return List.of();
        }
        try {
            return Arrays.asList(objectMapper.readValue(json, double[][].class));
        } catch (RuntimeException e) {
            return List.of();
        }
    }
}