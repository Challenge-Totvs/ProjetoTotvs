package com.challengetotvs.api.domain.reuniao;

import com.challengetotvs.api.domain.analise.AnaliseRepository;
import com.challengetotvs.api.domain.analise.ContratoV3;
import com.challengetotvs.api.domain.analise.LeitorAnalise;
import com.challengetotvs.api.domain.analise.Pseudonimizador;
import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.reuniao.ReuniaoDetalheResponse.AnaliseDetalhe;
import com.challengetotvs.api.domain.reuniao.ReuniaoDetalheResponse.TurnoResponse;
import com.challengetotvs.api.domain.reuniao.ReuniaoDetalheResponse.VendedorRef;
import com.challengetotvs.api.domain.tema.MontadorTemas;
import com.challengetotvs.api.domain.transcricao.LeitorTurnos;
import com.challengetotvs.api.domain.transcricao.MetricasConversa;
import com.challengetotvs.api.domain.transcricao.TranscricaoRepository;
import com.challengetotvs.api.exception.ApiException;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import com.challengetotvs.api.domain.reuniao.ReuniaoDetalheResponse.ClienteRef;
import com.challengetotvs.api.domain.reuniao.ReuniaoDetalheResponse.TemaNaReuniao;
import com.challengetotvs.api.domain.reuniao.ReuniaoDetalheResponse.MetricasResponse;
import java.util.Comparator;
import java.util.Optional;

import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class ReuniaoDetalhador {

    private final ReuniaoRepository reuniaoRepository;
    private final TranscricaoRepository transcricaoRepository;
    private final AnaliseRepository analiseRepository;
    private final MontadorTemas montadorTemas;
    private final LeitorAnalise leitor;

    public ReuniaoDetalheResponse montar(Long id, Consultor usuario) {
        var reuniao = buscar(id, usuario);

        var transcricao = transcricaoRepository.findByReuniaoId(id);
        var turnosLidos = transcricao.map(t -> LeitorTurnos.ler(t.getConteudo())).orElse(List.of());
        var analise = transcricao.flatMap(t -> analiseRepository.findByTranscricaoId(t.getId()));
        Map<Integer, String> papeis = analise.map(a -> leitor.papeis(a.getPapeis())).orElse(Map.of());

        var temasNaReuniao = montadorTemas.doCliente(reuniao.getCliente().getId(), false).stream()
                .filter(t -> t.naoProcede() == null)
                .map(t -> t.citacoes().stream()
                        .filter(c -> c.reuniaoId().equals(id))
                        .findFirst()
                        .map(c -> new TemaNaReuniao(t, c)))
                .flatMap(Optional::stream)
                .sorted(Comparator.comparingInt(x -> x.citacao().turno()))
                .toList();

        var analiseDetalhe = analise.map(a -> new AnaliseDetalhe(
                a.getMotor().valor(),
                leitor.lista(a.getTentativas(), ContratoV3.Tentativa[].class),
                a.getScore(),
                a.getSentimento() == null ? null : a.getSentimento().valor(),
                a.getResumo(),
                papeis,
                leitor.lista(a.getInteresse(), ContratoV3.Interesse[].class),
                leitor.lista(a.getProximosPassos(), String[].class),
                leitor.serie(a.getSentimentoSerie()),
                leitor.lista(a.getDescartados(), ContratoV3.Descartado[].class),
                a.getCriadoEm())).orElse(null);

        var metricas = analise
                .map(a -> MetricasResponse.de(MetricasConversa.calcular(turnosLidos, papeis, reuniao.getDuracaoMin())))
                .orElse(null);

        var cliente = reuniao.getCliente();
        var vendedor = reuniao.getConsultor();
        return new ReuniaoDetalheResponse(
                reuniao.getId(), reuniao.getTitulo(), reuniao.getDataHora(), reuniao.getDuracaoMin(),
                reuniao.getStatus(), reuniao.foiConfirmada(),
                reuniao.getContato() == null ? null : reuniao.getContato().getNome(),
                turnosLidos.size(),
                new ClienteRef(cliente.getId(), cliente.getNome(),
                        new VendedorRef(vendedor.getId(), vendedor.getNome())),
                analiseDetalhe, temasNaReuniao, List.of(), metricas,
                transcricao.isPresent());
    }

    public List<TurnoResponse> transcricao(Long id, String versao, Consultor usuario) {
        String v = versao == null ? "original" : versao;
        if (!v.equals("original") && !v.equals("llm")) {
            throw new ApiException(HttpStatus.UNPROCESSABLE_ENTITY, "versao_invalida",
                    "Use versao=original ou versao=llm.");
        }
        buscar(id, usuario);

        var transcricao = transcricaoRepository.findByReuniaoId(id)
                .orElseThrow(() -> new EntityNotFoundException("Esta reunião ainda não tem transcrição."));
        var analise = analiseRepository.findByTranscricaoId(transcricao.getId());
        Map<Integer, String> papeis = analise.map(a -> leitor.papeis(a.getPapeis())).orElse(Map.of());

        Pseudonimizador pseudonimizador = null;
        if (v.equals("llm")) {
            var a = analise.orElseThrow(() -> new ApiException(HttpStatus.CONFLICT, "sem_analise",
                    "A reunião ainda não foi analisada, então não há versão enviada à LLM."));
            pseudonimizador = Pseudonimizador.deMapa(leitor.entidades(a.getEntidades()));
        }

        final Pseudonimizador pseudo = pseudonimizador;
        return LeitorTurnos.ler(transcricao.getConteudo()).stream()
                .map(t -> new TurnoResponse(t.n(), t.locutor(), papeis.get(t.locutor()),
                        pseudo == null ? t.texto() : pseudo.pseudonimizar(t.texto())))
                .toList();
    }

    private Reuniao buscar(Long id, Consultor usuario) {
        return reuniaoRepository.findById(id)
                .filter(r -> "GESTOR".equals(usuario.getRole()) || r.pertenceA(usuario))
                .orElseThrow(() -> new EntityNotFoundException("Reunião não encontrada!"));
    }
}