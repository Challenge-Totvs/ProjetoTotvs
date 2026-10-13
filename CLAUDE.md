# InsightCall — ProjetoTotvs (Challenge TOTVS 2026, FIAP)

Recebe transcrições de reuniões comerciais e devolve análise: temas de risco e
oportunidade com citação literal, score, sentimento e próximos passos.
Prazos: banca TOTVS 15/10/2026 (define o top 4 para o Next, 24/10) · entrega FIAP
21/10/2026 (secundária). O produto continua depois do Challenge: releases contínuas.

## Mapa do repositório
- `analise-service/` — Python/FastAPI, motores de análise (João Paulo). Tem o próprio `CLAUDE.md`.
- `backend/` — Java/Spring (Kelwin). Consome `POST /analisar`.
- `frontend/` — React (Kelwin).
- `docs/contrato/` — `contrato-v3.md` e as fixtures JSON. Fonte única do contrato.
- `docs/SDD.md` (v3.0) e `docs/DIVISAO_TRABALHO.md` (tarefas P0–P6 e prazos).

## Contrato
O formato é o de `docs/contrato/contrato-v3.md` e das fixtures. O Java é a referência: o Python se alinha a ele.
Mudou campo? Atualize doc e fixture ANTES do código e avise João Paulo, que avisa o Kelwin.

## Estado atual (13/10)
P0 a P6, P7, P8 e P9 estão commitados na branch `analise-service(joao)`: o Python fala o contrato v3, a cadeia real
roda e o `/health` usa a última tentativa real (`FORCAR_FALHA` para a demo). Smokes das duas LLMs ok e prompt validado
com LLM real (P90: llm1 8,7 s, llm2 17,4 s; timeout do Java fica em 120 s). Ensaio de falha ao vivo registrado em
`docs/evidencias/ensaio-falha-13-10.md`. Dados reais: extração ok (233.267 trechos fora do holdout), amostra nova para o
ouro (283 trechos, fora dos 300) e piloto de destilação com `claude-haiku-5-5` (300 trechos, US$ 0,0162). Falta:
rotular e conciliar o ouro, rodar o P9 no ouro real, depois treino e portão.

## Arquitetura
router -> orchestrator -> cadeia: llm1 (Anthropic) -> llm2 (OpenAI) -> local
(classificador sklearn + regex por padrão) -> regras (só regex) -> 503 estruturado.
Os quatro motores existem e o contrato v3 vale ponta a ponta. O Java espera no máximo 120 s.

## Regras de dados e de commit
11. Fixtures e transcrições de teste são SINTÉTICAS. Nunca commite trecho do corpus da TOTVS.
12. Commits e PRs sem linhas de coautoria ou de atribuição automática.

- Dados reais ficam só em `analise-service/dados_locais/` (ignorado pelo git). O corpus `ANON_nome_transcricao.csv` é
  anonimizado pela TOTVS (decisão do João Paulo, 12/10): pode-se ler cabeçalhos e amostras dele para depurar.
- Continua proibido: commitar trechos (regra 11), pôr texto de transcrição em log ou relatório (só tamanhos, ids,
  contagens e métricas), abrir `*_PRONTO.xlsx` e `ouro_final.csv` (o ouro mede, não calibra).

## Ler sob demanda (não carregue inteiro)
- `docs/contrato/contrato-v3.md`: §3 pedido · §4 resposta · §7.2 citações · §8 erros e health
- `docs/DIVISAO_TRABALHO.md` §3 (tabela de tarefas) · `docs/SDD.md` §5.7, §6, §12
- Decisões e pendências: `docs/decisoes.md`
