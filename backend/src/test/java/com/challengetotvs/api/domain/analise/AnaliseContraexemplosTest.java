package com.challengetotvs.api.domain.analise;

import com.challengetotvs.api.domain.cliente.Cliente;
import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.reuniao.Reuniao;
import com.challengetotvs.api.domain.reuniao.StatusReuniao;
import com.challengetotvs.api.domain.tema.NaoProcedeDoCliente;
import com.challengetotvs.api.domain.tema.NaoProcedeDoCliente.Trecho;
import com.challengetotvs.api.domain.tema.PadraoRepository;
import com.challengetotvs.api.domain.transcricao.Transcricao;
import com.challengetotvs.api.domain.transcricao.TranscricaoRepository;
import com.challengetotvs.api.exception.AnaliseIndisponivelException;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/** O pedido do /analisar leva os "não procede" do mesmo cliente como contraexemplos (contrato v3 §3.1). */
class AnaliseContraexemplosTest {

    private static final long CLIENTE_ID = 7L;

    private final AtomicReference<ContratoV3.Pedido> enviado = new AtomicReference<>();
    private final NaoProcedeDoCliente naoProcede = mock(NaoProcedeDoCliente.class);
    private AnaliseService service;
    private Consultor vendedor;

    @BeforeEach
    void montar() {
        vendedor = new Consultor("Vendedor Teste", "v@insightcall.test", "x", "VENDEDOR");
        vendedor.setId(1L);
        var cliente = new Cliente("Cliente Sintetico", null, "Varejo", vendedor);
        cliente.setId(CLIENTE_ID);
        var reuniao = new Reuniao(vendedor, cliente, null, LocalDateTime.of(2026, 10, 13, 9, 0),
                "Reuniao", 30, StatusReuniao.REALIZADA);
        var transcricao = new Transcricao(reuniao, "[LOCUTOR 1] Bom dia.\n[LOCUTOR 2] Bom dia.", "COLADO",
                "hash", 40, 2, 2);

        var transcricoes = mock(TranscricaoRepository.class);
        when(transcricoes.findById(anyLong())).thenReturn(Optional.of(transcricao));
        var padroes = mock(PadraoRepository.class);
        when(padroes.findByAtivoTrueOrderByNomeAsc()).thenReturn(List.of());
        AnaliseStrategy capturaEPara = pedido -> {
            enviado.set(pedido);
            throw new AnaliseIndisponivelException("o teste só olha o pedido");
        };
        service = new AnaliseService(transcricoes, padroes, capturaEPara, mock(GravadorAnalise.class), naoProcede,
                mock(ClienteSimilares.class));
    }

    @Test
    void clienteSemNaoProcedeEnviaListaVazia() {
        when(naoProcede.doCliente(CLIENTE_ID)).thenReturn(List.of());

        assertThatThrownBy(() -> service.analisar(10L, vendedor)).isInstanceOf(AnaliseIndisponivelException.class);

        assertThat(enviado.get().contraexemplos()).isEmpty();
    }

    @Test
    void clienteComNaoProcedeEnviaPadraoTextoPseudonimizadoEMotivo() {
        when(naoProcede.doCliente(CLIENTE_ID)).thenReturn(List.of(
                new Trecho(31L, "cancelamento_citado", "A Cliente Sintetico vai cancelar a reserva do salão.", "fora_contexto"),
                new Trecho(32L, "preco_objecao", "O valor ficou salgado.", "outro")));

        assertThatThrownBy(() -> service.analisar(10L, vendedor)).isInstanceOf(AnaliseIndisponivelException.class);

        verify(naoProcede).doCliente(CLIENTE_ID);
        assertThat(enviado.get().contraexemplos()).containsExactly(
                new ContratoV3.Contraexemplo("cancelamento_citado", "A [EMPRESA_1] vai cancelar a reserva do salão.",
                        "fora_contexto"),
                new ContratoV3.Contraexemplo("preco_objecao", "O valor ficou salgado.", "outro"));
    }

    @Test
    void textoLongoECortadoNoLimiteDoContrato() {
        when(naoProcede.doCliente(CLIENTE_ID)).thenReturn(List.of(
                new Trecho(31L, "renovacao", "a".repeat(800), "outro")));

        assertThatThrownBy(() -> service.analisar(10L, vendedor)).isInstanceOf(AnaliseIndisponivelException.class);

        assertThat(enviado.get().contraexemplos().get(0).texto()).hasSize(AnaliseService.MAXIMO_TEXTO_CONTRAEXEMPLO);
    }
}
