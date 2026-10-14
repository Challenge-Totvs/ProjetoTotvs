package com.challengetotvs.api.domain.tema;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Optional;

/**
 * Os temas que o cliente marcou como "não procede" (ainda vigentes), com o trecho de cada um.
 * Vão como contraexemplos no /analisar (contrato v3 §3.1) e como referências no /similares.
 * O trecho guardado tem os nomes reais: quem envia ao Python pseudonimiza antes.
 */
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class NaoProcedeDoCliente {

    public static final int MAXIMO = 50;                 // limite de contraexemplos do contrato v3 §3.2
    private static final String MOTIVO_PADRAO = "outro"; // o Java aceita motivo vazio; o contrato, não

    private final EventoTemaRepository eventoTemaRepository;
    private final CitacaoRepository citacaoRepository;

    public record Trecho(Long temaId, String padrao, String texto, String motivo) {
    }

    public List<Trecho> doCliente(Long clienteId) {
        var vistos = new HashSet<Long>();
        var trechos = new ArrayList<Trecho>();
        var eventos = eventoTemaRepository
                .findByTemaClienteIdAndTipoAndDesfeitoEmIsNullOrderByCriadoEmDesc(clienteId, TipoEvento.NAO_PROCEDE);
        for (EventoTema evento : eventos) {
            if (trechos.size() == MAXIMO) {
                break;
            }
            Tema tema = evento.getTema();
            if (!vistos.add(tema.getId())) {
                continue;
            }
            trecho(evento).ifPresent(texto -> trechos.add(new Trecho(tema.getId(), tema.getPadrao().getChave(),
                    texto, evento.getMotivo() == null ? MOTIVO_PADRAO : evento.getMotivo())));
        }
        return trechos;
    }

    /** A citação que estava valendo quando o tema foi marcado: a última criada até a marcação (ou a última de todas). */
    public Optional<String> trecho(EventoTema evento) {
        var citacoes = citacaoRepository.findByTemaIdOrderByReuniaoDataHoraAsc(evento.getTema().getId());
        Citacao escolhida = null;
        for (Citacao c : citacoes) {
            if (escolhida == null || !c.getCriadoEm().isAfter(evento.getCriadoEm())) {
                escolhida = c;
            }
        }
        return Optional.ofNullable(escolhida)
                .map(Citacao::getTexto)
                .filter(texto -> !texto.isBlank());
    }
}
