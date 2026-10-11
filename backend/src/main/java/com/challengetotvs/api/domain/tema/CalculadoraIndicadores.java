package com.challengetotvs.api.domain.tema;

import java.util.List;

public final class CalculadoraIndicadores {

    private CalculadoraIndicadores() {
    }

    public record Item(boolean risco, boolean oportunidade, ResultadoSituacao resultado) {
    }

    public static Indicadores calcular(List<Item> itens) {
        int emPauta = 0, riscosSemRetorno = 0, riscosRecorrentes = 0, oportPerdidas = 0;
        int oportSemRetorno = 0, tratadosConversa = 0, tratadosFora = 0, foraDePauta = 0;
        int naoProcede = 0, recorrentes = 0, atencao = 0;

        for (Item item : itens) {
            ResultadoSituacao r = item.resultado();
            Situacao s = r.situacao();

            if (r.emPauta()) emPauta++;
            if (r.recorrente()) recorrentes++;
            if (r.atencao()) atencao++;

            if (item.risco() && (s == Situacao.SEM_RETORNO || s == Situacao.OPORTUNIDADE_PERDIDA)) {
                riscosSemRetorno++;
                if (r.recorrente()) riscosRecorrentes++;   // recorrentes só entre os riscos sem retorno
            }
            if (item.oportunidade() && s == Situacao.SEM_RETORNO) oportSemRetorno++;
            if (s == Situacao.OPORTUNIDADE_PERDIDA) oportPerdidas++;

            if (s == Situacao.TRATADO_CONVERSA) tratadosConversa++;
            if (s == Situacao.TRATADO_FORA) tratadosFora++;
            if (s == Situacao.FORA_DE_PAUTA) foraDePauta++;
            if (s == Situacao.NAO_PROCEDE) naoProcede++;
        }
        return new Indicadores(emPauta, riscosSemRetorno, riscosRecorrentes, oportPerdidas, oportSemRetorno,
                tratadosConversa, tratadosFora, foraDePauta, naoProcede, recorrentes, atencao);
    }
}