package com.challengetotvs.api.domain.analise;

import com.fasterxml.jackson.annotation.JsonValue;
import java.util.Locale;

public enum MotorUtilizado {
    LLM1, LLM2, LOCAL, REGRAS;

    @JsonValue
    public String valor() {
        return name().toLowerCase(Locale.ROOT);
    }

    public static MotorUtilizado de(String texto) {
        return valueOf(texto.strip().toUpperCase(Locale.ROOT));
    }
}