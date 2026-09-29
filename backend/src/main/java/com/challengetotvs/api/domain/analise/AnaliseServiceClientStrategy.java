package com.challengetotvs.api.domain.analise;


import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

@Service
@RequiredArgsConstructor
public class AnaliseServiceClientStrategy implements AnaliseStrategy{

    private final RestClient restClient;

    @Override
    public ResultadoAnalise analisar(String texto) {
        AnaliseRequest request = new AnaliseRequest(
                texto,
                "TXT"
        );
        return restClient.post()
                .uri("/analisar")
                .body(request)
                .retrieve()
                .body(ResultadoAnalise.class);
    }
}
