package com.challengetotvs.api.domain.analise;

import com.challengetotvs.api.exception.AnaliseIndisponivelException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Service
@RequiredArgsConstructor
public class AnaliseServiceClientStrategy implements AnaliseStrategy {

    private final RestClient restClient;       // o da RestClientConfig (URL do analise-service e timeout)

    @Override
    public ContratoV3.Resposta analisar(ContratoV3.Pedido pedido) {
        try {
            return restClient.post()
                    .uri("/analisar")
                    .body(pedido)
                    .retrieve()
                    .body(ContratoV3.Resposta.class);
        } catch (RestClientException e) {
            throw new AnaliseIndisponivelException("Servidor de analise está indisponivel no momento!", e);
        }
    }
}