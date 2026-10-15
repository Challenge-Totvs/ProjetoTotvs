package com.challengetotvs.api.domain.cliente;

import com.challengetotvs.api.domain.analise.Analise;
import com.challengetotvs.api.domain.analise.AnaliseRepository;
import com.challengetotvs.api.domain.cliente.ClienteResponse.ReuniaoItem;
import com.challengetotvs.api.domain.cliente.ClienteResponse.ReuniaoResumo;
import com.challengetotvs.api.domain.compromisso.CompromissoResponse;  // E1
import com.challengetotvs.api.domain.compromisso.CompromissoService;   // E1
import com.challengetotvs.api.domain.reuniao.Reuniao;
import com.challengetotvs.api.domain.reuniao.ReuniaoRepository;
import com.challengetotvs.api.domain.reuniao.StatusReuniao;
import com.challengetotvs.api.domain.tema.*;
import com.challengetotvs.api.domain.transcricao.LeitorTurnos;
import com.challengetotvs.api.domain.transcricao.Transcricao;
import com.challengetotvs.api.domain.transcricao.TranscricaoRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ClienteDetalhador {

    private static final ZoneId FUSO = ZoneId.of("America/Sao_Paulo");

    private final MontadorTemas montadorTemas;
    private final ReuniaoRepository reuniaoRepository;
    private final TranscricaoRepository transcricaoRepository;
    private final AnaliseRepository analiseRepository;
    private final CompromissoService compromissoService;   // E1


    /** Resumo pré-carregado (motor/score) de uma reunião analisada, para listagens em lote. */
    private record ResumoAnalise(String motor, Integer score) {
    }

    public ClienteResponse montar(Cliente cliente, boolean completo) {
        var reunioes = reuniaoRepository.findByClienteIdOrderByDataHoraDesc(cliente.getId());
        return montar(cliente, completo, reunioes, null);
    }

    /**
     * Várias clientes de uma vez (listagem do gestor/consultor): busca reuniões e resumos de análise em lote
     * (uma consulta por tabela, não uma por cliente) em vez de delegar a {@link #montar(Cliente, boolean)}.
     * Evita o N+1 que a tela de Clientes sofria com o Oracle remoto da faculdade.
     */
    public List<ClienteResponse> montarLista(List<Cliente> clientes) {
        if (clientes.isEmpty()) {
            return List.of();
        }
        var clienteIds = clientes.stream().map(Cliente::getId).toList();
        var todasReunioes = reuniaoRepository.findByClienteIdInOrderByDataHoraDesc(clienteIds);
        Map<Long, List<Reuniao>> reunioesPorCliente = todasReunioes.stream()
                .collect(Collectors.groupingBy(r -> r.getCliente().getId()));
        Map<Long, ResumoAnalise> resumoPreCarregado = carregarResumoAnalise(todasReunioes);

        return clientes.stream()
                .map(c -> montar(c, false, reunioesPorCliente.getOrDefault(c.getId(), List.of()), resumoPreCarregado))
                .toList();
    }

    /** Motor/score de todas as reuniões ANALISADAs de uma vez: evita 1 consulta de transcrição + 1 de análise por reunião. */
    private Map<Long, ResumoAnalise> carregarResumoAnalise(List<Reuniao> reunioes) {
        var reuniaoIds = reunioes.stream()
                .filter(r -> r.getStatus() == StatusReuniao.ANALISADA)
                .map(Reuniao::getId)
                .toList();
        if (reuniaoIds.isEmpty()) {
            return Map.of();
        }
        var transcricoes = transcricaoRepository.findByReuniaoIdIn(reuniaoIds);
        Map<Long, Transcricao> transcricaoPorReuniao = transcricoes.stream()
                .collect(Collectors.toMap(t -> t.getReuniao().getId(), t -> t, (a, b) -> a));
        var transcricaoIds = transcricoes.stream().map(Transcricao::getId).toList();
        Map<Long, Analise> analisePorTranscricao = transcricaoIds.isEmpty()
                ? Map.of()
                : analiseRepository.findByTranscricaoIdIn(transcricaoIds).stream()
                        .collect(Collectors.toMap(a -> a.getTranscricao().getId(), a -> a, (a, b) -> a));

        Map<Long, ResumoAnalise> resumos = new HashMap<>();
        for (Long reuniaoId : reuniaoIds) {
            var transcricao = transcricaoPorReuniao.get(reuniaoId);
            var analise = transcricao == null ? null : analisePorTranscricao.get(transcricao.getId());
            if (analise != null) {
                resumos.put(reuniaoId, new ResumoAnalise(analise.getMotor().valor(), analise.getScore()));
            }
        }
        return resumos;
    }

    private ClienteResponse montar(Cliente cliente, boolean completo, List<Reuniao> reunioes,
                                    Map<Long, ResumoAnalise> resumoPreCarregado) {
        var todos = montadorTemas.doCliente(cliente.getId(), completo);

        var itens = todos.stream()
                .map(t -> new CalculadoraIndicadores.Item(
                        t.tipos().contains("risco"), t.tipos().contains("oportunidade"),
                        new ResultadoSituacao(t.situacao(), t.emPauta(), t.recorrente(), t.reunioesNaJanela(),
                                t.atencao(), t.venceEm(), t.perdidaEm(), t.ultimaAtividade())))
                .toList();
        var indicadores = CalculadoraIndicadores.calcular(itens);
        var temas = completo ? todos : todos.stream().filter(TemaResponse::emPauta).toList();

        var agora = LocalDateTime.now(FUSO);

        var ultima = reunioes.stream()
                .filter(r -> r.getStatus() != StatusReuniao.AGENDADA && !r.getDataHora().isAfter(agora))
                .findFirst();
        var ultimaAnalisada = reunioes.stream()
                .filter(r -> r.getStatus() == StatusReuniao.ANALISADA)
                .findFirst();
        var proxima = reunioes.stream()
                .filter(r -> r.getStatus() == StatusReuniao.AGENDADA && !r.getDataHora().isBefore(agora))
                .min(Comparator.comparing(Reuniao::getDataHora));

        var itensReuniao = completo
                ? reunioes.stream().sorted(Comparator.comparing(Reuniao::getDataHora)).map(this::item).toList()
                : List.<ReuniaoItem>of();

        // E1: só a página de detalhe mostra os compromissos; a listagem de clientes segue sem eles
        List<CompromissoResponse> compromissos = completo
                ? compromissoService.doCliente(cliente.getId())
                : List.of();

        return ClienteResponse.from(cliente, indicadores,
                ultima.map(r -> resumo(r, resumoPreCarregado)).orElse(null),
                ultimaAnalisada.map(r -> resumo(r, resumoPreCarregado)).orElse(null),
                proxima.map(r -> resumo(r, resumoPreCarregado)).orElse(null),
                temas, itensReuniao, compromissos);
    }

    private ReuniaoResumo resumo(Reuniao r, Map<Long, ResumoAnalise> resumoPreCarregado) {
        String motor = null;
        Integer score = null;
        if (r.getStatus() == StatusReuniao.ANALISADA) {
            if (resumoPreCarregado != null) {
                var pre = resumoPreCarregado.get(r.getId());
                motor = pre == null ? null : pre.motor();
                score = pre == null ? null : pre.score();
            } else {
                var analise = transcricaoRepository.findByReuniaoId(r.getId())
                        .flatMap(t -> analiseRepository.findByTranscricaoId(t.getId()));
                motor = analise.map(a -> a.getMotor().valor()).orElse(null);
                score = analise.map(a -> a.getScore()).orElse(null);
            }
        }
        return new ReuniaoResumo(r.getId(), r.getTitulo(), r.getDataHora(), r.getDuracaoMin(), r.getStatus(),
                r.foiConfirmada(), r.getContato() == null ? null : r.getContato().getNome(), motor, score);
    }

    private ReuniaoItem item(Reuniao r) {
        var transcricao = transcricaoRepository.findByReuniaoId(r.getId());
        var analise = transcricao.flatMap(t -> analiseRepository.findByTranscricaoId(t.getId()));
        Integer turnos = transcricao.map(t -> LeitorTurnos.ler(t.getConteudo()).size()).orElse(null);
        return new ReuniaoItem(
                r.getId(), r.getTitulo(), r.getDataHora(), r.getStatus(), r.foiConfirmada(),
                r.getContato() == null ? null : r.getContato().getNome(),
                analise.map(a -> a.getMotor().valor()).orElse(null),
                analise.map(a -> a.getScore()).orElse(null),
                turnos);
    }
}