package com.challengetotvs.api.domain.inicio.semanal;

import com.challengetotvs.api.domain.consultor.Consultor;
import com.challengetotvs.api.domain.inicio.semanal.InicioSemanalResponse.PontoSemanalResponse;
import com.challengetotvs.api.domain.reuniao.StatusReuniao;
import lombok.RequiredArgsConstructor;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDate;
import java.time.ZoneId;
import java.util.List;

/**
 * Serviço novo e separado de {@code InicioService}: não lê {@code MontadorTemas} nem participa
 * do hot-path de {@code /api/inicio}.
 */
@Service
@RequiredArgsConstructor
@Transactional(readOnly = true)
public class InicioSemanalService {

    private static final ZoneId FUSO = ZoneId.of("America/Sao_Paulo");
    private static final List<StatusReuniao> STATUS_CONTAM = List.of(StatusReuniao.REALIZADA, StatusReuniao.ANALISADA);

    private final InicioSemanalRepository repository;

    @Value("${insightcall.janela-dias:30}")
    private int janelaPadrao;

    public InicioSemanalResponse montar(Consultor vendedor, Integer janelaDiasPedida) {
        int janela = janelaDiasPedida != null ? janelaDiasPedida : janelaPadrao;
        LocalDate hoje = LocalDate.now(FUSO);
        LocalDate inicioJanela = hoje.minusDays(janela);

        var linhas = repository.buscarDesde(vendedor.getId(), STATUS_CONTAM, inicioJanela.atStartOfDay());
        var serie = CalculadoraSerieSemanal.agrupar(linhas, inicioJanela, hoje);

        var semanas = serie.stream()
                .map(p -> new PontoSemanalResponse(p.inicioSemana(), p.realizadas(), p.analisadas(), p.engajamentoMedio()))
                .toList();

        return new InicioSemanalResponse(janela, semanas);
    }
}
