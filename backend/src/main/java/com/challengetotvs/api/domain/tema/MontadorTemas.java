package com.challengetotvs.api.domain.tema;

import com.challengetotvs.api.domain.analise.AnaliseRepository;
import com.challengetotvs.api.domain.reuniao.Reuniao;
import com.challengetotvs.api.domain.tema.TemaResponse.*;
import com.challengetotvs.api.domain.transcricao.LeitorTurnos;
import com.challengetotvs.api.domain.transcricao.TranscricaoRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import tools.jackson.databind.ObjectMapper;

import java.time.LocalDate;
import java.time.ZoneId;
import java.time.temporal.ChronoUnit;
import java.util.*;

@Service
@RequiredArgsConstructor
public class MontadorTemas {

    private static final ZoneId FUSO = ZoneId.of("America/Sao_Paulo");

    private final TemaRepository temaRepository;
    private final CitacaoRepository citacaoRepository;
    private final EventoTemaRepository eventoTemaRepository;
    private final TranscricaoRepository transcricaoRepository;
    private final AnaliseRepository analiseRepository;
    private final ObjectMapper objectMapper;

    @Value("${insightcall.janela-dias:30}")
    private int janela;

    private record DadosReuniao(List<LeitorTurnos.Turno> turnos, Map<Integer, String> papeis) {
    }

    public List<TemaResponse> doCliente(Long clienteId, boolean comContexto) {
        LocalDate hoje = LocalDate.now(FUSO);
        Map<Long, DadosReuniao> cache = new HashMap<>();
        List<TemaResponse> saida = new ArrayList<>();

        for (Tema tema : temaRepository.findByClienteId(clienteId)) {
            var citacoes = new ArrayList<>(citacaoRepository.findByTemaIdOrderByReuniaoDataHoraAsc(tema.getId()));
            if (citacoes.isEmpty()) {
                continue;
            }
            citacoes.sort(Comparator.comparing((Citacao c) -> c.getReuniao().getDataHora())
                    .thenComparingInt(Citacao::getTurno));

            var fora = eventoTemaRepository.findFirstByTemaIdAndTipoAndDesfeitoEmIsNullOrderByCriadoEmDesc(
                    tema.getId(), TipoEvento.TRATADO_FORA);
            var naoProcede = eventoTemaRepository.findFirstByTemaIdAndTipoAndDesfeitoEmIsNullOrderByCriadoEmDesc(
                    tema.getId(), TipoEvento.NAO_PROCEDE);

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

            saida.add(new TemaResponse(
                    tema.getId(), clienteId,
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
                    null,
                    tema.getAnterior() == null ? null : tema.getAnterior().getId(),
                    List.of()));
        }
        saida.sort(TemaResponse.ORDEM);
        return saida;
    }

    private CitacaoResponse paraResposta(Citacao c, boolean comContexto, Map<Long, DadosReuniao> cache) {
        Reuniao reuniao = c.getReuniao();
        DadosReuniao dados = dados(reuniao, cache);

        Integer locutor = dados.turnos().stream().filter(t -> t.n() == c.getTurno())
                .map(LeitorTurnos.Turno::locutor).findFirst().orElse(null);
        String papel = locutor == null ? null : dados.papeis().get(locutor);

        List<Contexto> contexto = List.of();
        if (comContexto) {
            int de = c.getTurno() - 2;
            int ate = (c.getTurnoFim() == null ? c.getTurno() : c.getTurnoFim()) + 2;
            contexto = dados.turnos().stream()
                    .filter(t -> t.n() >= de && t.n() <= ate)
                    .filter(t -> t.n() < c.getTurno()
                            || t.n() > (c.getTurnoFim() == null ? c.getTurno() : c.getTurnoFim()))
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
                    .map(a -> lerPapeis(a.getPapeis()))
                    .orElse(Map.of());
            return new DadosReuniao(turnos, papeis);
        });
    }

    private Map<Integer, String> lerPapeis(String json) {
        if (json == null || json.isBlank()) {
            return Map.of();
        }
        try {
            Map<?, ?> bruto = objectMapper.readValue(json, Map.class);
            Map<Integer, String> papeis = new HashMap<>();
            bruto.forEach((chave, valor) -> {
                if (valor != null) {
                    papeis.put(Integer.parseInt(chave.toString()), valor.toString());
                }
            });
            return papeis;
        } catch (RuntimeException e) {
            return Map.of();
        }
    }
}