package com.challengetotvs.api.domain.tema;

import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public final class DetectorMudancas {

    public static final int JANELA_DIAS = 14;

    private DetectorMudancas() {
    }

    public record Mudanca(String tipo, LocalDate data, Long temaId, String temaTitulo,
                          Long clienteId, String clienteNome) {
    }

    public static List<Mudanca> detectar(List<TemaResponse> temas, LocalDate hoje) {
        List<Mudanca> saida = new ArrayList<>();

        for (TemaResponse t : temas) {
            if (t.situacao() == Situacao.NAO_PROCEDE || t.citacoes().isEmpty()) {
                continue;
            }
            var ultima = t.citacoes().get(0);

            if (naJanela(ultima.reuniaoData(), hoje)) {
                saida.add(nova(tipoDaUltimaCitacao(t), ultima.reuniaoData(), t));
            }
            if (t.perdidaEm() != null && naJanela(t.perdidaEm(), hoje)) {
                saida.add(nova("virou_oportunidade_perdida", t.perdidaEm(), t));
            }

            if (t.registroFora() != null && naJanela(t.registroFora().data(), hoje)) {
                saida.add(nova("tratado_fora", t.registroFora().data(), t));
            }
        }

        saida.sort(Comparator.comparing(Mudanca::data).reversed().thenComparing(Mudanca::temaId));
        return saida;
    }

    private static String tipoDaUltimaCitacao(TemaResponse t) {
        boolean risco = t.tipos().contains("risco");
        boolean oportunidade = t.tipos().contains("oportunidade");
        var ultima = t.citacoes().get(0);

        if (t.citacoes().size() == 1) {
            if (risco && oportunidade) return "novo_tema";
            return risco ? "novo_risco" : "nova_oportunidade";
        }

        Boolean anterior = t.citacoes().get(1).tratado();
        Boolean atual = ultima.tratado();
        if (atual == null) {
            return "citado_sem_leitura";
        }
        if (atual) {
            return Boolean.FALSE.equals(anterior) ? "tratado_conversa" : "voltou_a_aparecer";
        }
        return Boolean.TRUE.equals(anterior) ? "voltou_sem_resposta" : "citado_de_novo_sem_resposta";
    }

    private static boolean naJanela(LocalDate data, LocalDate hoje) {
        long dias = ChronoUnit.DAYS.between(data, hoje);
        return dias >= 0 && dias <= JANELA_DIAS;
    }

    private static Mudanca nova(String tipo, LocalDate data, TemaResponse t) {
        return new Mudanca(tipo, data, t.id(), t.titulo(), t.clienteId(), t.clienteNome());
    }
}