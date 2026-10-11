---
name: p5-health
description: Tarefa P5 — /health com o estado de cada motor, motor e tentativas na resposta, erros 422/503/500 estruturados. Rode depois da P1.
disable-model-invocation: true
---
Tarefa P5 de `docs/DIVISAO_TRABALHO.md` §3. Ciclo do `CLAUDE.md`.

Leia: `docs/contrato/contrato-v3.md` §8.1–8.3 e `docs/contrato/health.json`, `erro-422.json`, `erro-503.json`;
`MotorStatusService.java` e `StatusMotores.java` (só leitura) para o formato que o Java repassa;
`app/router.py`, `app/orchestrator.py`.

Escopo:
1. `GET /health` -> `{"status","pipelineVersao","motores":[{"motor","ok"}]}` com llm1, llm2, local, regras.
   `ok` de llm1/llm2 = chave e modelo configurados; `local` = artefato existe e carrega (sem carregar no import);
   `regras` = sempre true. NUNCA chame a API da LLM no `/health`. Sem chaves e sem `.joblib`, responde 200.
2. Erros no formato do §8.1: 422 `pedido_invalido`/`padrao_desconhecido`, 503 `analise_indisponivel`
   (com `tentativas`), 500 `erro_interno`. Sem stack trace nem texto de transcrição no corpo.
3. `motor` e `tentativas` sempre preenchidos pelo código.
4. Testes: AC7 e os formatos de erro contra as fixtures.

Pendência A9 (503 vs 500 quando a análise falha): siga o §8.1 e registre em `docs/decisoes.md` se algo divergir do Java.
Commit: `feat(P5): health por motor e erros estruturados`.
