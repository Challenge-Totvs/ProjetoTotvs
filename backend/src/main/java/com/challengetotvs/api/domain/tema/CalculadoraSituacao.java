package com.challengetotvs.api.domain.tema;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.Comparator;
import java.util.List;

public final class CalculadoraSituacao {

    private CalculadoraSituacao() {
    }

    public static ResultadoSituacao calcular(List<CitacaoEntrada> citacoes, boolean oportunidade, LocalDate dataFora, boolean naoProcede, int janela, LocalDate hoje) {
        if (citacoes == null || citacoes.isEmpty()) {
            throw new IllegalArgumentException("Um tema precisa de ao menos uma citação");
        }

        List<CitacaoEntrada> ordenadas = citacoes.stream()
                .sorted(Comparator.comparing(CitacaoEntrada::dataHora)
                        .thenComparingInt(CitacaoEntrada::turno))
                .toList();
        CitacaoEntrada ultima = ordenadas.get(ordenadas.size() - 1);

        LocalDate dataUltima = ultima.dataHora().toLocalDate();
        long diasUltima = ChronoUnit.DAYS.between(dataUltima, hoje);

        boolean foraVale = dataFora != null && !dataFora.isBefore(dataUltima);

        LocalDate ultimaAtividade = foraVale && dataFora.isAfter(dataUltima) ? dataFora : dataUltima;
        boolean recente = ChronoUnit.DAYS.between(ultimaAtividade, hoje) <= janela;

        long reunioesNaJanela = ordenadas.stream()
                .filter(c -> ChronoUnit.DAYS.between(c.dataHora().toLocalDate(), hoje) <= janela)
                .map(CitacaoEntrada::reuniaoId)
                .distinct()
                .count();

        Situacao situacao;
        if (naoProcede) {
            situacao = Situacao.NAO_PROCEDE;
        } else if (foraVale) {
            situacao = recente ? Situacao.TRATADO_FORA : Situacao.FORA_DE_PAUTA;
        } else if (Boolean.TRUE.equals(ultima.tratado())) {
            situacao = recente ? Situacao.TRATADO_CONVERSA : Situacao.FORA_DE_PAUTA;
        } else if (ultima.tratado() == null) {
            situacao = recente ? Situacao.SEM_LEITURA : Situacao.FORA_DE_PAUTA;
        } else if (oportunidade && diasUltima > janela) {
            situacao = Situacao.OPORTUNIDADE_PERDIDA;
        } else {
            situacao = Situacao.SEM_RETORNO;
        }

        boolean emPauta = situacao != Situacao.FORA_DE_PAUTA && situacao != Situacao.NAO_PROCEDE;
        boolean recorrente = emPauta && reunioesNaJanela >= 2;
        boolean atencao = situacao == Situacao.SEM_RETORNO
                || situacao == Situacao.OPORTUNIDADE_PERDIDA
                || situacao == Situacao.SEM_LEITURA;

        Integer venceEm = (situacao == Situacao.SEM_RETORNO && oportunidade)
                ? (int) (janela - diasUltima + 1)
                : null;
        LocalDate perdidaEm = (situacao == Situacao.OPORTUNIDADE_PERDIDA)
                ? dataUltima.plusDays(janela + 1L)
                : null;

        return new ResultadoSituacao(situacao, emPauta, recorrente, (int) reunioesNaJanela,
                atencao, venceEm, perdidaEm, ultimaAtividade);
    }
}