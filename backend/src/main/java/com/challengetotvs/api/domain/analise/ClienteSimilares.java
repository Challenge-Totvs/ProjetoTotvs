package com.challengetotvs.api.domain.analise;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.util.HashMap;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * Cliente do POST /similares (docs/contrato/similares.md): o tema novo se parece com algum "não procede" do cliente?
 * É opcional: qualquer falha vira log e o tema segue sem aviso. Nunca lança.
 */
@Slf4j
@Service
public class ClienteSimilares {

    static final int TIMEOUT_MS = 3000;
    static final int MAXIMO_TEXTO = 2000;        // similares.md §2
    static final int MAXIMO_REFERENCIAS = 200;   // similares.md §2

    private final RestClient restClient;

    public record Referencia(String id, String texto) {
    }

    record PedidoSimilares(String texto, List<Referencia> referencias, int topK) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    record RespostaSimilares(List<Similar> similares) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    record Similar(String id, Double score) {
    }

    @Autowired
    public ClienteSimilares(RestClient analiseRestClient) {
        this(analiseRestClient, TIMEOUT_MS);
    }

    ClienteSimilares(RestClient analiseRestClient, int timeoutMs) {
        var factory = new SimpleClientHttpRequestFactory();
        factory.setConnectTimeout(timeoutMs);
        factory.setReadTimeout(timeoutMs);
        this.restClient = analiseRestClient.mutate().requestFactory(factory).build();
    }

    /**
     * Para cada padrão dos temas, o id da referência mais parecida (só os que passaram do limiar).
     * Na primeira falha as consultas restantes são puladas: com o Python lento, não somamos 3 s por tema.
     */
    public Map<String, Long> maisParecidos(List<ContratoV3.TemaResposta> temas, List<Referencia> referencias) {
        Map<String, Long> saida = new HashMap<>();
        var validas = referencias.stream()
                .filter(r -> r.id() != null && r.texto() != null && !r.texto().isBlank())
                .limit(MAXIMO_REFERENCIAS)
                .map(r -> new Referencia(r.id(), cortar(r.texto())))
                .toList();
        if (validas.isEmpty()) {
            return saida;
        }

        var consultados = new HashSet<String>();
        for (var tema : temas) {
            if (tema.padrao() == null || tema.texto() == null || tema.texto().isBlank()
                    || !consultados.add(tema.padrao())) {
                continue;
            }
            try {
                var resposta = restClient.post()
                        .uri("/similares")
                        .body(new PedidoSimilares(cortar(tema.texto()), validas, 1))
                        .retrieve()
                        .body(RespostaSimilares.class);
                idMaisParecido(resposta).ifPresent(id -> saida.put(tema.padrao(), id));
            } catch (RuntimeException e) {
                log.warn("/similares falhou ({}); os temas desta análise seguem sem semelhanteNaoProcede",
                        e.getClass().getSimpleName());
                break;
            }
        }
        return saida;
    }

    private Optional<Long> idMaisParecido(RespostaSimilares resposta) {
        if (resposta == null || resposta.similares() == null || resposta.similares().isEmpty()) {
            return Optional.empty();
        }
        try {
            return Optional.of(Long.valueOf(resposta.similares().get(0).id()));
        } catch (NumberFormatException e) {
            return Optional.empty();   // o id é nosso; se voltou outra coisa, não há o que mostrar
        }
    }

    private static String cortar(String texto) {
        String limpo = texto.strip();
        return limpo.length() <= MAXIMO_TEXTO ? limpo : limpo.substring(0, MAXIMO_TEXTO);
    }
}
