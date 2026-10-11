package com.challengetotvs.api.domain.inicio;

import com.challengetotvs.api.domain.analise.AnaliseRepository;
import com.challengetotvs.api.domain.analise.LeitorAnalise;
import com.challengetotvs.api.domain.cliente.ClienteRepository;
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
                        r.getTitulo(), r.getDataHora().toLocalDate()))
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

        var resumo = CalculadoraDesempenho.calcular(temas, janela, hoje);
        var desempenho = new Desempenho(
                naJanela.size(), analisadas.size(),
                resumo.temasCitados(), resumo.taxaConversa(), resumo.tratadosFora(),
                resumo.oportTratadas(), resumo.oportIdentificadas(),
                mediaFalaDoVendedor(analisadas),
                resumo.riscosSemRetorno(), resumo.oportPerdidas(),
                0, clientes.size());

        return new InicioResponse(
                janela, clientes.size(), pendentes,
                ListasInicio.riscos(temas), ListasInicio.oportunidades(temas),
                DetectorMudancas.detectar(temas, hoje),
                List.of(), agenda, desempenho);
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
}