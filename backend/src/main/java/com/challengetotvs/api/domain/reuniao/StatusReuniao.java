package com.challengetotvs.api.domain.reuniao;

import com.fasterxml.jackson.annotation.JsonValue;

public enum StatusReuniao {
    AGENDADA("agendada"),
    REALIZADA("aguardando"),
    ANALISADA("analisada");

    private final String valorJson;

    StatusReuniao(String valorJson) {
        this.valorJson = valorJson;
    }

    @JsonValue
    public String valorJson() {
        return valorJson;
    }
}