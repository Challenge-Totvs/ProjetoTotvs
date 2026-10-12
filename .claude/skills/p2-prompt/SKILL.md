---
name: p2-prompt
description: Tarefa P2 — prompt e llm_engine v3 (temas por padrão com trecho literal, papéis, compromissos, resumo, sentimentoSerie), timeouts e cadeia llm1 -> llm2. Rode depois da P1.
disable-model-invocation: true
---
Tarefa P2 de `docs/DIVISAO_TRABALHO.md` §3 (tamanho G; divida em duas sessões se precisar). Ciclo do `CLAUDE.md`.

Leia: `docs/contrato/contrato-v3.md` §3.3, §4, §6, §7.3–7.7, §8; `docs/SDD.md` §6.5 (prompt da LLM);
`app/engines/llm_engine.py`, `app/orchestrator.py`, `app/schemas.py`.

Escopo:
1. Prompt montado a partir de `turnos` (cada turno com `n` e `locutor`), `dataReuniao`, `padroes` (lista fechada),
   `contraexemplos`; extras opcionais entram só se presentes (§3.3). Neutralize `<transcricao>`/`</transcricao>`
   no texto. A LLM pede: padrão da lista + trecho literal + turno, `tratado` quando houver, papéis, compromissos
   com `regra`, resumo, próximos passos, `sentimentoSerie`, `interesse`.
2. Saída estruturada por `SaidaLLM`. O código escreve `motor`, `tentativas` (um item por tentativa, com `erro` de §6.5),
   `versaoContrato`.
3. Clients com `timeout=` (llm1 ~55 s, llm2 ~35 s) e `max_retries=0`; erro de chave ausente, 401 e timeout viram
   uma tentativa registrada, nunca silêncio. Logue por tentativa, sem texto de transcrição.
4. Limites de saída do §7.6 e limites do pedido do §3.2.
5. Testes com clients simulados: sucesso llm1; llm1 falha e llm2 responde; resposta fora do schema; transcrição com
   `</transcricao>` maliciosa. NENHUM teste chama rede (regra 4).

Não faça: conferência de citação (P3; deixe um ponto de extensão claro entre a resposta da LLM e a saída), regex (P4).
Smoke com chave real: só o João Paulo roda, em `scripts/smoke_llm.py`, com chaves de desenvolvimento; você NÃO lê `.env`.
Commit por assunto: `feat(P2): ...`.
