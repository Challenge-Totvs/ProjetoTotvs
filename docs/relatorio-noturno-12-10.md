# Relatório do lote noturno — 12/10/2026

Lote sem supervisão, autorizado a seguir sem aprovação de plano. Plano de cada item escrito aqui antes de implementar.
Sem texto de transcrição neste arquivo. Commits em nome de Joao, sem linhas de coautoria/atribuição.

Baseline do pytest no início do lote (`analise-service/.venv`): `282 passed in 7.67s`.

## Item 0 — CLAUDE.md: regra de commits
**Plano:** acrescentar a regra 12 às regras invioláveis; commitar junto com a edição já pendente do João no mesmo
parágrafo ("*SEM* co-author"), que trata do mesmo assunto.
**Status:** concluído.
Commit: `d157256 docs: regra de commits`.

## Item 1 — Smoke e cliente LLM
**Plano:** (a) `ErroMotor` ganha `status_http` e `tipo_provedor` (diagnóstico, nunca vai à resposta da API);
`llm_engine.diagnostico_do_provedor(e)` lê `status_code` e o tipo (`.type`, ou `body.error.type` da Anthropic /
`body.type` da OpenAI), aceitando só identificadores `[a-z0-9_]`; o smoke imprime `http` e `tipo_erro_provedor`.
(b) `config.workspace_llm1()` lê `LLM_PRINCIPAL_WORKSPACE_ID`; se definida, o cliente Anthropic recebe
`default_headers={"anthropic-workspace-id": ...}` (forma suportada pelo SDK 1.11); senão os kwargs não mudam. Cache de
clientes passa a considerar o workspace. Variável comentada no `.env.example`; `conftest.py` a remove em todo teste.
(c) O script `gerar_pedido_sintetico.py` (commit 43bb307, de hoje à noite) já fazia quase tudo; foi renomeado para
`gerar_transcricao_sintetica.py` e reescrito: fundo só com frases neutras, frases-modelo dos 14 padrões plantadas.
(d) `smoke_llm.py` passa a usar argparse, com `--entrada` (e `--pedido` como sinônimo, para não quebrar o uso de ontem).
**Status:** concluído. Suíte: 307 passed.
**Commits:**
- `d178946 feat(smoke): codigo HTTP e tipo do erro do provedor na falha`
- `6f6aedd feat(llm1): LLM_PRINCIPAL_WORKSPACE_ID opcional envia anthropic-workspace-id`
- `d4c6192 feat(smoke): gerar_transcricao_sintetica com temas plantados (P90 padrao)`
- `f187b45 feat(smoke): --entrada para a transcricao sintetica e padroes confirmados no resumo`

**Testes:** 401 (`authentication_error`), 404 (`not_found_error`), 403 (`permission_error`), 400 da OpenAI
(`invalid_request_error`), tipo com texto livre bloqueado, erro sem status, diagnóstico fora da resposta da API;
workspace presente/ausente/vazio, não afeta a OpenAI, troca de workspace recria o cliente, smoke mostra só
"definido/ausente"; gerador respeita 3k/20k/72k caracteres (até +600), as 14 frases casam com o próprio padrão, o fundo
não casa com nenhum padrão nem com interesse, `regras` acha exatamente os plantados; `--entrada`, padrão e motor inválido.

**Como usar amanhã:**
```
cd analise-service
python scripts/smoke_llm.py llm1                     # pedido curto do contrato
python scripts/smoke_llm.py --entrada tests/fixtures/transcricao-sintetica-p90.json   # pior caso (~72 mil caracteres)
```
A fixture P90 (399 turnos, 72.062 caracteres, ~21 mil tokens) tem plantados: treinamento (t40), cancelamento_citado
(t85), renovacao (t129), preco_objecao (t174), suporte_insatisfacao (t308), integracao (t353), mais 2 interesses.
Compare com `padroes_confirmados` do resumo do smoke.

**Decisões para validar (item 1):**
- 1-D1: renomeei `gerar_pedido_sintetico.py` em vez de manter dois geradores; `--pedido` continua aceito.
- 1-D2: a saída padrão é `tests/fixtures/transcricao-sintetica-p90.json` e ela foi VERSIONADA (sintética,
  determinística, ~98 KB) para o comando de amanhã funcionar sem gerar nada. O antigo `dados_locais/pedido-p90.json` não
  foi tocado.
- 1-D3: seis padrões plantados por padrão (3 risco, 3 oportunidade), de 10% a 90% da reunião; `--padroes` muda.
- 1-D4: o resumo do smoke ganhou `padroes_confirmados` (só nomes de padrão) para conferir os plantados.
- 1-D5: a regra 9 do CLAUDE.md proíbe mexer em `.env*`; editei `.env.example` só porque o lote pediu explicitamente.
