package com.challengetotvs.api.domain.analise;

import com.challengetotvs.api.domain.analise.ContratoV3.CompromissoResposta;
import com.challengetotvs.api.domain.analise.ContratoV3.Descartado;
import com.challengetotvs.api.domain.analise.ContratoV3.Interesse;
import com.challengetotvs.api.domain.analise.ContratoV3.Resposta;
import com.challengetotvs.api.domain.analise.ContratoV3.TemaResposta;
import com.challengetotvs.api.domain.analise.Pseudonimizador.Entidade;
import com.challengetotvs.api.domain.analise.Pseudonimizador.Tipo;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class TradutorRespostaTest {

    private static final Pseudonimizador PSEUDO = new Pseudonimizador(List.of(
            new Entidade("Helena Prado", Tipo.PESSOA),
            new Entidade("Clínica Bem Viver", Tipo.EMPRESA)));

    private static Resposta respostaComPseudonimos() {
        return new Resposta(
                "llm1", List.of(), 69, "neutro", Map.of("1", "vendedor"),
                "Reunião com [PESSOA_1] da [EMPRESA_1].",
                List.of(new Interesse("[PESSOA_1] gostou do reajuste", 6, "Isso ajuda, [PESSOA_1].")),
                List.of("Enviar proposta para [PESSOA_1]"),
                List.of(new TemaResposta("preco_objecao", "Preço para [EMPRESA_1]", List.of("risco"),
                        7, null, false, "Está caro para a [EMPRESA_1].")),
                List.of(new CompromissoResposta(16, "Envio a proposta para [PESSOA_1] até segunda.", "segunda")),
                List.of(List.of(2.0, 0.1)),
                List.of(new Descartado("[PESSOA_1] disse algo", "evidencia_nao_localizada")));
    }

    @Test
    void devolveOsNomesOriginaisEmTodosOsTextos() {
        Resposta r = TradutorResposta.restaurar(respostaComPseudonimos(), PSEUDO);

        assertThat(r.resumo()).isEqualTo("Reunião com Helena Prado da Clínica Bem Viver.");
        assertThat(r.interesse().get(0).texto()).isEqualTo("Helena Prado gostou do reajuste");
        assertThat(r.interesse().get(0).citacao()).isEqualTo("Isso ajuda, Helena Prado.");
        assertThat(r.proximosPassos().get(0)).isEqualTo("Enviar proposta para Helena Prado");
        assertThat(r.temas().get(0).titulo()).isEqualTo("Preço para Clínica Bem Viver");
        assertThat(r.temas().get(0).texto()).isEqualTo("Está caro para a Clínica Bem Viver.");
        assertThat(r.compromissos().get(0).texto()).isEqualTo("Envio a proposta para Helena Prado até segunda.");
        assertThat(r.descartados().get(0).texto()).isEqualTo("Helena Prado disse algo");
    }

    @Test
    void naoMexeNosCamposQueNaoSaoTexto() {
        Resposta original = respostaComPseudonimos();

        Resposta r = TradutorResposta.restaurar(original, PSEUDO);

        assertThat(r.motor()).isEqualTo("llm1");
        assertThat(r.score()).isEqualTo(69);
        assertThat(r.temas().get(0).padrao()).isEqualTo("preco_objecao");
        assertThat(r.temas().get(0).tratado()).isEqualTo(false);
        assertThat(r.temas().get(0).turno()).isEqualTo(7);
        assertThat(r.compromissos().get(0).regra()).isEqualTo("segunda");
        assertThat(r.sentimentoSerie()).isEqualTo(original.sentimentoSerie());
    }

    @Test
    void respostaSemTextoOpcionalNaoQuebra() {
        Resposta minima = new Resposta("regras", null, 50, "neutro", null, null, null, null, null, null, null, null);

        Resposta r = TradutorResposta.restaurar(minima, PSEUDO);

        assertThat(r.resumo()).isEqualTo(null);
        assertThat(r.temas().isEmpty()).isEqualTo(true);
    }
}