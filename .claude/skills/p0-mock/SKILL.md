---
name: p0-mock
description: Tarefa P0 — mock do contrato v3 no POST /analisar (PIPELINE_VERSAO=mock) e conftest que bloqueia rede. Desbloqueia o Kelwin.
disable-model-invocation: true
---
Tarefa P0 de `docs/DIVISAO_TRABALHO.md` §3 (Python). Siga o ciclo de "Como trabalhar" do `CLAUDE.md`.

Leia: `docs/contrato/contrato-v3.md` §3, §4, §8.1–8.3 e §10 (AC1, AC7, AC8); a tarefa P0 e P1 no
`DIVISAO_TRABALHO.md`; `ContratoV3.java` (só leitura) para conferir nomes e enums;
`analise-service/app/{main,router,schemas}.py` e `conftest.py` (hoje vazio).

Escopo:
1. `app/config.py` com `PIPELINE_VERSAO` (`real` | `mock`; padrão `real`; valor inválido = erro claro na subida).
2. Schema Pydantic v2 do PEDIDO v3 (`turnos[{n,locutor,texto}]` obrigatório e não vazio, `dataReuniao`,
   `padroes`, `contraexemplos`; aceita `contextoCliente`, `glossarioTime`, `correcoesAnteriores`).
   Pedido sem `turnos`, ou no formato v1 (`conteudo`), responde 422 `pedido_invalido` (§8.1).
3. Com `PIPELINE_VERSAO=mock`, `POST /analisar` valida o pedido e devolve SEMPRE o conteúdo de
   `docs/contrato/resposta-v3-llm.json`, com o header `X-Insightcall-Pipeline: mock`. Carregue o JSON
   de forma preguiçosa e com erro explícito se faltar.
4. `GET /health` no formato do §8.3 (pode devolver os motores como `ok: true` fixo por enquanto; P5 faz o real).
5. `conftest.py` que bloqueia socket em todo teste (nenhum teste chama rede), com um teste que prova o bloqueio.
6. Testes: AC1 (200 com `pedido-v3.json` e `pedido-v3-extras.json`; 422 sem `turnos`; 422 com `conteudo`),
   AC8 (a flag devolve a fixture e o header), AC7 (o app importa sem `.joblib` e sem chaves).

Não faça: motor real, prompt, conferência de citação, regex. Não toque em `backend/`.
Se o `orchestrator` atual (v1) quebrar por mudar o schema, isole-o atrás de `PIPELINE_VERSAO=real` em vez de reescrevê-lo (isso é P1/P2).
Commit: `feat(P0): mock do contrato v3 e flag PIPELINE_VERSAO`.
Ao final: diga ao João Paulo como o Kelwin chama o mock (comando `curl` pronto).
