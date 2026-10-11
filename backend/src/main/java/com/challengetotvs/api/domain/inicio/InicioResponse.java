package com.challengetotvs.api.domain.inicio;

import com.challengetotvs.api.domain.tema.DetectorMudancas.Mudanca;
import com.challengetotvs.api.domain.tema.TemaResponse;

import java.time.LocalDate;
import java.time.OffsetDateTime;
import java.util.List;

public record InicioResponse(
        int janelaDias,
        int totalClientes,
        List<Pendente> pendentes,
        List<TemaResponse> riscos,
        List<TemaResponse> oportunidades,
        List<Mudanca> mudancas,
        List<Object> compromissos,
        List<AgendaItem> agenda,
        Desempenho desempenho) {

    public record Pendente(Long reuniaoId, Long clienteId, String clienteNome, String titulo, LocalDate data) {
    }

    public record AgendaItem(Long reuniaoId, Long clienteId, String clienteNome, String titulo,
                             String contato, OffsetDateTime dataHora, boolean confirmada) {
    }

    public record Desempenho(
            int realizadas,
            int analisadas,
            int temasCitados,
            Double taxaConversa,
            int tratadosFora,
            int oportTratadas,
            int oportIdentificadas,
            Double falaVendedor,
            int riscosSemRetorno,
            int oportPerdidas,
            int compromissosVencidos,
            int clientes) {
    }
}