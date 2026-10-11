package com.challengetotvs.api.domain.reuniao;

import com.challengetotvs.api.domain.analise.ContratoV3;
import com.challengetotvs.api.domain.tema.TemaResponse;
import com.challengetotvs.api.domain.tema.TemaResponse.CitacaoResponse;
import com.challengetotvs.api.domain.transcricao.MetricasConversa;
import java.util.LinkedHashMap;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

public record ReuniaoDetalheResponse(
        Long id,
        String titulo,
        LocalDateTime dataHora,
        Integer duracaoMin,
        StatusReuniao status,
        boolean confirmada,
        String contato,
        int turnos,
        ClienteRef cliente,
        AnaliseDetalhe analise,
        List<TemaNaReuniao> temas,
        List<Object> compromissos,              // vazia até a E1
        MetricasResponse metricas,              // (era MetricasConversa.Metricas) nulo se não foi analisada
        boolean temTranscricao) {

    public record VendedorRef(Long id, String nome) {
    }

    public record ClienteRef(Long id, String nome, VendedorRef vendedor) {
    }

    public record TemaNaReuniao(TemaResponse tema, CitacaoResponse citacao) {
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

    public record MetricasResponse(
            boolean papeisInferidos,
            int total,
            Map<Integer, Integer> porLocutor,
            Double falaVendedor,
            MetricasConversa.Monologo maiorMonologo,
            MetricasConversa.Monologo maiorFalaCliente,
            Double trocasPorMin,
            Perguntas perguntas) {

        public record Perguntas(int vendedor, int cliente) {
        }

        public static MetricasResponse de(MetricasConversa.Metricas m) {
            Map<Integer, Integer> porLocutor = new LinkedHashMap<>();
            m.falaPorLocutor().forEach(f -> porLocutor.put(f.locutor(), f.palavras()));
            Perguntas perguntas = m.comPapeis()
                    ? new Perguntas(m.perguntas().getOrDefault("vendedor", 0),
                    m.perguntas().getOrDefault("cliente", 0))
                    : null;
            return new MetricasResponse(m.comPapeis(), m.totalPalavras(), porLocutor, m.falaVendedor(),
                    m.maiorMonologo(), m.maiorFalaCliente(), m.trocasPorMinuto(), perguntas);
        }
    }
}