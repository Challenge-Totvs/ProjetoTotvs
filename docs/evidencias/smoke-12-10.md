# Smoke com LLM real — 12/10/2026

Só fatos e contagens; nenhum texto de transcrição. Entrada: fixture sintética P90 (`tests/fixtures/transcricao-sintetica-p90.json`).

## llm2 (OpenAI, gpt-4.1-mini) — OK
| Item | Resultado |
|---|---|
| Fixture | P90: 399 turnos, 72.062 caracteres, ~21 mil tokens |
| Tempo | 17,4 s (orçamento da llm2: 35 s) |
| Resposta | `ok=true`; validou em `AnaliseResponse` |
| Padrões plantados confirmados | 6 de 6: cancelamento_citado, integracao, preco_objecao, renovacao, suporte_insatisfacao, treinamento |
| Descartes | 1 (interesse, motivo `evidencia_nao_localizada`) |

## llm1 (Anthropic) — PENDENTE
Não rodou: falta chave de workspace. Sem o smoke da llm1, o prompt continua sem validação com a llm1 real e
`PROMPT_VALIDADO_COM_LLM_REAL` NÃO foi alterado.
