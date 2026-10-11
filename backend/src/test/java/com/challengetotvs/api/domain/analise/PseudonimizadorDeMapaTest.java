package com.challengetotvs.api.domain.analise;

import com.challengetotvs.api.domain.analise.Pseudonimizador.Entidade;
import com.challengetotvs.api.domain.analise.Pseudonimizador.Tipo;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class PseudonimizadorDeMapaTest {

    @Test
    void refazOMesmoPseudonimizadorAPartirDoMapa() {
        var original = new Pseudonimizador(List.of(
                new Entidade("Clínica Bem Viver", Tipo.EMPRESA),
                new Entidade("Helena Prado", Tipo.PESSOA),
                new Entidade("Helena", Tipo.PESSOA),
                new Entidade("Kelwin Bastos", Tipo.PESSOA)));
        String texto = "Helena Prado, da Clínica Bem Viver, falou com Kelwin Bastos. Helena concordou.";

        var refeito = Pseudonimizador.deMapa(original.mapa());

        assertThat(refeito.pseudonimizar(texto)).isEqualTo(original.pseudonimizar(texto));
        assertThat(refeito.mapa()).isEqualTo(original.mapa());
    }

    @Test
    void ignoraChaveForaDoFormato() {
        var refeito = Pseudonimizador.deMapa(java.util.Map.of("lixo", "Fulano", "[PESSOA_1]", "Maria"));

        assertThat(refeito.pseudonimizar("Fulano e Maria")).isEqualTo("Fulano e [PESSOA_1]");
    }
}