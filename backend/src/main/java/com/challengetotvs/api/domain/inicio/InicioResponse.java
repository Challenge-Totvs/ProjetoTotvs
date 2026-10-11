package com.challengetotvs.api.domain.inicio;

import com.challengetotvs.api.domain.compromisso.CompromissoResponse;
import com.challengetotvs.api.domain.tema.TemaResponse;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.OffsetDateTime;
import java.util.List;

public record InicioResponse(
        int janelaDias,
        VendedorRef vendedor,
        int clientes,
        List<Pendente> pendentes,
        List<TemaResponse> riscos,
        List<TemaResponse> oportunidades,
        List<MudancaResponse> mudancas,
        List<CompromissoResponse> compromissos,
        List<AgendaItem> agenda,
        Desempenho desempenho) {

    public record VendedorRef(Long id, String nome) {
    }

    public record Pendente(Long reuniaoId, Long clienteId, String clienteNome, String titulo,
                           LocalDateTime dataHora) {
    }

    public record MudancaResponse(String id, String tipo, LocalDate data, TemaResponse tema) {
    }

    public record AgendaItem(Long reuniaoId, Long clienteId, String clienteNome, String titulo,
                             String contato, OffsetDateTime dataHora, boolean confirmada) {
    }

    public record Desempenho(
            int realizadas,
            int analisadas,
            int temasCitados,
            Double taxaConversa,
            int tratadosConversa,
            int comLeitura,
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