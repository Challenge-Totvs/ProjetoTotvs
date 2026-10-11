package com.challengetotvs.api.domain.tema;

import java.time.LocalDate;
import java.util.Set;

public final class RegrasAcaoTema {

    private static final Set<String> ACOES_OPORTUNIDADE =
            Set.of("proposta", "demonstracao", "material", "telefone", "outra_area", "outro_o");
    private static final Set<String> ACOES_RISCO =
            Set.of("suporte", "retorno", "condicao", "alinhamento", "outro_r");
    private static final Set<String> CANAIS =
            Set.of("email", "telefone", "whatsapp", "presencial", "outro");
    private static final Set<String> MOTIVOS =
            Set.of("nao_cliente", "fora_contexto", "tema_errado", "outro");

    public static final String CANAL_PADRAO = "email";

    private RegrasAcaoTema() {
    }

    public static boolean acaoValida(String acao, boolean risco, boolean oportunidade) {
        if (acao == null) {
            return false;
        }
        return (oportunidade && ACOES_OPORTUNIDADE.contains(acao)) || (risco && ACOES_RISCO.contains(acao));
    }

    public static boolean canalValido(String canal) {
        return canal != null && CANAIS.contains(canal);
    }

    public static boolean motivoValido(String motivo) {
        return motivo == null || motivo.isBlank() || MOTIVOS.contains(motivo);
    }

    public static boolean dataFutura(LocalDate data, LocalDate hoje) {
        return data.isAfter(hoje);
    }

    public static boolean anteriorAUltimaCitacao(LocalDate data, LocalDate ultimaCitacao) {
        return data.isBefore(ultimaCitacao);
    }
}