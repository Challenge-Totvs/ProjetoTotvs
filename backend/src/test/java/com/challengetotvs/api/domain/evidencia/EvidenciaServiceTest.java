package com.challengetotvs.api.domain.evidencia;

import com.challengetotvs.api.domain.analise.Pseudonimizador;
import com.challengetotvs.api.domain.analise.Pseudonimizador.Entidade;
import com.challengetotvs.api.domain.analise.Pseudonimizador.Tipo;
import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.evidencia.HistoricoDoCliente.Historico;
import com.challengetotvs.api.domain.evidencia.HistoricoDoCliente.Turno;
import com.challengetotvs.api.exception.ApiException;
import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.web.client.RestClient;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

/**
 * A busca é opcional para a tela: sucesso devolve o turno original; timeout, 5xx e Python fora do ar viram lista
 * vazia com aviso (nunca exceção); cliente sem transcrição nem chama o Python.
 */
class EvidenciaServiceTest {

    private static final LocalDateTime DATA = LocalDateTime.of(2026, 10, 9, 14, 30);

    private final HistoricoDoCliente historico = mock(HistoricoDoCliente.class);
    private final Consultor usuario = new Consultor("Marina Souza", "m@x.com", "h", "VENDEDOR");
    private final List<String> corpos = new CopyOnWriteArrayList<>();
    private HttpServer servidor;

    @AfterEach
    void parar() {
        if (servidor != null) {
            servidor.stop(0);
        }
    }

    @Test
    void sucessoDevolveOTurnoOriginalEnviandoSoPseudonimos() throws IOException {
        comTurnos(
                new Turno("12:1", 12L, 1, DATA, "A Acme Logistica precisa do prazo de entrega antes de renovar."),
                new Turno("12:2", 12L, 2, DATA, "O Carlos disse que o preço está alto."));
        subir(troca -> {
            ler(troca);
            responder(troca, 200, "{\"evidencias\":[{\"id\":\"12:1\",\"score\":0.4321},{\"id\":\"99:9\",\"score\":0.1}],"
                    + "\"versaoContrato\":\"v3\"}");
        });

        var resposta = servico(1000).buscar(5L, "  prazo da Acme Logistica ", usuario);

        assertThat(resposta.aviso()).isNull();
        assertThat(resposta.evidencias()).hasSize(1);   // o id desconhecido (99:9) é descartado
        var e = resposta.evidencias().get(0);
        assertThat(e.texto()).isEqualTo("A Acme Logistica precisa do prazo de entrega antes de renovar.");
        assertThat(e.reuniaoId()).isEqualTo(12L);
        assertThat(e.turno()).isEqualTo(1);
        assertThat(e.data()).isEqualTo(DATA);
        assertThat(e.score()).isEqualTo(0.4321);

        assertThat(corpos).hasSize(1);
        assertThat(corpos.get(0))
                .contains("\"consulta\":\"prazo da [EMPRESA_1]\"")
                .contains("\"id\":\"12:2\"").contains("O [PESSOA_1] disse")
                .contains("\"topK\":10")
                .doesNotContain("Acme").doesNotContain("Carlos");
    }

    @Test
    void timeoutDevolveListaVaziaComAvisoSemLancar() throws IOException {
        comTurnos(new Turno("12:1", 12L, 1, DATA, "O prazo de entrega atrasou."));
        subir(troca -> {
            ler(troca);
            dormir(1500);
            responder(troca, 200, "{\"evidencias\":[{\"id\":\"12:1\",\"score\":0.9}]}");
        });

        long inicio = System.nanoTime();
        var resposta = servico(200).buscar(5L, "prazo", usuario);
        long ms = (System.nanoTime() - inicio) / 1_000_000;

        assertThat(resposta.evidencias()).isEmpty();
        assertThat(resposta.aviso()).isEqualTo(EvidenciaService.AVISO_INDISPONIVEL);
        assertThat(ms).isLessThan(1500);
    }

    @Test
    void erro5xxDevolveListaVaziaComAvisoSemLancar() throws IOException {
        comTurnos(new Turno("12:1", 12L, 1, DATA, "O prazo de entrega atrasou."));
        subir(troca -> {
            ler(troca);
            responder(troca, 500, "{\"codigo\":\"erro_interno\",\"mensagem\":\"falhou\"}");
        });

        var resposta = servico(1000).buscar(5L, "prazo", usuario);

        assertThat(resposta.evidencias()).isEmpty();
        assertThat(resposta.aviso()).isEqualTo(EvidenciaService.AVISO_INDISPONIVEL);
    }

    @Test
    void pythonForaDoArDevolveListaVaziaComAviso() throws IOException {
        comTurnos(new Turno("12:1", 12L, 1, DATA, "O prazo de entrega atrasou."));
        int porta;
        try (var s = new java.net.ServerSocket(0)) {
            porta = s.getLocalPort();
        }
        var servico = new EvidenciaService(historico,
                new ClienteEvidencias(RestClient.create("http://127.0.0.1:" + porta), 500));

        var resposta = servico.buscar(5L, "prazo", usuario);

        assertThat(resposta.evidencias()).isEmpty();
        assertThat(resposta.aviso()).isEqualTo(EvidenciaService.AVISO_INDISPONIVEL);
    }

    @Test
    void clienteSemTranscricaoDevolveAvisoProprioENaoChamaOPython() throws IOException {
        comTurnos();
        subir(troca -> {
            ler(troca);
            responder(troca, 200, "{\"evidencias\":[]}");
        });

        var resposta = servico(1000).buscar(5L, "prazo", usuario);

        assertThat(resposta.evidencias()).isEmpty();
        assertThat(resposta.aviso()).isEqualTo(EvidenciaService.AVISO_SEM_TRANSCRICAO);
        assertThat(corpos).isEmpty();
    }

    @Test
    void nadaParecidoDevolveListaVaziaSemAviso() throws IOException {
        comTurnos(new Turno("12:1", 12L, 1, DATA, "Vamos abrir uma filial."));
        subir(troca -> {
            ler(troca);
            responder(troca, 200, "{\"evidencias\":[],\"versaoContrato\":\"v3\"}");
        });

        var resposta = servico(1000).buscar(5L, "garantia", usuario);

        assertThat(resposta.evidencias()).isEmpty();
        assertThat(resposta.aviso()).isNull();
    }

    @Test
    void consultaVaziaOuLongaDemaisE400() {
        var servico = new EvidenciaService(historico, mock(ClienteEvidencias.class));

        assertThatThrownBy(() -> servico.buscar(5L, "   ", usuario))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCodigo()).isEqualTo("consulta_vazia"));
        assertThatThrownBy(() -> servico.buscar(5L, null, usuario)).isInstanceOf(ApiException.class);
        assertThatThrownBy(() -> servico.buscar(5L, "x".repeat(501), usuario))
                .isInstanceOfSatisfying(ApiException.class, e -> assertThat(e.getCodigo()).isEqualTo("consulta_longa"));
    }

    private void comTurnos(Turno... turnos) {
        var pseudo = new Pseudonimizador(List.of(
                new Entidade("Acme Logistica", Tipo.EMPRESA), new Entidade("Carlos", Tipo.PESSOA)));
        when(historico.carregar(any(), any())).thenReturn(new Historico(List.of(turnos), pseudo));
    }

    private EvidenciaService servico(int timeoutMs) {
        var cliente = new ClienteEvidencias(RestClient.create("http://127.0.0.1:" + servidor.getAddress().getPort()), timeoutMs);
        return new EvidenciaService(historico, cliente);
    }

    private void subir(com.sun.net.httpserver.HttpHandler handler) throws IOException {
        servidor = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        servidor.setExecutor(java.util.concurrent.Executors.newCachedThreadPool());
        servidor.createContext("/evidencias", handler);
        servidor.start();
    }

    private String ler(HttpExchange troca) throws IOException {
        String corpo = new String(troca.getRequestBody().readAllBytes(), StandardCharsets.UTF_8);
        corpos.add(corpo);
        return corpo;
    }

    private static void dormir(long ms) {
        try {
            Thread.sleep(ms);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
    }

    private static void responder(HttpExchange troca, int status, String json) throws IOException {
        byte[] bytes = json.getBytes(StandardCharsets.UTF_8);
        troca.getResponseHeaders().add("Content-Type", "application/json");
        troca.sendResponseHeaders(status, bytes.length);
        troca.getResponseBody().write(bytes);
        troca.close();
    }
}
