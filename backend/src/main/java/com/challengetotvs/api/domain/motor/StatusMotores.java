package com.challengetotvs.api.domain.motor;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import java.time.OffsetDateTime;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class StatusMotores {

    public static final List<String> MOTORES = List.of("llm1", "llm2", "local", "regras");

    private StatusMotores() {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record MotorRecebido(String motor, Boolean ok) {
    }

    public static List<MotorStatus> normalizar(List<MotorRecebido> recebidos, OffsetDateTime quando) {
        if (recebidos == null || recebidos.isEmpty()) {
            return List.of();
        }
        Map<String, Boolean> porMotor = new LinkedHashMap<>();
        for (MotorRecebido r : recebidos) {
            if (r != null && r.motor() != null) {
                porMotor.put(r.motor(), Boolean.TRUE.equals(r.ok()));
            }
        }
        List<MotorStatus> saida = new ArrayList<>();
        for (String motor : MOTORES) {
            saida.add(new MotorStatus(motor, porMotor.getOrDefault(motor, false), quando));
        }
        porMotor.forEach((motor, ok) -> {
            if (!MOTORES.contains(motor)) {
                saida.add(new MotorStatus(motor, ok, quando));
            }
        });
        return saida;
    }

    public static List<MotorStatus> foraDoAr(OffsetDateTime quando) {
        return MOTORES.stream().map(m -> new MotorStatus(m, false, quando)).toList();
    }
}