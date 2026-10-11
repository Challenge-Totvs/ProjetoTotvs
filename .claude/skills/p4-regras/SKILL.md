---
name: p4-regras
description: Tarefa P4 — regex por padrão de volta na cadeia (motores local e regras), modelo local contribuindo com score e interesse, split por turno. Rode depois da P1 e da P3.
disable-model-invocation: true
---
Tarefa P4 de `docs/DIVISAO_TRABALHO.md` §3. Ciclo do `CLAUDE.md`.

Leia: `docs/contrato/contrato-v3.md` §5 (matriz campo × motor), §6.1 (os 14 padrões), §7.2, §10 (AC6),
A5/A8 em §12; `docs/SDD.md` §6.1 e §6.3; `app/engines/modelo_local_engine.py`, `app/orchestrator.py`, `app/schemas.py`.

Escopo:
1. `app/engines/regras_engine.py`: uma expressão regular por padrão (os 14). Cada acerto vira `Tema` com `padrao`,
   `titulo`, `tipos`, `turno`, `texto` (recorte do próprio turno), `tratado` nulo e SEM `confianca`.
   Passe os acertos por `conferir_citacoes` (P3), que apenas confirma.
2. `motor = regras`: score = proporção de sinais positivos (50 se não houver sinal); `sentimento` por limiares 70/45
   (proposta; deixe constantes nomeadas). `motor = local`: o classificador sklearn contribui com `score` e `interesse`;
   os temas vêm das regex. O mapeamento classificador -> 14 padrões é Release 2: NÃO o faça.
3. Divisão em trechos por TURNO (decisão A5 "por ora"): o modelo local deixa de falhar em silêncio com turnos numerados.
   Carga preguiçosa do `.joblib` com erro explícito (`avisos`: `contingencia_modelo_local`).
4. Orquestrador: llm1 -> llm2 -> local -> regras -> 503, com `tentativas`.
5. Testes: um por padrão com UMA transcrição sintética curta (crie em `tests/fixtures/`); cadeia com LLMs simuladas fora
   devolve `motor = local` ou `regras` com temas; sem `.joblib` cai para `regras`; todos fora = 503 `analise_indisponivel`.

Pendência A8: o conteúdo das 14 expressões precisa de revisão do João Paulo. Implemente uma primeira versão e liste
cada expressão em uma tabela no resumo final para ele aprovar.
Não faça: retreino, spaCy, mudança em `backend/`. Commits por assunto: `feat(P4): ...`.
