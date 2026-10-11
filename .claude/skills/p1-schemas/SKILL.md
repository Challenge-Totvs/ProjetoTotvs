---
name: p1-schemas
description: Tarefa P1 — schemas Pydantic completos da resposta v3 e de SaidaLLM; fixtures validadas no Python. Rode depois da P0.
disable-model-invocation: true
---
Tarefa P1 de `docs/DIVISAO_TRABALHO.md` §3. Siga o ciclo de "Como trabalhar" do `CLAUDE.md`.

Leia: `docs/contrato/contrato-v3.md` §4 (4.1, 4.2, 4.3), §5, §6 (listas fechadas), §7.3–7.6, §10 (AC2, AC3);
`ContratoV3.java` (só leitura); `app/schemas.py`, `app/orchestrator.py`, `app/engines/*.py`.

Escopo:
1. `AnaliseResponse` com todos os campos do §4: obrigatórios os que o Java lê; opcionais `confianca`,
   `eventosConduta`, `versaoContrato`, `avisos`. Enums fechados: `motor` (llm1|llm2|local|regras),
   `sentimento` (minúsculas), 14 padrões, `tipos`, `regra` do compromisso, motivos de `descartados`.
2. `SaidaLLM`: só o que a LLM preenche, compatível com saída estruturada estrita da OpenAI
   (sem `dict` livre nem tuplas). `motor`, `tentativas`, `versaoContrato`, `descartados` ficam FORA dele.
3. Testes: cada fixture `resposta-v3-*.json` valida em `AnaliseResponse` (AC2); campos extras do pedido
   passam; valor de enum fora da lista é rejeitado; `model_json_schema(SaidaLLM)` não tem `additionalProperties` livre.
4. Mantenha o mock da P0 funcionando.

Não faça: prompt (P2), conferência de citação (P3), regex (P4). Não toque em `backend/`.
Campo da fixture que o schema não tem, ou o contrário: pare e mostre ao João Paulo antes de decidir.
Commit: `feat(P1): schemas Pydantic do contrato v3`.
