package com.challengetotvs.api.domain.analise;

import com.challengetotvs.api.domain.analise.ContratoV3.Contraexemplo;
import com.challengetotvs.api.domain.analise.ContratoV3.Pedido;
import com.challengetotvs.api.domain.analise.ContratoV3.Resposta;
import com.challengetotvs.api.domain.analise.ContratoV3.TurnoPedido;
import org.junit.jupiter.api.Test;
import tools.jackson.databind.json.JsonMapper;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

class ContratoV3Test {

    private static final JsonMapper MAPPER = JsonMapper.builder().build();

    @Test
    void leARespostaDoExemploDoSdd() {
        String json = """
                {
                  "motor": "llm1",
                  "tentativas": [{ "motor": "llm1", "ok": true }],
                  "score": 69,
                  "sentimento": "neutro",
                  "papeis": { "1": "vendedor", "2": "cliente" },
                  "resumo": "Alinhamento da renovação.",
                  "interesse": [{ "texto": "Reagiu bem", "turno": 6, "citacao": "Isso ajuda bastante." }],
                  "proximosPassos": ["Responder sobre os chamados"],
                  "temas": [
                    { "padrao": "suporte_insatisfacao", "titulo": "Demora do suporte", "tipos": ["risco"],
                      "turno": 7, "turnoFim": 7, "tratado": false,
                      "texto": "O suporte continua demorando para responder os chamados." }
                  ],
                  "compromissos": [{ "turno": 16, "texto": "Te envio a proposta até segunda.", "regra": "segunda" }],
                  "sentimentoSerie": [[2, 0.1], [7, -0.5], [15, 0.3]],
                  "descartados": [{ "texto": "...", "motivo": "evidencia_nao_localizada" }]
                }
                """;

        Resposta r = MAPPER.readValue(json, Resposta.class);

        assertThat(r.motor()).isEqualTo("llm1");
        assertThat(r.score()).isEqualTo(69);
        assertThat(r.papeis().get("2")).isEqualTo("cliente");
        assertThat(r.temas().get(0).padrao()).isEqualTo("suporte_insatisfacao");
        assertThat(r.temas().get(0).tratado()).isEqualTo(false);
        assertThat(r.compromissos().get(0).regra()).isEqualTo("segunda");
        assertThat(r.sentimentoSerie().get(1).get(1)).isEqualTo(-0.5);
    }

    @Test
    void respostaMinimaDoModeloLocalTemListasVazias() {
        Resposta r = MAPPER.readValue(
                "{\"motor\":\"regras\",\"score\":50,\"sentimento\":\"neutro\"}", Resposta.class);

        assertThat(r.temas().isEmpty()).isEqualTo(true);
        assertThat(r.compromissos().isEmpty()).isEqualTo(true);
        assertThat(r.resumo()).isEqualTo(null);
    }

    @Test
    void ignoraCampoNovoQueOPythonAcrescentar() {
        Resposta r = MAPPER.readValue(
                "{\"motor\":\"llm1\",\"campoNovo\":123}", Resposta.class);

        assertThat(r.motor()).isEqualTo("llm1");
    }

    @Test
    void serializaOPedidoComOsNomesDoContrato() {
        Pedido pedido = new Pedido(
                List.of(new TurnoPedido(1, 1, "Bom dia, [PESSOA_1].")),
                "2026-10-07",
                List.of("preco_objecao"),
                List.of(new Contraexemplo("cancelamento_citado", "Vamos cancelar a reserva.", "fora_contexto")));

        String json = MAPPER.writeValueAsString(pedido);

        assertThat(json).contains("\"dataReuniao\":\"2026-10-07\"");
        assertThat(json).contains("\"locutor\":1");
        assertThat(json).contains("\"contraexemplos\"");
    }
}