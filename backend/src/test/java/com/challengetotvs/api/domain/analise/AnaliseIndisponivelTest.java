package com.challengetotvs.api.domain.analise;

import com.challengetotvs.api.domain.cliente.Cliente;
import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.reuniao.Reuniao;
import com.challengetotvs.api.domain.reuniao.StatusReuniao;
import com.challengetotvs.api.domain.tema.NaoProcedeDoCliente;
import com.challengetotvs.api.domain.tema.PadraoRepository;
import com.challengetotvs.api.domain.transcricao.Transcricao;
import com.challengetotvs.api.domain.transcricao.TranscricaoRepository;
import com.challengetotvs.api.exception.AnaliseIndisponivelException;
import com.challengetotvs.api.exception.GlobalExceptionHandler;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.http.HttpStatus;
import org.springframework.web.client.RestClient;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.ServerSocket;
import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/** O Python fora do ar ou com erro vira 503 analise_indisponivel, e a reunião fica como estava para tentar de novo. */
class AnaliseIndisponivelTest {

    private HttpServer servidor;

    @AfterEach
    void parar() {
        if (servidor != null) {
            servidor.stop(0);
        }
    }

    @Test
    void pythonComErro5xxViraAnaliseIndisponivel() throws IOException {
        servidor = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        servidor.createContext("/analisar", troca -> {
            byte[] corpo = "{\"codigo\":\"analise_indisponivel\",\"mensagem\":\"nenhum motor\"}".getBytes();
            troca.sendResponseHeaders(503, corpo.length);
            troca.getResponseBody().write(corpo);
            troca.close();
        });
        servidor.start();
        var strategy = new AnaliseServiceClientStrategy(
                RestClient.create("http://127.0.0.1:" + servidor.getAddress().getPort()));

        assertThatThrownBy(() -> strategy.analisar(pedidoMinimo()))
                .isInstanceOf(AnaliseIndisponivelException.class);
    }

    @Test
    void pythonForaDoArViraAnaliseIndisponivel() throws IOException {
        int portaFechada;
        try (var s = new ServerSocket(0)) {
            portaFechada = s.getLocalPort();
        }
        var strategy = new AnaliseServiceClientStrategy(RestClient.create("http://127.0.0.1:" + portaFechada));

        assertThatThrownBy(() -> strategy.analisar(pedidoMinimo()))
                .isInstanceOf(AnaliseIndisponivelException.class);
    }

    @Test
    void handlerDevolve503ComCodigoDoContrato() {
        var resposta = new GlobalExceptionHandler().tratar503(new AnaliseIndisponivelException("fora do ar"));

        assertThat(resposta.getStatusCode()).isEqualTo(HttpStatus.SERVICE_UNAVAILABLE);
        assertThat(resposta.getBody().codigo()).isEqualTo("analise_indisponivel");
    }

    @Test
    void falhaNaoGravaNadaEReuniaoContinuaAguardando() {
        var vendedor = new Consultor("Vendedor", "v@insightcall.test", "x", "VENDEDOR");
        vendedor.setId(1L);
        var cliente = new Cliente("Cliente Sintetico", null, "Varejo", vendedor);
        var reuniao = new Reuniao(vendedor, cliente, null, LocalDateTime.of(2026, 10, 13, 9, 0),
                "Reuniao", 30, StatusReuniao.REALIZADA);
        var transcricao = new Transcricao(reuniao, "[LOCUTOR 1] Bom dia.\n[LOCUTOR 2] Bom dia.", "COLADO",
                "hash", 40, 2, 2);

        var transcricoes = mock(TranscricaoRepository.class);
        when(transcricoes.findById(anyLong())).thenReturn(Optional.of(transcricao));
        var padroes = mock(PadraoRepository.class);
        when(padroes.findByAtivoTrueOrderByNomeAsc()).thenReturn(List.of());
        var gravador = mock(GravadorAnalise.class);
        AnaliseStrategy foraDoAr = pedido -> {
            throw new AnaliseIndisponivelException("fora do ar");
        };
        var service = new AnaliseService(transcricoes, padroes, foraDoAr, gravador, mock(NaoProcedeDoCliente.class));

        assertThatThrownBy(() -> service.analisar(10L, vendedor)).isInstanceOf(AnaliseIndisponivelException.class);
        verify(gravador, never()).gravar(any(), any(), any(), anyLong());
        assertThat(reuniao.getStatus()).isEqualTo(StatusReuniao.REALIZADA);
    }

    private ContratoV3.Pedido pedidoMinimo() {
        return new ContratoV3.Pedido(List.of(new ContratoV3.TurnoPedido(1, 1, "Bom dia.")),
                "2026-10-13", List.of(), List.of());
    }
}
