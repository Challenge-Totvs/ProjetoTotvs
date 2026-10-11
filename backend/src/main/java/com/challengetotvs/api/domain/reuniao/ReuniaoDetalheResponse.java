package com.challengetotvs.api.domain.reuniao;

import com.challengetotvs.api.domain.analise.ContratoV3;
import com.challengetotvs.api.domain.tema.TemaResponse;
import com.challengetotvs.api.domain.transcricao.MetricasConversa;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

public record ReuniaoDetalheResponse(
        Long id,
        Long clienteId,
        String cliente,
        String titulo,
        LocalDateTime dataHora,
        Integer duracaoMin,
        StatusReuniao status,
        boolean confirmada,
        String contato,
        VendedorRef vendedor,
        int totalTurnos,
        AnaliseDetalhe analise,
        List<TemaResponse> temasCitados,
        List<Object> compromissos,
        MetricasConversa.Metricas metricas,
        List<TurnoResponse> turnos) {

    public record VendedorRef(Long id, String nome) {
    }

    public record AnaliseDetalhe(
            String motor,
            List<ContratoV3.Tentativa> tentativas,
            Integer score,
            String sentimento,
            String resumo,
            Map<Integer, String> papeis,
            List<ContratoV3.Interesse> interesse,
            List<String> proximosPassos,
            List<double[]> sentimentoSerie,
            List<ContratoV3.Descartado> descartados,
            LocalDateTime criadoEm) {
    }

    public record TurnoResponse(int n, int locutor, String papel, String texto) {
    }
}