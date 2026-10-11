package com.challengetotvs.api.domain.tema;

import com.challengetotvs.api.domain.analise.ContratoV3.TemaResposta;
import com.challengetotvs.api.domain.tema.ConsolidadorTemas.TemaConsolidado;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class ConsolidadorTemasTest {

    // Os dois padrões "válidos" dos testes: um de risco e um de oportunidade
    private static final Map<String, TipoPadrao> PADROES = Map.of(
            "preco_objecao", TipoPadrao.RISCO,
            "modulo_adicional", TipoPadrao.OPORTUNIDADE);

    // Atalho para montar um TemaResposta (turnoFim sempre null nestes testes)
    private static TemaResposta tema(String padrao, String titulo, List<String> tipos,
                                     int turno, Boolean tratado, String texto) {
        return new TemaResposta(padrao, titulo, tipos, turno, null, tratado, texto);
    }

    @Test
    void descartaPadraoForaDaLista() {
        var saida = ConsolidadorTemas.consolidar(List.of(
                tema("padrao_que_nao_existe", "X", List.of("risco"), 1, false, "texto"),
                tema("preco_objecao", "Preço", List.of("risco"), 2, false, "está caro")), PADROES);

        assertThat(saida.size()).isEqualTo(1);                          // só o válido sobrou
        assertThat(saida.get(0).padrao()).isEqualTo("preco_objecao");
    }

    @Test
    void descartaTemaSemTexto() {
        var saida = ConsolidadorTemas.consolidar(List.of(
                tema("preco_objecao", "Preço", List.of("risco"), 2, false, "  "),       // só espaços
                tema("modulo_adicional", "BI", List.of("oportunidade"), 3, false, null)), PADROES);  // nulo

        assertThat(saida.isEmpty()).isEqualTo(true);
    }

    @Test
    void mesmoPadraoDuasVezesViraUmSoEFicaComASemResposta() {
        var saida = ConsolidadorTemas.consolidar(List.of(
                tema("preco_objecao", "Primeiro título", List.of("risco"), 2, true, "respondido"),
                tema("preco_objecao", "Segundo título", List.of("risco"), 9, false, "sem resposta")), PADROES);

        assertThat(saida.size()).isEqualTo(1);
        TemaConsolidado t = saida.get(0);
        assertThat(t.titulo()).isEqualTo("Primeiro título");   // título vem da primeira ocorrência
        assertThat(t.turno()).isEqualTo(9);                    // trecho/turno vêm da sem resposta
        assertThat(t.tratado()).isEqualTo(false);
        assertThat(t.texto()).isEqualTo("sem resposta");
    }

    @Test
    void semNenhumaSemRespostaFicaComAPrimeira() {
        var saida = ConsolidadorTemas.consolidar(List.of(
                tema("preco_objecao", "A", List.of("risco"), 2, true, "primeira"),
                tema("preco_objecao", "B", List.of("risco"), 9, null, "segunda")), PADROES);

        assertThat(saida.get(0).texto()).isEqualTo("primeira");
    }

    @Test
    void unePosTiposDasDuasOcorrencias() {
        var saida = ConsolidadorTemas.consolidar(List.of(
                tema("modulo_adicional", "BI", List.of("oportunidade"), 2, false, "quero BI"),
                tema("modulo_adicional", "BI", List.of("risco"), 5, false, "depende do fiscal")), PADROES);

        assertThat(saida.get(0).risco()).isEqualTo(true);          // tema duplo
        assertThat(saida.get(0).oportunidade()).isEqualTo(true);
    }

    @Test
    void semTiposUsaOTipoDoPadrao() {
        var saida = ConsolidadorTemas.consolidar(List.of(
                tema("preco_objecao", "Preço", List.of(), 2, false, "caro"),
                tema("modulo_adicional", "BI", List.of(), 3, false, "quero")), PADROES);

        assertThat(saida.get(0).risco()).isEqualTo(true);           // padrão de risco
        assertThat(saida.get(0).oportunidade()).isEqualTo(false);
        assertThat(saida.get(1).risco()).isEqualTo(false);          // padrão de oportunidade
        assertThat(saida.get(1).oportunidade()).isEqualTo(true);
    }

    @Test
    void mantemAOrdemDeChegada() {
        var saida = ConsolidadorTemas.consolidar(List.of(
                tema("modulo_adicional", "BI", List.of("oportunidade"), 3, false, "quero"),
                tema("preco_objecao", "Preço", List.of("risco"), 2, false, "caro")), PADROES);

        assertThat(saida.get(0).padrao()).isEqualTo("modulo_adicional");
        assertThat(saida.get(1).padrao()).isEqualTo("preco_objecao");
    }
}