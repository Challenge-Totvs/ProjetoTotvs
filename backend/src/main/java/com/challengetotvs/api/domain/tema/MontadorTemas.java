package com.challengetotvs.api.domain.tema;

import com.challengetotvs.api.domain.analise.Analise;
import com.challengetotvs.api.domain.analise.AnaliseRepository;
import com.challengetotvs.api.domain.analise.LeitorAnalise;
import com.challengetotvs.api.domain.reuniao.Reuniao;
import com.challengetotvs.api.domain.tema.TemaResponse.*;
import com.challengetotvs.api.domain.transcricao.LeitorTurnos;
import com.challengetotvs.api.domain.transcricao.Transcricao;
import com.challengetotvs.api.domain.transcricao.TranscricaoRepository;
import jakarta.persistence.EntityNotFoundException;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.ZoneId;
import java.time.temporal.ChronoUnit;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class MontadorTemas {

    private static final ZoneId FUSO = ZoneId.of("America/Sao_Paulo");

    private final TemaRepository temaRepository;
    private final CitacaoRepository citacaoRepository;
    private final EventoTemaRepository eventoTemaRepository;
    private final TranscricaoRepository transcricaoRepository;
    private final AnaliseRepository analiseRepository;
    private final LeitorAnalise leitorAnalise;
    private final NaoProcedeDoCliente naoProcedeDoCliente;

    @Value("${insightcall.janela-dias:30}")
    private int janela;

    private record DadosReuniao(List<LeitorTurnos.Turno> turnos, Map<Integer, String> papeis) {
    }

    public List<TemaResponse> doCliente(Long clienteId, boolean comContexto) {
        LocalDate hoje = LocalDate.now(FUSO);
        List<Tema> temas = temaRepository.findByClienteId(clienteId);
        if (temas.isEmpty()) {
            return List.of();
        }

        // Tudo em lote (uma consulta por tabela, não uma por tema): essencial com o Oracle remoto da faculdade.
        Map<Long, List<Citacao>> citacoesPorTema = citacaoRepository.findByTemaClienteIdOrderByReuniaoDataHoraAsc(clienteId)
                .stream().collect(Collectors.groupingBy(c -> c.getTema().getId()));
        Map<Long, EventoTema> foraPorTema = vigentePorTema(eventoTemaRepository
                .findByTemaClienteIdAndTipoAndDesfeitoEmIsNullOrderByCriadoEmDesc(clienteId, TipoEvento.TRATADO_FORA));
        Map<Long, EventoTema> naoProcedePorTema = vigentePorTema(eventoTemaRepository
                .findByTemaClienteIdAndTipoAndDesfeitoEmIsNullOrderByCriadoEmDesc(clienteId, TipoEvento.NAO_PROCEDE));

        Set<Long> reuniaoIds = citacoesPorTema.values().stream().flatMap(List::stream)
                .map(c -> c.getReuniao().getId()).collect(Collectors.toSet());
        Map<Long, DadosReuniao> cache = carregarDados(reuniaoIds);

        List<TemaResponse> saida = new ArrayList<>();
        for (Tema tema : temas) {
            var citacoes = new ArrayList<>(citacoesPorTema.getOrDefault(tema.getId(), List.of()));
            TemaResponse resposta = montar(tema, hoje, comContexto, citacoes,
                    Optional.ofNullable(foraPorTema.get(tema.getId())),
                    Optional.ofNullable(naoProcedePorTema.get(tema.getId())),
                    cache);
            if (resposta != null) {
                saida.add(resposta);
            }
        }
        saida.sort(TemaResponse.ORDEM);
        return saida;
    }

    public TemaResponse doTema(Long temaId, boolean comContexto) {
        Tema tema = temaRepository.findById(temaId)
                .orElseThrow(() -> new EntityNotFoundException("Tema não encontrado!"));
        var citacoes = new ArrayList<>(citacaoRepository.findByTemaIdOrderByReuniaoDataHoraAsc(tema.getId()));
        var fora = eventoTemaRepository.findFirstByTemaIdAndTipoAndDesfeitoEmIsNullOrderByCriadoEmDesc(
                tema.getId(), TipoEvento.TRATADO_FORA);
        var naoProcede = eventoTemaRepository.findFirstByTemaIdAndTipoAndDesfeitoEmIsNullOrderByCriadoEmDesc(
                tema.getId(), TipoEvento.NAO_PROCEDE);
        TemaResponse resposta = montar(tema, LocalDate.now(FUSO), comContexto, citacoes, fora, naoProcede, new HashMap<>());
        if (resposta == null) {
            throw new EntityNotFoundException("Tema sem citações!");
        }
        return resposta;
    }

    /** Entre vários eventos vigentes (um tipo, vários temas, do mais novo ao mais antigo), fica o primeiro de cada tema. */
    private Map<Long, EventoTema> vigentePorTema(List<EventoTema> vigentesDoMaisNovoAoMaisAntigo) {
        Map<Long, EventoTema> porTema = new LinkedHashMap<>();
        for (EventoTema e : vigentesDoMaisNovoAoMaisAntigo) {
            porTema.putIfAbsent(e.getTema().getId(), e);
        }
        return porTema;
    }

    /** Turnos e papéis de várias reuniões de uma vez, para citações de clientes diferentes não repetirem consulta. */
    private Map<Long, DadosReuniao> carregarDados(Set<Long> reuniaoIds) {
        Map<Long, DadosReuniao> cache = new HashMap<>();
        if (reuniaoIds.isEmpty()) {
            return cache;
        }
        var transcricoes = transcricaoRepository.findByReuniaoIdIn(reuniaoIds);
        Map<Long, Transcricao> transcricaoPorReuniao = transcricoes.stream()
                .collect(Collectors.toMap(t -> t.getReuniao().getId(), t -> t, (a, b) -> a));
        var transcricaoIds = transcricoes.stream().map(Transcricao::getId).toList();
        Map<Long, Analise> analisePorTranscricao = transcricaoIds.isEmpty()
                ? Map.of()
                : analiseRepository.findByTranscricaoIdIn(transcricaoIds).stream()
                        .collect(Collectors.toMap(a -> a.getTranscricao().getId(), a -> a, (a, b) -> a));

        for (Long reuniaoId : reuniaoIds) {
            Transcricao transcricao = transcricaoPorReuniao.get(reuniaoId);
            if (transcricao == null) {
                cache.put(reuniaoId, new DadosReuniao(List.of(), Map.of()));
                continue;
            }
            var turnos = LeitorTurnos.ler(transcricao.getConteudo());
            var analise = analisePorTranscricao.get(transcricao.getId());
            var papeis = analise == null ? Map.<Integer, String>of() : leitorAnalise.papeis(analise.getPapeis());
            cache.put(reuniaoId, new DadosReuniao(turnos, papeis));
        }
        return cache;
    }

    private TemaResponse montar(Tema tema, LocalDate hoje, boolean comContexto, List<Citacao> citacoes,
                                 Optional<EventoTema> fora, Optional<EventoTema> naoProcede, Map<Long, DadosReuniao> cache) {
        if (citacoes.isEmpty()) {
            return null;
        }
        citacoes.sort(Comparator.comparing((Citacao c) -> c.getReuniao().getDataHora())
                .thenComparingInt(Citacao::getTurno));

        var entradas = citacoes.stream()
                .map(c -> new CitacaoEntrada(c.getReuniao().getDataHora(), c.getReuniao().getId(),
                        c.getTurno(), c.getTratado()))
                .toList();
        LocalDate dataFora = fora.map(EventoTema::getDataAcao).orElse(null);

        ResultadoSituacao r = CalculadoraSituacao.calcular(
                entradas, tema.isOportunidade(), dataFora, naoProcede.isPresent(), janela, hoje);

        Citacao ultima = citacoes.get(citacoes.size() - 1);
        LocalDate ultimaData = ultima.getReuniao().getDataHora().toLocalDate();

        var explicacao = ExplicadorTema.explicar(new ExplicadorTema.Entrada(
                r, tema.isRisco(), tema.isOportunidade(), janela, hoje,
                ultima.getReuniao().getTitulo(), ultimaData,
                fora.map(f -> f.getPor().getNome()).orElse(null),
                fora.map(EventoTema::getAcao).orElse(null),
                fora.map(EventoTema::getCanal).orElse(null),
                dataFora,
                naoProcede.map(n -> n.getPor().getNome()).orElse(null),
                naoProcede.map(EventoTema::getMotivo).orElse(null),
                naoProcede.map(n -> n.getCriadoEm().toLocalDate()).orElse(null)));

        List<CitacaoResponse> citacoesResposta = new ArrayList<>();
        for (int i = citacoes.size() - 1; i >= 0; i--) {
            citacoesResposta.add(paraResposta(citacoes.get(i), comContexto, cache));
        }

        List<String> tipos = new ArrayList<>();
        if (tema.isRisco()) tipos.add("risco");
        if (tema.isOportunidade()) tipos.add("oportunidade");

        return new TemaResponse(
                tema.getId(), tema.getCliente().getId(), tema.getCliente().getNome(),
                tema.getPadrao().getChave(), tema.getPadrao().getNome(), tema.getTitulo(), tipos,
                r.situacao(), r.emPauta(), r.atencao(), r.recorrente(), r.reunioesNaJanela(),
                ultima.getTratado() != null,
                ChronoUnit.DAYS.between(ultimaData, hoje),
                r.ultimaAtividade(), r.venceEm(), r.perdidaEm(), explicacao,
                citacoesResposta,
                fora.map(f -> new RegistroFora(f.getAcao(), f.getCanal(), f.getDataAcao(),
                        f.getObservacao(), f.getPor().getNome())).orElse(null),
                naoProcede.map(n -> new NaoProcede(n.getMotivo(), n.getPor().getNome(),
                        n.getCriadoEm().toLocalDate())).orElse(null),
                semelhante(tema),
                tema.getAnterior() == null ? null : tema.getAnterior().getId(),
                List.of());
    }

    /** Só enquanto o tema de referência continuar "não procede": desfeita a marcação, o aviso some. */
    private SemelhanteNaoProcede semelhante(Tema tema) {
        Long id = tema.getSemelhanteNaoProcedeId();
        if (id == null) {
            return null;
        }
        return eventoTemaRepository
                .findFirstByTemaIdAndTipoAndDesfeitoEmIsNullOrderByCriadoEmDesc(id, TipoEvento.NAO_PROCEDE)
                .flatMap(naoProcedeDoCliente::trecho)
                .map(texto -> new SemelhanteNaoProcede(id, texto, tema.getCliente().getNome()))
                .orElse(null);
    }

    private CitacaoResponse paraResposta(Citacao c, boolean comContexto, Map<Long, DadosReuniao> cache) {
        Reuniao reuniao = c.getReuniao();
        DadosReuniao dados = dados(reuniao, cache);

        Integer locutor = dados.turnos().stream().filter(t -> t.n() == c.getTurno())
                .map(LeitorTurnos.Turno::locutor).findFirst().orElse(null);
        String papel = locutor == null ? null : dados.papeis().get(locutor);

        List<Contexto> contexto = List.of();
        if (comContexto) {
            int fim = c.getTurnoFim() == null ? c.getTurno() : c.getTurnoFim();
            int de = c.getTurno() - 2;
            int ate = fim + 2;
            contexto = dados.turnos().stream()
                    .filter(t -> t.n() >= de && t.n() <= ate)
                    .filter(t -> t.n() < c.getTurno() || t.n() > fim)
                    .map(t -> new Contexto(t.n(), t.locutor(), dados.papeis().get(t.locutor()), t.texto()))
                    .toList();
        }
        return new CitacaoResponse(reuniao.getId(), reuniao.getTitulo(), reuniao.getDataHora().toLocalDate(),
                c.getTurno(), c.getTratado(), c.getTexto(), locutor, papel, contexto);
    }

    private DadosReuniao dados(Reuniao reuniao, Map<Long, DadosReuniao> cache) {
        return cache.computeIfAbsent(reuniao.getId(), id -> {
            var transcricao = transcricaoRepository.findByReuniaoId(id);
            if (transcricao.isEmpty()) {
                return new DadosReuniao(List.of(), Map.of());
            }
            var turnos = LeitorTurnos.ler(transcricao.get().getConteudo());
            var papeis = analiseRepository.findByTranscricaoId(transcricao.get().getId())
                    .map(a -> leitorAnalise.papeis(a.getPapeis()))
                    .orElse(Map.of());
            return new DadosReuniao(turnos, papeis);
        });
    }
}