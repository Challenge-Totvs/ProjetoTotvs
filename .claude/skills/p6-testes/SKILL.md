---
name: p6-testes
description: Tarefa P6 — testes do orquestrador (cenários 2 a 4) e do contrato; fecha a suíte e confere as fixtures contra o Java. Rode por último (depois de P2 a P5).
disable-model-invocation: true
---
Tarefa P6 de `docs/DIVISAO_TRABALHO.md` §3. Ciclo do `CLAUDE.md`.

Leia: `docs/contrato/contrato-v3.md` §9 (compatibilidade com o Java), §10 (AC1 a AC10); `docs/SDD.md` §12;
`ContratoV3.java` (só leitura); `analise-service/tests/`.

Escopo:
1. Mapeie cada AC1..AC10 a um teste existente; crie os que faltam. Mostre a tabela AC -> teste no resumo.
2. Cenários do orquestrador (SDD §12): llm1 ok; llm1 falha -> llm2; duas fora -> local; tudo fora -> 503; llm lenta
   estoura o prazo total de 100 s (use relógio simulado, sem `sleep` real).
3. Teste de contrato: cada fixture `resposta-v3-*.json` valida em `AnaliseResponse`; os enums do Python batem com os de
   `MotorUtilizado.java` e `SentimentoGeral.java` (leia os arquivos Java no teste só para comparar valores, ou liste
   os valores esperados em constantes e aponte a origem em comentário).
4. `python -m pytest -q` verde, sem rede e sem chaves, em menos de 30 s.
5. Relatório final: lista de pendências abertas do §12 do contrato e o que o Kelwin precisa fazer (teste Java lendo
   as fixtures, AC9; atualizar SDD §6.2, A10).

Não corrija código de produção além do necessário para o teste revelar um bug: se achar bug, pare e descreva.
Commit: `test(P6): suite do orquestrador e do contrato`.
