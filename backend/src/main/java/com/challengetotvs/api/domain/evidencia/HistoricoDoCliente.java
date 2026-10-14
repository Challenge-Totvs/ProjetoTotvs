package com.challengetotvs.api.domain.evidencia;

import com.challengetotvs.api.domain.analise.Pseudonimizador;
import com.challengetotvs.api.domain.analise.Pseudonimizador.Entidade;
import com.challengetotvs.api.domain.analise.Pseudonimizador.Tipo;
import com.challengetotvs.api.domain.cliente.ClienteRepository;
import com.challengetotvs.api.domain.cliente.ClienteService;
import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.transcricao.LeitorTurnos;
import com.challengetotvs.api.domain.transcricao.TranscricaoRepository;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;

/**
 * Os turnos das transcrições mais recentes do cliente, já em memória: quem chama o Python não segura transação.
 * Os turnos guardam o texto original (com nomes reais); o {@link Pseudonimizador} devolvido cobre o cliente, os
 * contatos e os consultores das reuniões carregadas, e quem envia ao Python pseudonimiza antes.
 */
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class HistoricoDoCliente {

    static final int MAXIMO_TRANSCRICOES = 20;
    static final int MAXIMO_TURNOS = ClienteEvidencias.MAXIMO_TRECHOS;

    private final ClienteRepository clienteRepository;
    private final ClienteService clienteService;
    private final TranscricaoRepository transcricaoRepository;

    public record Turno(String id, Long reuniaoId, int turno, LocalDateTime data, String texto) {
    }

    public record Historico(List<Turno> turnos, Pseudonimizador pseudonimizador) {
    }

    /** 404 se o cliente não existe ou o usuário não pode vê-lo (mesma regra de GET /api/clientes/{id}). */
    public Historico carregar(Long clienteId, Consultor usuario) {
        var cliente = clienteRepository.findById(clienteId)
                .filter(c -> clienteService.podeVer(c, usuario))
                .orElseThrow(() -> new EntityNotFoundException("Cliente não encontrado"));

        var entidades = new ArrayList<Entidade>();
        entidades.add(new Entidade(cliente.getNome(), Tipo.EMPRESA));
        cliente.getContatos().forEach(c -> adicionarPessoa(entidades, c.getNome()));
        adicionarPessoa(entidades, usuario.getNome());

        var turnos = new ArrayList<Turno>();
        var transcricoes = transcricaoRepository.maisRecentesDoCliente(clienteId, PageRequest.of(0, MAXIMO_TRANSCRICOES));
        for (var transcricao : transcricoes) {
            var reuniao = transcricao.getReuniao();
            adicionarPessoa(entidades, reuniao.getConsultor().getNome());
            for (var turno : LeitorTurnos.ler(transcricao.getConteudo())) {
                if (turnos.size() == MAXIMO_TURNOS) {
                    break;
                }
                turnos.add(new Turno(reuniao.getId() + ":" + turno.n(), reuniao.getId(), turno.n(), reuniao.getDataHora(),
                        turno.texto()));
            }
        }
        return new Historico(turnos, new Pseudonimizador(entidades));
    }

    // mesma regra do AnaliseService: nome completo e primeiro nome (se tiver 3+ letras e for diferente)
    private static void adicionarPessoa(List<Entidade> lista, String nome) {
        if (nome == null || nome.isBlank()) {
            return;
        }
        String completo = nome.strip();
        lista.add(new Entidade(completo, Tipo.PESSOA));
        String primeiro = completo.split("\\s+")[0];
        if (!primeiro.equals(completo) && primeiro.length() >= 3) {
            lista.add(new Entidade(primeiro, Tipo.PESSOA));
        }
    }
}
