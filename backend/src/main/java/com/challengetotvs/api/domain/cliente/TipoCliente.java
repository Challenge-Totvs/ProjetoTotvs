package com.challengetotvs.api.domain.cliente;

import com.fasterxml.jackson.annotation.JsonValue;
import java.util.Locale;

public enum TipoCliente {
    ATIVO,
    PROSPECT;

    @JsonValue
    public String valor() {
        return name().toLowerCase(Locale.ROOT);
    }
}