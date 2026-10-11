package com.challengetotvs.api.domain.motor;

import java.time.OffsetDateTime;

public record MotorStatus(String motor, boolean ok, OffsetDateTime verificadoEm) {
}