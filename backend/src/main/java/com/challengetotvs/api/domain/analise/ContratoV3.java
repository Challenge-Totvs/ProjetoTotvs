package com.challengetotvs.api.domain.analise;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import java.util.List;
import java.util.Map;

public final class ContratoV3 {

    private ContratoV3() {
    }


    public record Pedido(
            List<TurnoPedido> turnos,
            String dataReuniao,
            List<String> padroes,
            List<Contraexemplo> contraexemplos) {
    }

    public record TurnoPedido(int n, int locutor, String texto) {
    }

    public record Contraexemplo(String padrao, String texto, String motivo) {
    }


    @JsonIgnoreProperties(ignoreUnknown = true)
    public record Resposta(
            String motor,
            List<Tentativa> tentativas,
            Integer score,
            String sentimento,
            Map<String, String> papeis,
            String resumo,
            List<Interesse> interesse,
            List<String> proximosPassos,
            List<TemaResposta> temas,
            List<CompromissoResposta> compromissos,
            List<List<Double>> sentimentoSerie,
            List<Descartado> descartados) {

        public Resposta {
            tentativas = tentativas == null ? List.of() : tentativas;
            papeis = papeis == null ? Map.of() : papeis;
            interesse = interesse == null ? List.of() : interesse;
            proximosPassos = proximosPassos == null ? List.of() : proximosPassos;
            temas = temas == null ? List.of() : temas;
            compromissos = compromissos == null ? List.of() : compromissos;
            sentimentoSerie = sentimentoSerie == null ? List.of() : sentimentoSerie;
            descartados = descartados == null ? List.of() : descartados;
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record Tentativa(String motor, boolean ok) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record Interesse(String texto, int turno, String citacao) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record TemaResposta(
            String padrao,
            String titulo,
            List<String> tipos,
            int turno,
            Integer turnoFim,
            Boolean tratado,
            String texto) {

        public TemaResposta {
            tipos = tipos == null ? List.of() : tipos;
        }
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record CompromissoResposta(int turno, String texto, String regra) {
    }

    @JsonIgnoreProperties(ignoreUnknown = true)
    public record Descartado(String texto, String motivo) {
    }
}