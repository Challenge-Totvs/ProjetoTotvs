package com.challengetotvs.api.domain.tema;

import com.challengetotvs.api.domain.analise.ContratoV3;
import com.challengetotvs.api.domain.reuniao.Reuniao;
import com.challengetotvs.api.domain.tema.EscolhaDeTema.Candidato;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.ZoneId;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
public class IncorporadorTemas {

    private static final ZoneId FUSO = ZoneId.of("America/Sao_Paulo");

    private final PadraoRepository padraoRepository;
    private final TemaRepository temaRepository;
    private final CitacaoRepository citacaoRepository;
    private final EventoTemaRepository eventoTemaRepository;

    @Value("${insightcall.janela-dias:30}")
    private int janela;

    public record Resumo(int novos, int atualizados) {
    }

    public Resumo incorporar(Reuniao reuniao, ContratoV3.Resposta resposta) {
        citacaoRepository.deleteAll(citacaoRepository.findByReuniaoId(reuniao.getId()));
        citacaoRepository.flush();

        Map<String, Padrao> padroes = new HashMap<>();
        Map<String, TipoPadrao> tipoPorPadrao = new HashMap<>();
        for (Padrao p : padraoRepository.findByAtivoTrueOrderByNomeAsc()) {
            padroes.put(p.getChave(), p);
            tipoPorPadrao.put(p.getChave(), p.getTipo());
        }

        LocalDate hoje = LocalDate.now(FUSO);
        int novos = 0;
        int atualizados = 0;


        for (var consolidado : ConsolidadorTemas.consolidar(resposta.temas(), tipoPorPadrao)) {
            Long clienteId = reuniao.getCliente().getId();
            List<Tema> existentes = temaRepository
                    .findByClienteIdAndPadraoChaveOrderByCriadoEmAsc(clienteId, consolidado.padrao());

            Map<Long, Tema> porId = new HashMap<>();
            List<Candidato> candidatos = new ArrayList<>();
            for (Tema t : existentes) {
                porId.put(t.getId(), t);
                candidatos.add(paraCandidato(t));
            }

            var ativo = EscolhaDeTema.ativo(candidatos, janela, hoje);
            Tema tema;
            if (ativo.isPresent()) {
                tema = porId.get(ativo.get().id());
                tema.setRisco(tema.isRisco() || consolidado.risco());
                tema.setOportunidade(tema.isOportunidade() || consolidado.oportunidade());
                temaRepository.save(tema);
                atualizados++;
            } else {
                Tema anterior = EscolhaDeTema.anterior(candidatos)
                        .map(c -> porId.get(c.id()))
                        .orElse(null);
                tema = temaRepository.save(Tema.builder()
                        .cliente(reuniao.getCliente())
                        .padrao(padroes.get(consolidado.padrao()))
                        .titulo(titulo(consolidado.titulo(), padroes.get(consolidado.padrao())))
                        .risco(consolidado.risco())
                        .oportunidade(consolidado.oportunidade())
                        .anterior(anterior)
                        .build());
                novos++;
            }

            citacaoRepository.save(Citacao.builder()
                    .tema(tema)
                    .reuniao(reuniao)
                    .turno(consolidado.turno())
                    .turnoFim(consolidado.turnoFim())
                    .tratado(consolidado.tratado())
                    .texto(consolidado.texto())
                    .build());
        }
        return new Resumo(novos, atualizados);
    }

    private Candidato paraCandidato(Tema t) {
        var citacoes = citacaoRepository.findByTemaIdOrderByReuniaoDataHoraAsc(t.getId()).stream()
                .map(c -> new CitacaoEntrada(c.getReuniao().getDataHora(), c.getReuniao().getId(),
                        c.getTurno(), c.getTratado()))
                .toList();
        LocalDate dataFora = eventoTemaRepository
                .findFirstByTemaIdAndTipoAndDesfeitoEmIsNullOrderByCriadoEmDesc(t.getId(), TipoEvento.TRATADO_FORA)
                .map(EventoTema::getDataAcao).orElse(null);
        boolean naoProcede = eventoTemaRepository
                .findFirstByTemaIdAndTipoAndDesfeitoEmIsNullOrderByCriadoEmDesc(t.getId(), TipoEvento.NAO_PROCEDE)
                .isPresent();
        return new Candidato(t.getId(), citacoes, t.isOportunidade(), dataFora, naoProcede);
    }

    private String titulo(String daLlm, Padrao padrao) {
        String t = (daLlm == null || daLlm.isBlank()) ? padrao.getNome() : daLlm.strip();
        return t.length() > 255 ? t.substring(0, 255) : t;
    }
}