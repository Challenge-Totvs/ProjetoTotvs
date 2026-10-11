package com.challengetotvs.api.domain.tema;

public record Indicadores(
        int emPauta, int riscosSemRetorno, int riscosRecorrentes, int oportPerdidas,
        int oportSemRetorno, int tratadosConversa, int tratadosFora, int foraDePauta,
        int naoProcede, int recorrentes, int atencao) {

    public static Indicadores zerados() {
        return new Indicadores(0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0);
    }
}