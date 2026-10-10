package com.challengetotvs.api.domain.tema;

import com.fasterxml.jackson.annotation.JsonValue; // anotação do Jackson (no Jackson 3 ela continua com este pacote)
import java.util.Locale;

public enum TipoPadrao {
    RISCO,
    OPORTUNIDADE;

    @JsonValue
    public String valor() {
        return name().toLowerCase(Locale.ROOT);
    }
}