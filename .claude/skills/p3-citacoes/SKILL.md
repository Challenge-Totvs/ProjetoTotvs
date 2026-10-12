---
name: p3-citacoes
description: Tarefa P3 — conferir_citacoes (normalização, janelas de 2-3 turnos, vizinhos ±2, turno/turnoFim, descartados). Pode rodar em paralelo à P2, depois da P1.
disable-model-invocation: true
---
Tarefa P3 de `docs/DIVISAO_TRABALHO.md` §3. Ciclo do `CLAUDE.md`.

Leia: `docs/contrato/contrato-v3.md` §7.2 (regras completas), §6.7, §10 (AC4); `docs/SDD.md` §5.7 e §12 (plano de testes);
`app/schemas.py`.

Escopo: função pura `conferir_citacoes(turnos, itens)` em `app/citacoes.py`, sem I/O, aplicada a
`temas[].texto`, `interesse[].citacao`, `compromissos[].texto` e `eventosConduta[].texto`.
1. Normalizar os dois lados (NFC, aspas e travessões tipográficos, reticências, espaços, ignorar maiúsculas, acentos intactos).
2. Buscar no turno indicado; depois janelas de 2 e 3 turnos consecutivos; depois n−2..n+2, do mais próximo ao mais distante.
3. Acerto: corrigir `turno` e preencher `turnoFim`; gravar o texto do turno recebido (não o normalizado).
4. Sem acerto: `descartados` com `evidencia_nao_localizada`; tamanho < 10 → `trecho_curto`; > 600 → `trecho_longo`.
5. Testes (escreva primeiro): acerto exato; diferença de espaços e aspas; maiúsculas; turno errado mas vizinho;
   trecho que cruza dois turnos; inexistente; curto; longo; alucinação parecida (uma palavra trocada deve ser descartada).
   Use as fixtures: toda citação de `resposta-v3-llm.json` deve ser confirmada contra `pedido-v3.json`.

Não faça: integrar ao orquestrador (isso é P2/P4/P5 usando a função). Não toque em `backend/`.
Commit: `feat(P3): conferencia de citacoes literais`.
