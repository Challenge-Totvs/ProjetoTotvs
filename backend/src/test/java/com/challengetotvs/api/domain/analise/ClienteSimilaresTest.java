package com.challengetotvs.api.domain.analise;

import com.challengetotvs.api.domain.analise.ClienteSimilares.Referencia;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.web.client.RestClient;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CopyOnWriteArrayList;

import static org.assertj.core.api.Assertions.assertThat;

/** O /similares é opcional: sucesso preenche o mapa; timeout, 5xx e falta de referência devolvem vazio sem lançar. */
class ClienteSimilaresTest {

    private static final List<ContratoV3.TemaResposta> DOIS_TEMAS = List.of(
            tema("suporte_insatisfacao", "O suporte está demorando demais para responder os chamados."),
            tema("preco_objecao", "O preço ficou muito caro para o que a gente usa."));

    private static final List<Referencia> REFERENCIAS = List.of(
            new Referencia("31", "O suporte demora demais para responder, ninguém retornou."),
            new Referencia("32", "Vamos abrir uma nova filial no mês que vem."));

    private final List<String> corpos = new CopyOnWriteArrayList<>();
    private HttpServer servidor;

    @AfterEach
    void parar() {
        if (servidor != null) {
            servidor.stop(0);
        }
    }

    @Test
    void sucessoGuardaOIdMaisParecidoPorPadrao() throws IOException {
        subir(troca -> {
            String corpo = ler(troca);
            responder(troca, 200, corpo.contains("suporte_insatisfacao") || corpo.contains("O suporte está")
                    ? "{\"similares\":[{\"id\":\"31\",\"score\":0.259}],\"versaoContrato\":\"v3\"}"
                    : "{\"similares\":[],\"versaoContrato\":\"v3\"}");
        });

        Map<String, Long> mapa = cliente(1000).maisParecidos(DOIS_TEMAS, REFERENCIAS);

        assertThat(mapa).containsExactly(Map.entry("suporte_insatisfacao", 31L));
        assertThat(corpos).hasSize(2);
        assertThat(corpos.get(0)).contains("\"topK\":1").contains("\"id\":\"31\"").doesNotContain("limiar");
    }

    @Test
    void timeoutDevolveVazioSemLancarENaoInsiste() throws IOException {
        subir(troca -> {
            ler(troca);
            try {
                Thread.sleep(1500);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
            }
            responder(troca, 200, "{\"similares\":[{\"id\":\"31\",\"score\":0.9}]}");
        });

        long inicio = System.nanoTime();
        Map<String, Long> mapa = cliente(200).maisParecidos(DOIS_TEMAS, REFERENCIAS);
        long ms = (System.nanoTime() - inicio) / 1_000_000;

        assertThat(mapa).isEmpty();
        assertThat(corpos).hasSize(1);          // a segunda consulta é pulada
        assertThat(ms).isLessThan(1500);
    }

    @Test
    void erro5xxDevolveVazioSemLancarENaoInsiste() throws IOException {
        subir(troca -> {
            ler(troca);
            responder(troca, 500, "{\"codigo\":\"erro_interno\",\"mensagem\":\"falhou\"}");
        });

        Map<String, Long> mapa = cliente(1000).maisParecidos(DOIS_TEMAS, REFERENCIAS);

        assertThat(mapa).isEmpty();
        assertThat(corpos).hasSize(1);
    }

    @Test
    void semReferenciasNemChamaOPython() throws IOException {
        subir(troca -> {
            ler(troca);
            responder(troca, 200, "{\"similares\":[]}");
        });

        assertThat(cliente(1000).maisParecidos(DOIS_TEMAS, List.of())).isEmpty();
        assertThat(cliente(1000).maisParecidos(DOIS_TEMAS, List.of(new Referencia("33", "   ")))).isEmpty();
        assertThat(corpos).isEmpty();
    }

    @Test
    void pythonForaDoArDevolveVazio() throws IOException {
        int porta;
        try (var s = new java.net.ServerSocket(0)) {
            porta = s.getLocalPort();
        }
        var cliente = new ClienteSimilares(RestClient.create("http://127.0.0.1:" + porta), 500);

        assertThat(cliente.maisParecidos(DOIS_TEMAS, REFERENCIAS)).isEmpty();
    }

    private ClienteSimilares cliente(int timeoutMs) {
        return new ClienteSimilares(RestClient.create("http://127.0.0.1:" + servidor.getAddress().getPort()), timeoutMs);
    }

    private void subir(com.sun.net.httpserver.HttpHandler handler) throws IOException {
        servidor = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        servidor.setExecutor(java.util.concurrent.Executors.newCachedThreadPool());
        servidor.createContext("/similares", handler);
        servidor.start();
    }

    private String ler(HttpExchange troca) throws IOException {
        String corpo = new String(troca.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
        corpos.add(corpo);
        return corpo;
    }

    private static void responder(HttpExchange troca, int status, String json) throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        troca.getResponseHeaders().add("Content-Type", "application/json");
        troca.sendResponseHeaders(status, bytes.length);
        troca.getResponseBody().write(bytes);
        troca.close();
    }

    private static ContratoV3.TemaResposta tema(String padrao, String texto) {
        return new ContratoV3.TemaResposta(padrao, "titulo", List.of("risco"), 3, null, false, texto);
    }
}
