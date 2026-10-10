package com.challengetotvs.api.domain.analise;

import com.challengetotvs.api.domain.analise.Pseudonimizador.Entidade;
import com.challengetotvs.api.domain.analise.Pseudonimizador.Tipo;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class PseudonimizadorTest {

    private static Pseudonimizador comHelena() {
        return new Pseudonimizador(List.of(
                new Entidade("Helena Prado", Tipo.PESSOA),
                new Entidade("Helena", Tipo.PESSOA)));
    }

    @Test
    void trocaOTermoLongoAntesDoCurto() {                       // o critério da J8: "Helena Prado" e "Helena"
        String saida = comHelena().pseudonimizar("Helena Prado falou. Depois Helena concordou.");

        assertThat(saida).isEqualTo("[PESSOA_1] falou. Depois [PESSOA_2] concordou.");
        assertThat(saida).doesNotContain("Prado");               // não sobrou "Prado" solto
    }

    @Test
    void trocaOTermoLongoMesmoQuandoOCurtoVemPrimeiroNaLista() {
        Pseudonimizador p = new Pseudonimizador(List.of(
                new Entidade("Helena", Tipo.PESSOA),
                new Entidade("Helena Prado", Tipo.PESSOA)));

        String saida = p.pseudonimizar("Helena Prado e Helena");

        assertThat(saida).isEqualTo("[PESSOA_2] e [PESSOA_1]");
    }

    @Test
    void mesmoNomeViraSempreOMesmoPseudonimo() {
        String saida = comHelena().pseudonimizar("Helena, Helena e Helena.");

        assertThat(saida).isEqualTo("[PESSOA_2], [PESSOA_2] e [PESSOA_2].");
    }

    @Test
    void contadorEPorTipo() {                                   // é o exemplo da tela de Configurações
        Pseudonimizador p = new Pseudonimizador(List.of(
                new Entidade("Helena Prado", Tipo.PESSOA),
                new Entidade("Clínica Bem Viver", Tipo.EMPRESA),
                new Entidade("Jundiaí", Tipo.LOCAL),
                new Entidade("Kelwin", Tipo.PESSOA)));

        String saida = p.pseudonimizar(
                "Helena Prado, da Clínica Bem Viver, vai abrir a unidade de Jundiaí. O Kelwin manda o plano.");

        assertThat(saida).isEqualTo(
                "[PESSOA_1], da [EMPRESA_1], vai abrir a unidade de [LOCAL_1]. O [PESSOA_2] manda o plano.");
    }

    @Test
    void soTrocaPalavraInteiraComAcentos() {
        Pseudonimizador p = new Pseudonimizador(List.of(new Entidade("João", Tipo.PESSOA)));

        assertThat(p.pseudonimizar("João e Joãozinho")).isEqualTo("[PESSOA_1] e Joãozinho");
        assertThat(p.pseudonimizar("Sem João.")).isEqualTo("Sem [PESSOA_1].");
        assertThat(p.pseudonimizar("DeJoão")).isEqualTo("DeJoão");
    }

    @Test
    void diferenciaMaiusculasDeMinusculas() {
        String saida = comHelena().pseudonimizar("helena não é Helena");

        assertThat(saida).isEqualTo("helena não é [PESSOA_2]");
    }

    @Test
    void caracteresEspeciaisNoNomeNaoQuebramARegex() {
        Pseudonimizador p = new Pseudonimizador(List.of(new Entidade("Alfa S.A. (Matriz)", Tipo.EMPRESA)));

        assertThat(p.pseudonimizar("Falei com a Alfa S.A. (Matriz) ontem"))
                .isEqualTo("Falei com a [EMPRESA_1] ontem");
    }

    @Test
    void semEntidadesOTextoNaoMuda() {
        Pseudonimizador p = new Pseudonimizador(List.of());

        assertThat(p.pseudonimizar("Bom dia")).isEqualTo("Bom dia");
        assertThat(p.mapa()).isEqualTo(Map.of());
    }

    @Test
    void termosVaziosEDuplicadosSaoIgnorados() {
        Pseudonimizador p = new Pseudonimizador(List.of(
                new Entidade("  ", Tipo.PESSOA),
                new Entidade("Ana", Tipo.PESSOA),
                new Entidade("Ana", Tipo.PESSOA)));

        assertThat(p.mapa().size()).isEqualTo(1);
        assertThat(p.pseudonimizar("Ana")).isEqualTo("[PESSOA_1]");
    }

    @Test
    void restauraOTextoOriginalIdaEVolta() {
        Pseudonimizador p = comHelena();
        String original = "Helena Prado falou. Depois Helena concordou.";

        assertThat(p.restaurar(p.pseudonimizar(original))).isEqualTo(original);
    }

    @Test
    void restauraUmaCitacaoSoltaEMantemPseudonimoDesconhecido() {
        Pseudonimizador p = comHelena();

        assertThat(p.restaurar("Obrigado, [PESSOA_1].")).isEqualTo("Obrigado, Helena Prado.");
        assertThat(p.restaurar("Veja [PESSOA_9]")).isEqualTo("Veja [PESSOA_9]");
    }

    @Test
    void guardaOMapaDePseudonimoParaOriginal() {
        assertThat(comHelena().mapa()).isEqualTo(Map.of(
                "[PESSOA_1]", "Helena Prado",
                "[PESSOA_2]", "Helena"));
    }
}