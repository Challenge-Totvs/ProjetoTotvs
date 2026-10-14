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
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.anyLong;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

/** Depois do /analisar, os "não procede" do cliente vão ao /similares e o resultado chega ao gravador. */
class AnaliseSemelhantesTest {

    @Test
    void referenciasPseudonimizadasComIdDoTemaEResultadoVaiParaOGravador() {
        var vendedor = new Consultor("Vendedor Teste", "v@insightcall.test", "x", "VENDEDOR");
        vendedor.setId(1L);
        var cliente = new Cliente("Cliente Sintetico", null, "Varejo", vendedor);
        cliente.setId(7L);
        var reuniao = new Reuniao(vendedor, cliente, null, LocalDateTime.of(2026, 10, 13, 9, 0),
                "Reuniao", 30, StatusReuniao.REALIZADA);
        var transcricao = new Transcricao(reuniao, "[LOCUTOR 1] Bom dia.\n[LOCUTOR 2] Bom dia.", "COLADO",
                "hash", 40, 2, 2);

        var transcricoes = mock(TranscricaoRepository.class);
        when(transcricoes.findById(anyLong())).thenReturn(Optional.of(transcricao));
        var padroes = mock(PadraoRepository.class);
        when(padroes.findByAtivoTrueOrderByNomeAsc()).thenReturn(List.of());
        var naoProcede = mock(NaoProcedeDoCliente.class);
        when(naoProcede.doCliente(7L)).thenReturn(List.of(
                new Trecho(31L, "suporte_insatisfacao", "A Cliente Sintetico reclamou do suporte.", "outro")));

        var temas = List.of(new ContratoV3.TemaResposta("suporte_insatisfacao", "Suporte lento", List.of("risco"),
                2, null, false, "Bom dia."));
        var resposta = new ContratoV3.Resposta("llm1", List.of(new ContratoV3.Tentativa("llm1", true)), 70,
                "neutro", null, "resumo", null, null, temas, null, null, null);
        AnaliseStrategy python = pedido -> resposta;

        var similares = mock(ClienteSimilares.class);
        var esperadas = List.of(new ClienteSimilares.Referencia("31", "A [EMPRESA_1] reclamou do suporte."));
        when(similares.maisParecidos(temas, esperadas)).thenReturn(Map.of("suporte_insatisfacao", 31L));
        var gravador = mock(GravadorAnalise.class);
        when(gravador.gravar(any(), any(), any(), anyLong(), any())).thenReturn(new GravadorAnalise.Gravado(1, 0, 0));

        var service = new AnaliseService(transcricoes, padroes, python, gravador, naoProcede, similares);
        var analisado = service.analisar(10L, vendedor);

        assertThat(analisado.novos()).isEqualTo(1);
        verify(similares).maisParecidos(temas, esperadas);
        verify(gravador).gravar(eq(transcricao), eq(resposta), any(), anyLong(),
                eq(Map.of("suporte_insatisfacao", 31L)));
    }
}
