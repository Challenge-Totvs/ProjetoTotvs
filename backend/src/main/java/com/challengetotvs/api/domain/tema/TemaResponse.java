package com.challengetotvs.api.domain.tema;

import java.time.LocalDate;
import java.util.Comparator;
import java.util.List;

public record TemaResponse(
        Long id,
        Long clienteId,
        String padrao,
        String padraoNome,
        String titulo,
        List<String> tipos,
        Situacao situacao,
        boolean emPauta,
        boolean atencao,
        boolean recorrente,
        int reunioesNaJanela,
        boolean leitura,
        long diasUltimaCitacao,
        LocalDate ultimaAtividade,
        Integer venceEm,
        LocalDate perdidaEm,
        String explicacao,
        List<CitacaoResponse> citacoes,
        RegistroFora registroFora,
        NaoProcede naoProcede,
        Object semelhanteNaoProcede,
        Long anteriorId,
        List<Object> avisos) {

    public record CitacaoResponse(
            Long reuniaoId, String reuniaoTitulo, LocalDate reuniaoData, int turno, Boolean tratado,
            String texto, Integer locutor, String papel, List<Contexto> contexto) {
    }

    public record Contexto(int turno, int locutor, String papel, String texto) {
    }

    public record RegistroFora(String acao, String canal, LocalDate data, String observacao, String por) {
    }

    public record NaoProcede(String motivo, String por, LocalDate em) {
    }

    private static int grupo(Situacao s) {
        return switch (s) {
            case SEM_RETORNO, OPORTUNIDADE_PERDIDA, SEM_LEITURA -> 1;
            case TRATADO_CONVERSA, TRATADO_FORA -> 2;
            case FORA_DE_PAUTA -> 3;
            case NAO_PROCEDE -> 4;
        };
    }

    public static final Comparator<TemaResponse> ORDEM = Comparator
            .comparingInt((TemaResponse t) -> grupo(t.situacao()))
            .thenComparing(t -> !t.recorrente())
            .thenComparing(TemaResponse::ultimaAtividade, Comparator.reverseOrder());
}