package com.challengetotvs.api.domain.analise;

import com.fasterxml.jackson.annotation.JsonValue;
import java.util.Locale;

public enum SentimentoGeral {
    POSITIVO, NEUTRO, NEGATIVO;

    @JsonValue
    public String valor() {
        return name().toLowerCase(Locale.ROOT);
    }

    public static SentimentoGeral de(String texto) {
        if (texto == null || texto.isBlank()) {
            return null;
        }
        return valueOf(texto.strip().toUpperCase(Locale.ROOT));
    }
}