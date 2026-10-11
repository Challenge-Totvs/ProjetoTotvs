package com.challengetotvs.api.domain.cliente;

import com.challengetotvs.api.domain.analise.AnaliseRepository;
import com.challengetotvs.api.domain.cliente.ClienteResponse.ReuniaoResumo;
import com.challengetotvs.api.domain.reuniao.Reuniao;
import com.challengetotvs.api.domain.reuniao.ReuniaoRepository;
import com.challengetotvs.api.domain.reuniao.StatusReuniao;
import com.challengetotvs.api.domain.tema.*;
import com.challengetotvs.api.domain.transcricao.TranscricaoRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Comparator;

@Service
@RequiredArgsConstructor
public class ClienteDetalhador {

    private static final ZoneId FUSO = ZoneId.of("America/Sao_Paulo");

    private final MontadorTemas montadorTemas;
    private final ReuniaoRepository reuniaoRepository;
    private final TranscricaoRepository transcricaoRepository;
    private final AnaliseRepository analiseRepository;

    public ClienteResponse montar(Cliente cliente, boolean completo) {
        var todos = montadorTemas.doCliente(cliente.getId(), completo);

        var itens = todos.stream()
                .map(t -> new CalculadoraIndicadores.Item(
                        t.tipos().contains("risco"), t.tipos().contains("oportunidade"),
                        new ResultadoSituacao(t.situacao(), t.emPauta(), t.recorrente(), t.reunioesNaJanela(),
                                t.atencao(), t.venceEm(), t.perdidaEm(), t.ultimaAtividade())))
                .toList();
        var indicadores = CalculadoraIndicadores.calcular(itens);
        var temas = completo ? todos : todos.stream().filter(TemaResponse::emPauta).toList();

        var reunioes = reuniaoRepository.findByClienteIdOrderByDataHoraDesc(cliente.getId());
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

        return ClienteResponse.from(cliente, indicadores,
                ultima.map(this::resumo).orElse(null),
                ultimaAnalisada.map(this::resumo).orElse(null),
                proxima.map(this::resumo).orElse(null),
                temas);
    }

    private ReuniaoResumo resumo(Reuniao r) {
        String motor = null;
        Integer score = null;
        if (r.getStatus() == StatusReuniao.ANALISADA) {
            var analise = transcricaoRepository.findByReuniaoId(r.getId())
                    .flatMap(t -> analiseRepository.findByTranscricaoId(t.getId()));
            motor = analise.map(a -> a.getMotor().valor()).orElse(null);
            score = analise.map(a -> a.getScore()).orElse(null);
        }
        return new ReuniaoResumo(r.getId(), r.getTitulo(), r.getDataHora(), r.getDuracaoMin(), r.getStatus(),
                r.foiConfirmada(), r.getContato() == null ? null : r.getContato().getNome(), motor, score);
    }
}