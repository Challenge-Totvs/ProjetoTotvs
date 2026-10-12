# Smoke com LLM real — 12/10/2026

Só fatos e contagens; nenhum texto de transcrição. Entradas sintéticas: pedido curto do contrato
(`docs/contrato/pedido-v3.json`) e fixture P90 (`tests/fixtures/transcricao-sintetica-p90.json`).

## llm2 (OpenAI, gpt-4.1-mini) — OK
| Item | Resultado |
|---|---|
| Fixture | P90: 399 turnos, 72.062 caracteres, ~21 mil tokens |
| Tempo | 17,4 s (orçamento da llm2: 35 s) |
| Resposta | `ok=true`; validou em `AnaliseResponse` |
| Padrões plantados confirmados | 6 de 6: cancelamento_citado, integracao, preco_objecao, renovacao, suporte_insatisfacao, treinamento |
| Descartes | 1 (interesse, motivo `evidencia_nao_localizada`) |

## llm1 (Anthropic, claude-haiku-5-5) — OK
Duas execuções.

| Item | (1) Pedido curto | (2) Fixture P90 |
|---|---|---|
| Entrada | 12 turnos, 740 caracteres | 399 turnos, 72.062 caracteres |
| Tempo | 7,2 s | 8,7 s (orçamento da llm1: 55 s) |
| Resposta | `ok=true`; validou em `AnaliseResponse` | `ok=true` |
| Temas | 4: modulo_adicional, orcamento_restrito, renovacao, suporte_insatisfacao | 6 de 6 plantados confirmados |
| Interesses | 2 | 4 |
| Compromissos | 2 | 2 |
| Eventos de conduta | 1 | não registrado |
| Descartes | nenhum | nenhum |

## Conclusão
As duas LLMs responderam e validaram no contrato v3; o prompt passa a valer como validado com LLM real
(`PROMPT_VALIDADO_COM_LLM_REAL = True`). Pior caso medido: 17,4 s (llm2, P90). O timeout do Java fica em 120 s.
