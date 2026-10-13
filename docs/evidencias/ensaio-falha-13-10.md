# Ensaio de falha da cadeia — 13/10/2026 (para o slide da demo)

Só motores, códigos e tempos; nenhum texto de transcrição. Pedido: o curto do contrato (`docs/contrato/pedido-v3.json`,
12 turnos, sintético).

## Ao vivo (servidor real, chaves do `.env`, `FORCAR_FALHA`, serviço reiniciado a cada cenário)

| # | Cenário | `FORCAR_FALHA` | HTTP | Motor | Tentativas (motor: resultado, ms) | Avisos | Tempo de resposta | `/health` depois |
|---|---|---|---|---|---|---|---|---|
| 1 | llm1 fora | `llm1` | 200 | **llm2** | llm1: erro_provedor, 0 · llm2: ok, 6.274 | — | **6,28 s** | ok (llm1 X) |
| 2 | llm1 + llm2 fora | `llm1,llm2` | 200 | **local** | llm1: erro_provedor · llm2: erro_provedor · local: ok, 87 | `contingencia_modelo_local` | **0,12 s** | degradado |
| 3 | só regras | `llm1,llm2,local` | 200 | **regras** | … · local: erro_provedor · regras: ok, 3 | `contingencia_regras` | **0,03 s** | degradado |
| 4 | tudo fora | `llm1,llm2,local,regras` | **503** `analise_indisponivel` | — | 4 tentativas com erro_provedor | — | **0,02 s** | indisponivel |

Nos cenários 1 a 3 a resposta trouxe 4 temas e nenhum descarte. A subida do serviço levou cerca de 1,6 s em cada reinício.

## Simulado (`python scripts/ensaio_falha.py`; o `FORCAR_FALHA` não produz estes dois)

| # | Cenário | HTTP | Motor | Tentativas | Avisos | Descartes |
|---|---|---|---|---|---|---|
| 6 | a llm1 devolve uma citação inventada (e uma real) | 200 | **llm1** | llm1: ok | `saida_parcial` | `evidencia_nao_localizada`: 1 (o tema real fica, o inventado sai) |
| 7 | timeout da llm1 | 200 | **llm2** | llm1: timeout · llm2: ok | — | — |

No simulado o tempo é do cliente falso (centésimos de segundo). Com a LLM real, o timeout da llm1 só dispara depois de até
55 s (`TIMEOUT_LLM_S`), com prazo total de 100 s, e o Java espera 120 s.

## Para o slide
- A análise nunca é inventada: cada resposta diz o motor e o caminho percorrido (`tentativas`).
- Caiu a LLM principal: a segunda responde em ~6 s. Caíram as duas: o modelo local responde em ~0,1 s, com aviso.
- Tudo fora: 503 estruturado em ~0,02 s, e não um erro cru.
- Citação que não está na reunião é descartada e contada (`descartados`), com o aviso `saida_parcial`.

Custo de API deste ensaio: 1 chamada à llm2 (cenário 1), cerca de US$ 0,004 (estimativa: ~2,5 mil tokens de entrada e
até ~2 mil de saída no preço de tabela do gpt-4.1-mini, não conferido nesta sessão). Os outros cenários não chamam API.
