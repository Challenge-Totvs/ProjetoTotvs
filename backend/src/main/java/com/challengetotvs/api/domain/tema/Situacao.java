package com.challengetotvs.api.domain.tema;

import com.fasterxml.jackson.annotation.JsonValue;
import java.util.Locale;

public enum Situacao {
    SEM_RETORNO,
    OPORTUNIDADE_PERDIDA,
    SEM_LEITURA,
    TRATADO_CONVERSA,
    TRATADO_FORA,
    FORA_DE_PAUTA,
    NAO_PROCEDE;

    @JsonValue
    public String valor() {
        return name().toLowerCase(Locale.ROOT);
    }
}