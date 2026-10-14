package com.challengetotvs.api.domain.evidencia;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.List;
import java.util.Optional;

/**
 * Cliente do POST /evidencias (docs/contrato/evidencias.md). Nunca lança: falha vira Optional vazio, para o
 * chamador distinguir "o Python falhou" (vazio) de "nada parecido" (lista vazia).
 */
@Slf4j
@Service
public class ClienteEvidencias {

    static final int TIMEOUT_MS = 3000;
    static final int MAXIMO_TEXTO = 2000;   // evidencias.md §2
    static final int MAXIMO_TRECHOS = 500;  // evidencias.md §2
    static final int TOP_K = 10;

    private final RestClient restClient;

    public record Trecho(String id, String texto) {
    }

    public record Achado(String id, double score) {
    }

    record PedidoEvidencias(String consulta, List<Trecho> trechos, int topK) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    record RespostaEvidencias(List<Item> evidencias) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    record Item(String id, Double score) {
    }

    @Autowired
    public ClienteEvidencias(RestClient analiseRestClient) {
        this(analiseRestClient, TIMEOUT_MS);
    }

    ClienteEvidencias(RestClient analiseRestClient, int timeoutMs) {
        var factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(timeoutMs);
        factory.setReadTimeout(timeoutMs);
        this.restClient = analiseRestClient.mutate().requestFactory(factory).build();
    }

    /** Os achados em ordem de score, ou vazio se o Python falhou (timeout, 4xx, 5xx, corpo inválido). */
    public Optional<List<Achado>> buscar(String consulta, List<Trecho> trechos) {
        var enviados = trechos.stream().limit(MAXIMO_TRECHOS).toList();
        try {
            var resposta = restClient.post()
                    .uri("/evidencias")
                    .body(new PedidoEvidencias(consulta, enviados, TOP_K))
                    .retrieve()
                    .body(RespostaEvidencias.class);
            if (resposta == null || resposta.evidencias() == null) {
                log.warn("/evidencias devolveu corpo vazio");
                return Optional.empty();
            }
            return Optional.of(resposta.evidencias().stream()
                    .filter(i -> i.id() != null && i.score() != null)
                    .map(i -> new Achado(i.id(), i.score()))
                    .toList());
        } catch (RuntimeException e) {
            log.warn("/evidencias falhou ({}); a busca volta vazia com aviso", e.getClass().getSimpleName());
            return Optional.empty();
        }
    }
}
