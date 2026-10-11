package com.challengetotvs.api.domain.tema;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;

public final class EscolhaDeTema {

    private EscolhaDeTema() {
    }

    public record Candidato(Long id, List<CitacaoEntrada> citacoes, boolean oportunidade, LocalDate dataFora, boolean naoProcede) {
    }

    public static Optional<Candidato> ativo(List<Candidato> candidatos, int janela, LocalDate hoje) {
        for (Candidato c : candidatos) {
            if (c.naoProcede()) {
                continue;
            }
            if (c.citacoes().isEmpty()) {
                return Optional.of(c);
            }
            Situacao situacao = CalculadoraSituacao
                    .calcular(c.citacoes(), c.oportunidade(), c.dataFora(), false, janela, hoje)
                    .situacao();
            if (situacao != Situacao.FORA_DE_PAUTA) {
                return Optional.of(c);
            }
        }
        return Optional.empty();
    }

    // Último tema do padrão que não foi marcado "não procede": vira o "anterior" do novo
    public static Optional<Candidato> anterior(List<Candidato> candidatos) {
        Candidato ultimo = null;
        for (Candidato c : candidatos) {
            if (!c.naoProcede()) {
                ultimo = c;
            }
        }
        return Optional.ofNullable(ultimo);
    }
}