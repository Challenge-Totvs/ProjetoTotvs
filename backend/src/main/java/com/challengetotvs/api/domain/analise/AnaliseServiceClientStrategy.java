package com.challengetotvs.api.domain.analise;


import com.challengetotvs.api.exception.AnaliseIndisponivelException;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Service
@RequiredArgsConstructor
public class AnaliseServiceClientStrategy implements AnaliseStrategy{

    private final RestClient restClient;

    @Override
    public ResultadoAnalise analisar(String texto) {
        try {
            AnaliseRequest request = new AnaliseRequest(
                    texto,
                    "TXT"
            );
            return restClient.post()
                    .uri("/analisar")
                    .body(request)
                    .retrieve()
                    .body(ResultadoAnalise.class);
        } catch (RestClientException e) {
            throw new AnaliseIndisponivelException("Servidor de analise está indisponivel no momento!", e);
        }
    }
}
