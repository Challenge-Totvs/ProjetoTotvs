package com.challengetotvs.api.domain.motor;

import com.challengetotvs.api.domain.motor.StatusMotores.MotorRecebido;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

import java.time.Duration;
import java.time.Instant;
import java.time.OffsetDateTime;
import java.time.ZoneId;
import java.util.List;

@Service
public class MotorStatusService {

    private static final ZoneId FUSO = ZoneId.of("America/Sao_Paulo");
    private static final Duration VALIDADE_CACHE = Duration.ofSeconds(10);

    private final RestClient restClient;

    private List<MotorStatus> ultimo;
    private Instant consultadoEm;

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record HealthPython(List<MotorRecebido> motores) {
    }

    public MotorStatusService(RestClient analiseRestClient) {
        var factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(2000);
        factory.setReadTimeout(3000);
        this.restClient = analiseRestClient.mutate().requestFactory(factory).build();
    }

    public synchronized List<MotorStatus> status() {
        Instant agora = Instant.now();
        if (ultimo != null && Duration.between(consultadoEm, agora).compareTo(VALIDADE_CACHE) < 0) {
            return ultimo;
        }

        OffsetDateTime quando = OffsetDateTime.now(FUSO);
        List<MotorStatus> resultado;
        try {
            var health = restClient.get().uri("/health").retrieve().body(HealthPython.class);
            resultado = StatusMotores.normalizar(health == null ? null : health.motores(), quando);
        } catch (RestClientException e) {
            resultado = StatusMotores.foraDoAr(quando);
        }
        ultimo = resultado;
        consultadoEm = agora;
        return resultado;
    }
}