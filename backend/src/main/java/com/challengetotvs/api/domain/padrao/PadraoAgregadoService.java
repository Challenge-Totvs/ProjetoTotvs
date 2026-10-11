package com.challengetotvs.api.domain.padrao;

import com.challengetotvs.api.domain.cliente.Cliente;
import com.challengetotvs.api.domain.cliente.ClienteRepository;
import com.challengetotvs.api.domain.cliente.TipoCliente;
import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.padrao.PadraoAgregadoResponse.Amostra;
import com.challengetotvs.api.domain.padrao.PadraoAgregadoResponse.ClienteRef;
import com.challengetotvs.api.domain.tema.MontadorTemas;
import com.challengetotvs.api.domain.tema.Padrao;
import com.challengetotvs.api.domain.tema.PadraoRepository;
import com.challengetotvs.api.domain.tema.Situacao;
import com.challengetotvs.api.domain.tema.TemaResponse;
import com.challengetotvs.api.domain.transcricao.LeitorTurnos;
import com.challengetotvs.api.domain.transcricao.TranscricaoRepository;
import com.challengetotvs.api.security.Perfis;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class PadraoAgregadoService {

    private final ClienteRepository clienteRepository;
    private final PadraoRepository padraoRepository;
    private final MontadorTemas montadorTemas;
    private final TranscricaoRepository transcricaoRepository;

    private record TemaDoCliente(TemaResponse tema, Cliente cliente) {
    }

    private record CitacaoDoTema(TemaDoCliente item, TemaResponse.CitacaoResponse citacao) {
    }


    public List<PadraoAgregadoResponse> agregar(String tipoCliente, String tipo, Consultor usuario) {
        Perfis.exigirGestor(usuario);

        var clientes = clienteRepository.findByVendedorIsNotNullOrderByNomeAsc().stream()
                .filter(c -> aceitaTipoCliente(c, tipoCliente))
                .toList();

        Map<String, List<TemaDoCliente>> porPadrao = new HashMap<>();
        for (var cliente : clientes) {
            for (var tema : montadorTemas.doCliente(cliente.getId(), false)) {
                porPadrao.computeIfAbsent(tema.padrao(), k -> new ArrayList<>())
                        .add(new TemaDoCliente(tema, cliente));
            }
        }

        Map<Long, Integer> cacheTurnos = new HashMap<>();
        List<PadraoAgregadoResponse> saida = new ArrayList<>();
        for (var padrao : padraoRepository.findByAtivoTrueOrderByNomeAsc()) {
            if (!"todos".equals(tipo) && !padrao.getTipo().valor().equals(tipo)) {
                continue;
            }
            var itens = porPadrao.get(padrao.getChave());
            if (itens == null || itens.isEmpty()) {
                continue;
            }
            saida.add(calcular(padrao, itens, cacheTurnos));
        }

        saida.sort(Comparator
                .comparingInt((PadraoAgregadoResponse p) -> p.semRetorno() + p.perdidas() + p.recorrentes())
                .reversed()
                .thenComparing(Comparator.comparingInt(PadraoAgregadoResponse::total).reversed())
                .thenComparing(PadraoAgregadoResponse::nome));
        return saida;
    }

    private PadraoAgregadoResponse calcular(Padrao padrao, List<TemaDoCliente> itens,
                                            Map<Long, Integer> cacheTurnos) {
        int total = itens.size();
        var validos = itens.stream().filter(i -> i.tema().naoProcede() == null).toList();
        int naoProcede = total - validos.size();

        Map<String, Integer> motivos = new HashMap<>();
        for (var i : itens) {
            var np = i.tema().naoProcede();
            if (np != null) {
                motivos.merge(np.motivo() == null ? "sem_motivo" : np.motivo(), 1, Integer::sum);
            }
        }

        int semRetorno = 0, perdidas = 0, recorrentes = 0, comLeitura = 0, respondidos = 0;
        Map<String, Integer> porVendedor = new HashMap<>();
        Map<String, Integer> porSegmento = new HashMap<>();
        int[] terco = new int[3];
        List<CitacaoDoTema> todasCitacoes = new ArrayList<>();

        for (var item : validos) {
            var tema = item.tema();
            if (tema.situacao() == Situacao.SEM_RETORNO) semRetorno++;
            if (tema.situacao() == Situacao.OPORTUNIDADE_PERDIDA) perdidas++;
            if (tema.recorrente()) recorrentes++;

            var ultima = tema.citacoes().get(0);
            if (ultima.tratado() != null) {
                comLeitura++;
                if (Boolean.TRUE.equals(ultima.tratado())) respondidos++;
            }

            porVendedor.merge(item.cliente().getVendedor().getNome(), 1, Integer::sum);
            porSegmento.merge(item.cliente().getSegmento(), 1, Integer::sum);

            for (var cit : tema.citacoes()) {
                todasCitacoes.add(new CitacaoDoTema(item, cit));
                int turnos = turnosDaReuniao(cit.reuniaoId(), cacheTurnos);
                if (turnos <= 0) continue;
                double pos = (cit.turno() - 0.5) / turnos;
                terco[pos < 1.0 / 3 ? 0 : pos < 2.0 / 3 ? 1 : 2]++;
            }
        }

        Double taxaConversa = comLeitura == 0 ? null : (double) respondidos / comLeitura;
        int clientesDistintos = (int) validos.stream().map(i -> i.cliente().getId()).distinct().count();

        todasCitacoes.sort(Comparator
                .comparing((CitacaoDoTema x) -> x.citacao().reuniaoData())
                .thenComparingInt(x -> x.citacao().turno())
                .reversed());
        List<Amostra> amostra = todasCitacoes.stream().limit(3).map(this::amostra).toList();

        return new PadraoAgregadoResponse(
                padrao.getChave(), padrao.getNome(), padrao.getTipo().valor(),
                total, naoProcede, (double) naoProcede / total,
                clientesDistintos, semRetorno, perdidas, recorrentes, taxaConversa,
                List.of(terco[0], terco[1], terco[2]),
                ordenar(porVendedor), ordenar(porSegmento), ordenar(motivos),
                amostra);
    }

    private Amostra amostra(CitacaoDoTema x) {
        var c = x.citacao();
        var cliente = x.item().cliente();
        return new Amostra(
                c.reuniaoId(), c.reuniaoTitulo(), c.reuniaoData(), c.turno(), c.tratado(), c.texto(),
                true, c.locutor(), c.papel(), null,
                x.item().tema().id(),
                new ClienteRef(cliente.getId(), cliente.getNome()),
                cliente.getVendedor().getNome());
    }

    private int turnosDaReuniao(Long reuniaoId, Map<Long, Integer> cache) {
        return cache.computeIfAbsent(reuniaoId, id -> transcricaoRepository.findByReuniaoId(id)
                .map(t -> LeitorTurnos.ler(t.getConteudo()).stream()
                        .mapToInt(LeitorTurnos.Turno::n).max().orElse(0))
                .orElse(0));
    }

    private static List<List<Object>> ordenar(Map<String, Integer> contagem) {
        return contagem.entrySet().stream()
                .sorted((a, b) -> {
                    int porQuantidade = Integer.compare(b.getValue(), a.getValue());
                    return porQuantidade != 0 ? porQuantidade : a.getKey().compareTo(b.getKey());
                })
                .map(e -> List.<Object>of(e.getKey(), e.getValue()))
                .toList();
    }

    private static boolean aceitaTipoCliente(Cliente cliente, String filtro) {
        return switch (filtro == null ? "todos" : filtro) {
            case "ativo" -> cliente.getTipo() == TipoCliente.ATIVO;
            case "prospect" -> cliente.getTipo() == TipoCliente.PROSPECT;
            case "sem" -> cliente.getTipo() == null;
            default -> true;
        };
    }
}