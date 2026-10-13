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

## Ajuste de prompt, 13/10/2026
Depois do smoke de 12/10, o prompt (`_INSTRUCOES`, em `app/engines/llm_engine.py`) foi ajustado por problemas vistos no app
com as LLMs reais: título de tema que não batia com a citação, compromisso repetido por confirmação do vendedor, prazo
"amanhã" mapeado para `segunda` ou `mesmo_dia`, e próximos passos com dia da semana que ninguém disse.

Mudanças: título limitado ao conteúdo do trecho; uma entrega prometida diferente é um compromisso, e a confirmação da mesma
promessa não cria outro; `regra` só quando o prazo dito bate exatamente (senão `null`); promessas novas e curtas de ação do
vendedor entram mesmo com prazo vago; sem datas inventadas em `resumo` e `proximosPassos`.

Conferência (llm1, 5 execuções por transcrição): na renovação de exemplo, 4 de 5 só com a promessa do turno 16 (1 de 5 trouxe
também "Mando sim."); na transcrição com 3 promessas, as 3 em 4 de 5 e o "amanhã" sem prazo em 5 de 5 (o prompt antigo acertou
o "amanhã" em 1 de 3). `smoke_llm.py` (llm1 e llm2) ok em 13/10 e `pytest` verde. O contrato v3 não mudou.

Nota: numa execução isolada de `smoke_llm.py llm2` (13/10, 16h) a OpenAI estourou o orçamento de 35 s (`timeout`); a repetição
respondeu em 10,2 s. Lentidão passageira do provedor; a cadeia cai para o modelo local nesse caso.