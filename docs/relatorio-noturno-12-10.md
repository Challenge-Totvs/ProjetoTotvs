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

## Item 2 — P7: `POST /similares`
**Plano:** (1) contrato `docs/contrato/similares.md`, marcado PROPOSTA no topo, e fixtures sintéticas
`pedido-similares.json`/`resposta-similares.json`; (2) `app/similares.py` com `TfidfVectorizer` ajustado por pedido
(minúsculas, sem acento, `ngram_range=(1, 2)`, `sublinear_tf=True`), cosseno, `LIMIAR_SIMILARIDADE` nomeado, sklearn
importado só no uso; (3) schemas `PedidoSimilares`/`RespostaSimilares` em `schemas.py` e rota no `router.py`, 422 pelo
handler existente; (4) testes sintéticos.
**Status:** concluído. Suíte: 334 passed.
**Commits:** `3541e1e docs(P7): contrato PROPOSTO do /similares e fixtures` · `46b2ba0 feat(P7): POST /similares (TF-IDF, sem API)`.
**Testes (27):** quase igual casa (>0,8); acento/maiúsculas; assuntos diferentes não casam; ordem decrescente; `topK`
(e padrão 3); limiar do pedido; sem referências; sem vocabulário útil; score 0 nunca volta; texto vazio/só espaços/ausente
=> 422; 200 vs 201 referências; `topK`/`limiar` fora dos limites; referência sem id/texto; 422 sem texto do pedido;
resposta == fixture; campos extras ignorados; sem estado entre pedidos; log só com tamanhos; responde também em `mock`;
sem rede; importar o app não carrega sklearn.

**Decisões para validar (item 2):**
- 2-D1: `LIMIAR_SIMILARIDADE = 0.2`. Com frases sintéticas, paráfrases do mesmo assunto ficaram entre ~0,2 e ~0,35 e
  assuntos diferentes até ~0,14 (TF-IDF de palavras pega pouca paráfrase; char n-grams pegariam mais, mas a skill pede
  palavras 1-2). Calibrar com o ouro.
- 2-D2: lista curta de stop words do português (~90 palavras) como constante em `app/similares.py`; sem ela, "que",
  "para", "com" inflavam o score.
- 2-D3: limites que a skill não fixava: `topK` 1..50, `id` 1..100 caracteres, `texto` de referência 1..2000, texto com
  espaços nas pontas é aparado (só espaços => 422 `vazio`). Score com 4 casas; score 0 nunca volta (mesmo com
  `limiar: 0`); empate mantém a ordem de chegada; `id` repetido não é erro.
- 2-D4: `/similares` responde igual em `PIPELINE_VERSAO=mock` (não usa LLM) e não leva o cabeçalho `X-Insightcall-Pipeline`.
- 2-D5: o 422 reaproveita o handler global, então a `mensagem` é "O pedido não segue o contrato v3." também aqui.

**Pendências (P7):** validação do contrato (João + Kelwin); cliente Java, campo `semelhanteNaoProcede` e ignorar falha
em silêncio (Kelwin); calibração do limiar com o ouro (P8).

## Item 3 — P8: pipeline de retreino (etapas 1 a 6)
**Plano (escrito antes de implementar):**
- Pasta `analise-service/treino/` (pacote, para os testes importarem), um script por etapa, todos com `--help`,
  imprimindo só contagens/métricas. `treino/comum.py`: caminhos (`dados_locais/`), leitura de turnos pela regra do SDD
  §5.2 (`[LOCUTOR n]`), grupos (risco/oportunidade a partir de `regras_engine.TIPO_DO_PADRAO`), normalização de rótulos,
  hash de arquivo, escrita de CSV. Nenhum dado real é lido por mim; testes só com dados sintéticos em `tmp_path`.
- **1. `extrair_trechos.py`**: lê o CSV do corpus (nomes de coluna configuráveis: `--col-reuniao`, `--col-cliente`,
  `--col-texto`, porque o formato real não está documentado no repo) e o `holdout_reunioes.csv`; exclui as reuniões do
  holdout E todas as reuniões dos clientes (CODT) que aparecem no holdout; divide por turno; grava `trechos.csv`
  (id `reuniao:turno`, reunião, cliente, turno, locutor, texto do turno alvo, contexto = 2 turnos anteriores).
  `--verificar` imprime só os NOMES das colunas e a contagem de linhas, para o João conferir os nomes antes.
- **2. `rotulos_fracos.py`**: (a) regra: `regras_engine` como fonte única (risco/oportunidade = alguma expressão do
  tipo casa no turno alvo; interesse = `EXPRESSAO_INTERESSE`, sem veto). (b) `--destilar`: amostra de ~3.000 candidatos
  (70% com algum acerto de regra, 30% sem, semente fixa), lotes de 20 trechos por chamada a UMA LLM (`--motor llm1|llm2`,
  credenciais do `.env` via `app.config`), saída estruturada `{id, risco, oportunidade, interesse}`, texto neutralizado
  (`llm_engine.neutralizar`). Exige `--teto-usd` (máx. 2) e os preços por milhão de tokens (`--preco-entrada`,
  `--preco-saida`, sem preço embutido no código); para ANTES de um lote que possa estourar o teto; cache JSONL e gasto
  acumulado em disco, retoma de onde parou. A chamada é injetável: os testes usam cliente simulado. Saída
  `rotulos_fracos.csv` (regra + destilação; rótulo de treino = LLM quando houver, senão regra).
- **3. `conciliar_ouro.py`**: `--modo unico` (padrão): metade A obrigatória, B opcional ("parcial" sem ela); reteste
  (`ouro_reteste_PRONTO.xlsx` + `reteste_mapa.csv`) => kappa de Cohen teste-reteste para `padrao` e `interesse`.
  `--modo pares`: 4 planilhas (1-2 = metade A, 3-4 = metade B), kappa por par e campo, `divergencias.xlsx` para
  arbitragem; com `divergencias_PRONTO.xlsx` aplica a arbitragem e grava o ouro. Kappa < 0,6 => aviso explícito. Grava
  `ouro_final.csv` + `ouro_final.json` (modo, completo/parcial, kappas) e um relatório só com métricas. Colunas das
  planilhas por nome de cabeçalho (configuráveis); `--verificar` imprime só cabeçalhos e contagens.
- **4. `treinar.py`**: `sklearn.base.clone` do Pipeline de `app/modelos/classificador_risco.joblib` (D17: herda os
  hiperparâmetros e as 315 stop words) para o risco E para o interesse (mesma família). Só rótulos fracos, só reuniões
  fora do holdout; aborta se algum id/reunião do ouro aparecer no treino. `--param chave=valor` exige `--justificativa`
  e fica registrado. Salva `dados_locais/candidatos/<data>/{risco,interesse}.joblib` + `metadata.json` (data, sha256
  dos dados, versão do sklearn, tamanhos, positivos, hiperparâmetros escalares, mudanças).
- **5. `portao.py`**: no `ouro_final.csv` (sem as linhas com `duvida`), por grupo: risco (classificador atual × candidato,
  limiar `LIMIAR_RISCO`), interesse (filtro atual = regex v2 + risco < 0,3 × candidato com `LIMIAR_P_INTERESSE`),
  oportunidade (regex nos dois: informativo). Precisão, revocação, F1, IC95% por bootstrap da diferença de F1. Aprova
  por modelo: F1 cand >= F1 atual E precisão não cai > 0,02 E IC95% não inteiramente < 0. Ouro parcial => nunca
  recomenda promoção. Escreve `docs/evidencias/portao-<data>.md` (só métricas, declara modo e parcial/completo, avisa que
  por padrão é indicativo) e imprime o comando de promoção manual ou "REPROVADO: mantém o atual".
- **6. Encaixe em `modelo_local_engine`**: `config.interesse_modelo_ligado()` (ausente = "0" = desligado) e
  `config.CAMINHO_MODELO_INTERESSE = app/modelos/classificador_interesse.joblib` (nunca `dados_locais/`).
  `prever_interesse(trechos: list[(n, texto NFC)]) -> dict[n, p] | None`; `None` = usar o filtro atual (flag desligada,
  artefato ausente, falha ao carregar ou exceção na predição, com log só do tipo). Com p, interesse = turnos com
  `p >= LIMIAR_P_INTERESSE` (até 20, maiores p), citação = turno (recorte <= 600) via `conferir_citacoes`. Flag NÃO entra
  no `.env` nem no `.env.example`.

**Status:** concluído (etapas 1 a 6). Suíte: 414 passed. Nenhum dado real lido; nada criado em `dados_locais/` nem em
`docs/evidencias/` pelos testes (tudo em `tmp_path`).
**Commits:**
- `27d3b4c feat(P8): extrair trechos fora do holdout`
- `8facdee feat(P8): rotulos fracos por regra e destilacao com teto`
- `ba389e7 feat(P8): conciliar ouro nos modos unico e pares, kappa teste-reteste`
- `3d8f89a feat(P8): treinar candidatos de risco e interesse por clone do classificador atual (D17)`
- `234ac12 feat(P8): encaixe do classificador de interesse no motor local, desligado por padrao` (etapa 6)
- `493b85d feat(P8): portao com metricas por grupo e IC95 por bootstrap` (etapa 5; commitada depois da 6 porque
  importa `LIMIAR_P_INTERESSE` do motor local)

**Testes (72 novos):** etapa 1 (regra do SDD §5.2, exclusão por reunião E por cliente do holdout, contexto de 2 turnos,
`--verificar`, coluna errada); etapa 2 (regra = `regras_engine`, amostra 70/30 determinística, cache e retomada sem
pagar de novo, teto nunca ultrapassado mesmo com estimativa otimista, teto fora de (0, 2] recusado, item sem resposta
não é repetido, erro do provedor só com código, prompt neutralizado, rótulo da LLM prevalece, chamada real simulada nos
dois provedores); etapa 3 (kappa, único parcial/completo, reteste, aviso de kappa < 0,6, inválidos só contados, pares
com arbitragem em dois passos, 4 rotuladores, colunas com outros nomes); etapa 4 (clone herda todos os parâmetros e as
stop words, base intacta, `--param` exige justificativa, holdout/ouro no treino abortam, classe única, não sobrescreve;
clone do artefato REAL confere D17: 315 stop words, `min_df=5`, `max_df=0.6`); etapa 5 (métricas, bootstrap pareado e
determinístico, as 5 situações da regra de aprovação, ouro parcial/sem meta nunca promove, reprovação, dúvida fora,
pipeline 1→5 ponta a ponta); etapa 6 (abaixo). Todo script tem teste de `--help`.

**Etapa 6 — o que foi testado:** com `INTERESSE_MODELO` não setado, o fallback é sempre usado, mesmo com um
`interesse.joblib` de candidato em `dados_locais/candidatos/` (sintético, em `tmp_path`) e até com um artefato válido no
caminho promovido — o artefato nem é carregado; valores diferentes de "1" ("0", "", "true", "sim") = desligado; com "1"
e artefato sintético carregável o modelo é chamado e substitui o filtro; com "1" e artefato ausente, corrompido ou que
lança exceção na predição, cai no filtro atual sem derrubar o motor (log só com o tipo). O `conftest.py` remove
`INTERESSE_MODELO` em todo teste; nenhum teste de produção liga a flag. Teste garante que a flag não está no
`.env.example`.

### Comandos que o João roda nos dados reais (nesta ordem, a partir de `analise-service/`)
Coloque em `dados_locais/`: o CSV do corpus, `holdout_reunioes.csv` e as planilhas `*_PRONTO.xlsx`.
```
# 0. dependência de treino (já instalada no .venv): pip install -r requirements-treino.txt
# 1. trechos (confira os nomes de coluna ANTES; o --verificar só imprime cabeçalhos e contagens)
python treino/extrair_trechos.py --corpus dados_locais/<corpus>.csv --verificar
python treino/extrair_trechos.py --corpus dados_locais/<corpus>.csv --col-reuniao <col> --col-cliente <CODT> --col-texto <col> [--col-holdout <col>]
# 2. rótulos fracos: primeiro só regra (sem custo)...
python treino/rotulos_fracos.py
#    ...e, com a chave de desenvolvimento, a destilação (confira os preços do modelo barato na página do provedor)
python treino/rotulos_fracos.py --destilar --motor llm2 --modelo <modelo-barato> --teto-usd 2 --preco-entrada <US$/Mtok> --preco-saida <US$/Mtok>
#    (pode rodar de novo: retoma do cache em dados_locais/destilacao/ e respeita o gasto acumulado)
# 3. ouro (depois da metade A; de novo quando a B e o reteste estiverem prontos)
python treino/conciliar_ouro.py --verificar
python treino/conciliar_ouro.py [--col-texto <coluna com a fala ALVO>] [--col-id ...]
# 4. treino dos candidatos (depois do passo 3, para conferir que o ouro não vazou para o treino)
python treino/treinar.py
# 5. portão
python treino/portao.py
# 6. só se o portão imprimir "APROVADO" (exige ouro completo): rodar o Copy-Item impresso, rodar a suíte e commitar.
```
**`INTERESSE_MODELO=1` no `.env` só deve ser acrescentado DEPOIS** que o pipeline rodar nos dados reais, o `portao.py`
aprovar o candidato real de interesse com o ouro completo e o artefato for promovido para
`app/modelos/classificador_interesse.joblib`. Até lá a variável fica AUSENTE (= desligado) e o motor `local` se
comporta exatamente como hoje.

**Contingência (P8):** sem chaves, rode só o passo 2 sem `--destilar`: o modelo de interesse tende a reproduzir a regra
(demonstra pipeline e portão, não ganho). Só a metade A rotulada: o portão roda, marca "PARCIAL" e não recomenda
promoção.

**Decisões para validar (item 3):**
- 3-D1: nomes de coluna do corpus e das planilhas não estão no repo; padrões `reuniao`/`CODT`/`transcricao` e
  `id`/`texto`/`padrao_1`/`padrao_2`/`interesse`/`duvida`, todos configuráveis, com `--verificar`. O cabeçalho da planilha
  pode estar em qualquer uma das 10 primeiras linhas. A planilha precisa ter a fala ALVO numa coluna (é o que o portão
  avalia).
- 3-D2: exclusão do holdout = reuniões listadas E todas as reuniões dos clientes delas (CODT do holdout ou do corpus).
- 3-D3: destilação: amostra 70% com acerto de regra / 30% sem; lotes de 20; contexto e fala alvo cortados em 1.500
  caracteres; `--motor llm2` por padrão; preços por CLI (nada embutido); teto máximo 2,0 recusado acima (D14);
  estimativa por lote = pior caso (saída = `max_tokens` 4.000, entrada = caracteres/3,4, margem 1,5) e nunca abaixo do
  lote mais caro já pago; item sem resposta fica no cache como falha e não é pago de novo. Risco residual: o 1º lote
  custar mais que o teto inteiro (irrelevante com preços de modelo barato).
- 3-D4: rótulo de treino = o da LLM quando houver, senão o da regra.
- 3-D5: kappa só para `padrao` (= `padrao_1`, categórico) e `interesse`; no modo pares a divergência também olha
  `padrao_2`; `duvida` de qualquer um dos dois marca o trecho; valores inválidos são só contados (nunca impressos).
- 3-D6: os relatórios do ouro e do portão vão para `docs/evidencias/ouro-<data>.md` e `portao-<data>.md` (só métricas).
- 3-D7: o candidato de interesse também é `clone` do Pipeline atual (mesma família e hiperparâmetros).
- 3-D8: o treino aborta se uma reunião do holdout ou um id do ouro estiver nos rótulos; texto idêntico ao do ouro
  (>= 40 caracteres) só é contado no `metadata.json`.
- 3-D9: portão: trechos com `duvida` ficam de fora; oportunidade é só informativa (regex dos dois lados); decisão por
  modelo (risco e interesse separados); sem `ouro_final.json` conta como parcial; candidato sem positivos no ouro não é
  aprovado; o comando de promoção é `Copy-Item` (PowerShell); bootstrap com 2.000 reamostragens pareadas, semente 42.
- 3-D10: `LIMIAR_P_INTERESSE = 0.5` [proposta]; com o modelo ligado o interesse NÃO tem veto de risco (o modelo
  substitui o filtro inteiro), até 20 turnos de maior p, texto "Sinal de interesse (modelo local)", citação = o turno
  (até 600 caracteres) conferida por `conferir_citacoes`.
- 3-D11: a flag só liga com o valor exato "1" (espaços nas pontas ignorados).

**Pendências (P8):** validar a "professora" (LLM da destilação) contra o ouro antes de confiar nos rótulos fracos
(o escopo §3 pede; não há script para isso ainda — dá para fazer com `--amostra` restrita aos ids do ouro numa próxima
sessão); calibrar `LIMIAR_P_INTERESSE`, o veto 0,3 e o `LIMIAR_SIMILARIDADE` com o ouro; promover candidatos só por
decisão manual do João.
