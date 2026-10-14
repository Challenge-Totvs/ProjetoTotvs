package com.challengetotvs.api.domain.evidencia;

import com.challengetotvs.api.domain.cliente.Cliente;
import com.challengetotvs.api.domain.cliente.ClienteRepository;
import com.challengetotvs.api.domain.cliente.ClienteService;
import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.reuniao.Reuniao;
import com.challengetotvs.api.domain.transcricao.Transcricao;
import com.challengetotvs.api.domain.transcricao.TranscricaoRepository;
import jakarta.persistence.EntityNotFoundException;
import org.junit.jupiter.api.Test;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.ArgumentMatchers.eq;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

class HistoricoDoClienteTest {

    private final ClienteRepository clientes = mock(ClienteRepository.class);
    private final ClienteService clienteService = mock(ClienteService.class);
    private final TranscricaoRepository transcricoes = mock(TranscricaoRepository.class);
    private final HistoricoDoCliente historico = new HistoricoDoCliente(clientes, clienteService, transcricoes);

    private final Consultor usuario = consultor(1L, "Marina Souza");
    private final Cliente cliente = new Cliente("Acme Logistica", null, "Logística", usuario);

    @Test
    void clienteSemTranscricaoTemHistoricoVazio() {
        liberar();
        when(transcricoes.maisRecentesDoCliente(eq(5L), any())).thenReturn(List.of());

        assertThat(historico.carregar(5L, usuario).turnos()).isEmpty();
    }

    @Test
    void turnosVemDaMaisRecenteComIdReuniaoNumeroEPseudonimizadorDoCadastro() {
        liberar();
        cliente.adicionarContato("Carlos Lima", "Diretor");
        var recente = transcricao(20L, LocalDateTime.of(2026, 10, 9, 10, 0),
                "[LOCUTOR 1]: Bom dia, Carlos.\n[LOCUTOR 2]: Bom dia, Marina.");
        var antiga = transcricao(10L, LocalDateTime.of(2026, 9, 1, 10, 0), "[LOCUTOR 1]: A Acme Logistica quer prazo.");
        when(transcricoes.maisRecentesDoCliente(eq(5L), any())).thenReturn(List.of(recente, antiga));

        var resultado = historico.carregar(5L, usuario);

        assertThat(resultado.turnos()).extracting(HistoricoDoCliente.Turno::id).containsExactly("20:1", "20:2", "10:1");
        assertThat(resultado.turnos().get(0).data()).isEqualTo(LocalDateTime.of(2026, 10, 9, 10, 0));
        assertThat(resultado.turnos().get(0).texto()).isEqualTo("Bom dia, Carlos.");   // o original fica intacto
        var pseudo = resultado.pseudonimizador();
        assertThat(pseudo.pseudonimizar("Carlos da Acme Logistica falou com a Marina"))
                .doesNotContain("Carlos").doesNotContain("Acme").doesNotContain("Marina");
    }

    @Test
    void respeitaOLimiteDeTurnos() {
        liberar();
        var conteudo = new StringBuilder();
        for (int i = 0; i < 600; i++) {
            conteudo.append("[LOCUTOR 1]: Turno ").append(i).append(".\n");
        }
        when(transcricoes.maisRecentesDoCliente(eq(5L), any()))
                .thenReturn(List.of(transcricao(20L, LocalDateTime.now(), conteudo.toString())));

        assertThat(historico.carregar(5L, usuario).turnos()).hasSize(HistoricoDoCliente.MAXIMO_TURNOS);
    }

    @Test
    void clienteInexistenteOuQueOUsuarioNaoVeE404SemLerTranscricao() {
        when(clientes.findById(5L)).thenReturn(Optional.of(cliente));
        when(clienteService.podeVer(cliente, usuario)).thenReturn(false);

        assertThatThrownBy(() -> historico.carregar(5L, usuario)).isInstanceOf(EntityNotFoundException.class);
        assertThatThrownBy(() -> historico.carregar(6L, usuario)).isInstanceOf(EntityNotFoundException.class);
        verify(transcricoes, never()).maisRecentesDoCliente(any(), any());
    }

    private void liberar() {
        when(clientes.findById(5L)).thenReturn(Optional.of(cliente));
        when(clienteService.podeVer(cliente, usuario)).thenReturn(true);
    }

    private Transcricao transcricao(Long reuniaoId, LocalDateTime data, String conteudo) {
        var reuniao = Reuniao.builder().consultor(usuario).cliente(cliente).dataHora(data).titulo("Reunião").build();
        reuniao.setId(reuniaoId);
        return Transcricao.builder().reuniao(reuniao).conteudo(conteudo).formatoOrigem("txt").hashTexto("h")
                .caracteres(conteudo.length()).turnos(0).locutores(2).build();
    }

    private static Consultor consultor(Long id, String nome) {
        var c = new Consultor(nome, "m@x.com", "h", "VENDEDOR");
        c.setId(id);
        return c;
    }
}
