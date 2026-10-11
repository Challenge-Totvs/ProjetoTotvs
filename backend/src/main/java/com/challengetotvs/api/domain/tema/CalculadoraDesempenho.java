package com.challengetotvs.api.domain.tema;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.List;

public final class CalculadoraDesempenho {

    private CalculadoraDesempenho() {
    }

    public record ResumoTemas(
            int temasCitados,
            Double taxaConversa,
            int tratadosConversa,
            int comLeitura,
            int tratadosFora,
            int oportTratadas,
            int oportIdentificadas,
            int riscosSemRetorno,
            int oportPerdidas) {
    }

    public static ResumoTemas calcular(List<TemaResponse> temas, int janela, LocalDate hoje) {
        int citados = 0, comLeitura = 0, respondidos = 0, tratadosFora = 0;
        int oportTratadas = 0, oportIdentificadas = 0, riscosSemRetorno = 0, oportPerdidas = 0;

        for (TemaResponse t : temas) {
            if (t.situacao() == Situacao.NAO_PROCEDE || t.citacoes().isEmpty()) {
                continue;
            }
            var ultima = t.citacoes().get(0);
            boolean respondido = Boolean.TRUE.equals(ultima.tratado());

            if (naJanela(ultima.reuniaoData(), janela, hoje)) {
                citados++;
                if (ultima.tratado() != null) {
                    comLeitura++;
                    if (respondido) respondidos++;
                }
                if (t.tipos().contains("oportunidade")) {
                    oportIdentificadas++;
                    // tratada = respondida na reunião OU com "tratei fora" válido
                    if (respondido || t.situacao() == Situacao.TRATADO_FORA) oportTratadas++;
                }
            }
            if (t.registroFora() != null && naJanela(t.registroFora().data(), janela, hoje)) {
                tratadosFora++;
            }
            if (t.tipos().contains("risco")
                    && (t.situacao() == Situacao.SEM_RETORNO || t.situacao() == Situacao.OPORTUNIDADE_PERDIDA)) {
                riscosSemRetorno++;
            }
            if (t.situacao() == Situacao.OPORTUNIDADE_PERDIDA) {
                oportPerdidas++;
            }
        }

        Double taxa = comLeitura == 0 ? null : (double) respondidos / comLeitura;
        return new ResumoTemas(citados, taxa, respondidos, comLeitura, tratadosFora, oportTratadas,
                oportIdentificadas, riscosSemRetorno, oportPerdidas);
    }

    private static boolean naJanela(LocalDate data, int janela, LocalDate hoje) {
        long dias = ChronoUnit.DAYS.between(data, hoje);
        return dias >= 0 && dias <= janela;
    }
}