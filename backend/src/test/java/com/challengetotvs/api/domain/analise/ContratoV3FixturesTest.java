package com.challengetotvs.api.domain.analise;

import com.challengetotvs.api.domain.analise.ContratoV3.Resposta;
import org.junit.jupiter.api.Test;
import tools.jackson.databind.json.JsonMapper;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

// Garante que os JSONs de exemplo do analise-service (docs/contrato) continuam
// compatíveis com o que o backend lê. Se o João mudar o contrato, este teste quebra.
class ContratoV3FixturesTest {

    private static final JsonMapper MAPPER = JsonMapper.builder().build();

    // Os 14 padrões da lista fechada (iguais aos de pedido-v3.json)
    private static final List<String> PADROES = List.of(
            "suporte_insatisfacao", "preco_objecao", "prazo_implantacao", "concorrente_citado",
            "cancelamento_citado", "adocao_resistencia", "fiscal_problema", "orcamento_restrito",
            "expansao_unidade", "modulo_adicional", "integracao", "renovacao",
            "upgrade_licencas", "treinamento");

    private static final List<String> REGRAS = List.of(
            "sexta", "segunda", "sexta_semana_que_vem", "mesmo_dia", "mais2");

    // O Maven roda dentro de backend/, então a pasta docs fica um nível acima
    private static final Path PASTA = Path.of("..", "docs", "contrato");

    @Test
    void respostaLlmEhCompativel() throws Exception {
        verificar("resposta-v3-llm.json");
    }

    @Test
    void respostaLocalEhCompativel() throws Exception {
        verificar("resposta-v3-local.json");
    }

    @Test
    void respostaRegrasEhCompativel() throws Exception {
        verificar("resposta-v3-regras.json");
    }

    private void verificar(String arquivo) throws Exception {
        Resposta r = MAPPER.readValue(Files.readString(PASTA.resolve(arquivo)), Resposta.class);

        // Se o motor ou o sentimento forem inválidos, de(...) lança exceção e o teste falha.
        // É o mesmo erro que derrubaria a análise real (503).
        assertThat(MotorUtilizado.de(r.motor())).isNotNull();
        assertThat(SentimentoGeral.de(r.sentimento())).isNotNull();

        for (ContratoV3.Tentativa t : r.tentativas()) {
            assertThat(MotorUtilizado.de(t.motor())).isNotNull();
        }
        for (ContratoV3.TemaResposta t : r.temas()) {
            assertThat(PADROES).contains(t.padrao());
            assertThat(List.of("risco", "oportunidade")).containsAll(t.tipos());
        }
        for (ContratoV3.CompromissoResposta c : r.compromissos()) {
            // regra pode ser null (sem prazo), mas se vier tem que ser uma das 5
            if (c.regra() != null) {
                assertThat(REGRAS).contains(c.regra());
            }
        }
    }
}