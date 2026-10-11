package com.challengetotvs.api.domain.inicio;

import com.challengetotvs.api.domain.analise.AnaliseRepository;
import com.challengetotvs.api.domain.analise.LeitorAnalise;
import com.challengetotvs.api.domain.cliente.ClienteRepository;
import com.challengetotvs.api.domain.compromisso.CompromissoService;
import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.inicio.InicioResponse.AgendaItem;
import com.challengetotvs.api.domain.inicio.InicioResponse.Desempenho;
import com.challengetotvs.api.domain.inicio.InicioResponse.Pendente;
import com.challengetotvs.api.domain.reuniao.Reuniao;
import com.challengetotvs.api.domain.reuniao.ReuniaoRepository;
import com.challengetotvs.api.domain.reuniao.StatusReuniao;
import com.challengetotvs.api.domain.tema.*;
import com.challengetotvs.api.domain.transcricao.LeitorTurnos;
import com.challengetotvs.api.domain.transcricao.MetricasConversa;
import com.challengetotvs.api.domain.transcricao.TranscricaoRepository;
import com.challengetotvs.api.domain.inicio.InicioResponse.MudancaResponse;
import com.challengetotvs.api.domain.inicio.InicioResponse.VendedorRef;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.ZoneId;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class InicioService {

    private static final ZoneId FUSO = ZoneId.of("America/Sao_Paulo");
    private static final int DIAS_AGENDA = 14;

    private final ClienteRepository clienteRepository;
    private final ReuniaoRepository reuniaoRepository;
    private final TranscricaoRepository transcricaoRepository;
    private final AnaliseRepository analiseRepository;
    private final MontadorTemas montadorTemas;
    private final LeitorAnalise leitorAnalise;
    private final CompromissoService compromissoService; // E1

    @Value("${insightcall.janela-dias:30}")
    private int janela;

    public InicioResponse montar(Consultor vendedor) {
        LocalDate hoje = LocalDate.now(FUSO);

        var clientes = clienteRepository.findByVendedorOrderByNomeAsc(vendedor);
        List<TemaResponse> temas = new ArrayList<>();
        for (var cliente : clientes) {
            temas.addAll(montadorTemas.doCliente(cliente.getId(), false));
        }

        var reunioes = reuniaoRepository.findByClienteVendedorIdOrderByDataHoraAsc(vendedor.getId());

        var pendentes = reunioes.stream()
                .filter(r -> r.getStatus() == StatusReuniao.REALIZADA)
                .sorted(Comparator.comparing(Reuniao::getDataHora).reversed())
                .map(r -> new Pendente(r.getId(), r.getCliente().getId(), r.getCliente().getNome(),
                        r.getTitulo(), r.getDataHora()))
                .toList();

        var agenda = reunioes.stream()
                .filter(r -> r.getStatus() == StatusReuniao.AGENDADA)
                .filter(r -> {
                    long dias = ChronoUnit.DAYS.between(hoje, r.getDataHora().toLocalDate());
                    return dias >= 0 && dias <= DIAS_AGENDA;
                })
                .map(r -> new AgendaItem(r.getId(), r.getCliente().getId(), r.getCliente().getNome(), r.getTitulo(),
                        r.getContato() == null ? null : r.getContato().getNome(),
                        r.getDataHora().atZone(FUSO).toOffsetDateTime(),        // "2026-10-10T10:00:00-03:00"
                        r.foiConfirmada()))
                .toList();

        var naJanela = reunioes.stream()
                .filter(r -> r.getStatus() != StatusReuniao.AGENDADA)
                .filter(r -> {
                    long dias = ChronoUnit.DAYS.between(r.getDataHora().toLocalDate(), hoje);
                    return dias >= 0 && dias <= janela;
                })
                .toList();
        var analisadas = naJanela.stream().filter(r -> r.getStatus() == StatusReuniao.ANALISADA).toList();

        var compromissos = compromissoService.doInicio(vendedor.getId(), hoje); // E1: lista ordenada + vencidos

        var resumo = CalculadoraDesempenho.calcular(temas, janela, hoje);
        var desempenho = new Desempenho(
                naJanela.size(), analisadas.size(),
                resumo.temasCitados(), resumo.taxaConversa(),
                resumo.tratadosConversa(), resumo.comLeitura(),
                resumo.tratadosFora(),
                resumo.oportTratadas(), resumo.oportIdentificadas(),
                mediaFalaDoVendedor(analisadas),
                resumo.riscosSemRetorno(), resumo.oportPerdidas(),
                compromissos.vencidos(), clientes.size());                       // E1: era 0

        return new InicioResponse(
                janela, new VendedorRef(vendedor.getId(), vendedor.getNome()), clientes.size(), pendentes,
                ListasInicio.riscos(temas), ListasInicio.oportunidades(temas),
                mudancas(DetectorMudancas.detectar(temas, hoje), temas),
                compromissos.lista(), agenda, desempenho);                       // E1: era List.of()
    }


    private Double mediaFalaDoVendedor(List<Reuniao> analisadas) {
        double soma = 0;
        int contadas = 0;
        for (Reuniao reuniao : analisadas) {
            var transcricao = transcricaoRepository.findByReuniaoId(reuniao.getId());
            if (transcricao.isEmpty()) continue;
            var analise = analiseRepository.findByTranscricaoId(transcricao.get().getId());
            if (analise.isEmpty()) continue;
            var papeis = leitorAnalise.papeis(analise.get().getPapeis());
            if (papeis.isEmpty()) continue;

            var metricas = MetricasConversa.calcular(
                    LeitorTurnos.ler(transcricao.get().getConteudo()), papeis, reuniao.getDuracaoMin());
            if (metricas.falaVendedor() != null) {
                soma += metricas.falaVendedor();
                contadas++;
            }
        }
        return contadas == 0 ? null : soma / contadas;
    }

    private static final Map<String, String> TIPO_NO_FRONT = Map.of(
            "tratado_conversa", "tratado",
            "citado_de_novo_sem_resposta", "de_novo_sem_resposta",
            "voltou_a_aparecer", "voltou",
            "virou_oportunidade_perdida", "virou_perdida",
            "citado_sem_leitura", "sem_leitura");

    private List<MudancaResponse> mudancas(List<DetectorMudancas.Mudanca> eventos, List<TemaResponse> temas) {
        Map<Long, TemaResponse> porId = temas.stream().collect(Collectors.toMap(TemaResponse::id, t -> t));
        return eventos.stream()
                .map(e -> new MudancaResponse(
                        e.tipo() + "-" + e.temaId() + "-" + e.data(),
                        TIPO_NO_FRONT.getOrDefault(e.tipo(), e.tipo()),
                        e.data(), porId.get(e.temaId())))
                .toList();
    }

}