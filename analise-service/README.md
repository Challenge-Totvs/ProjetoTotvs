# analise-service (InsightCall)

Serviço Python/FastAPI que recebe a transcrição de uma reunião comercial (já numerada e pseudonimizada pelo Java) e
devolve temas de risco e oportunidade com citação literal, score, sentimento e próximos passos. Contrato:
`docs/contrato/contrato-v3.md` (fonte única) e `docs/contrato/similares.md` (PROPOSTA).

## Subir

```
cd analise-service
python -m venv .venv && .venv\Scripts\activate        # Windows (no Linux/macOS: source .venv/bin/activate)
pip install -r requirements.txt                         # scikit-learn==1.9.1 é pinado de propósito
uvicorn app.main:app --reload --port 8000
```
O app sobe sem chaves e sem o `.joblib` (cada motor que faltar só aparece como `ok: false`). Ele lê
`analise-service/.env` se existir, sem sobrescrever variáveis já definidas no ambiente.

## Variáveis de ambiente (só em `.env`; nunca versionar)

| Variável | Significado |
|---|---|
| `LLM_PRINCIPAL_API_KEY`, `LLM_PRINCIPAL_MODEL` | Chave e modelo da Anthropic (motor `llm1`) |
| `LLM_PRINCIPAL_WORKSPACE_ID` | Opcional. ID do workspace da Anthropic: envia o cabeçalho `anthropic-workspace-id`. Ausente = nada muda |
| `LLM_SECUNDARIA_API_KEY`, `LLM_SECUNDARIA_MODEL` | Chave e modelo da OpenAI (motor `llm2`) |
| `LLM_*_PROVIDER` | Informativas no `.env.example`; o código não as lê (llm1 = Anthropic, llm2 = OpenAI) |
| `PIPELINE_VERSAO` | `real` (padrão) ou `mock`. Valor inválido impede a subida |
| `FORCAR_FALHA` | Lista de motores que falham de propósito, ex. `llm1,llm2` (só para a demo). Vazia por padrão |
| `INTERESSE_MODELO` | Liga o classificador de interesse no motor `local` com o valor `1`. **Fica AUSENTE até o candidato real ser aprovado pelo portão e promovido** (ausente = desligado = comportamento atual) |
| `INSIGHTCALL_IGNORAR_DOTENV` | Usada pelos testes: não lê o `.env` real |

## Cadeia de motores (`POST /analisar`)

`llm1` (Anthropic) -> `llm2` (OpenAI) -> `local` (classificador sklearn + expressões por padrão) -> `regras` (só
expressões) -> 503 `analise_indisponivel`. O primeiro que responder vence; `motor`, `tentativas`, `versaoContrato` e
`descartados` são escritos pelo código, nunca pela LLM. Toda citação é conferida contra o texto recebido (contrato
§7.2); o que não for literal vai para `descartados`. Prazo compartilhado por pedido: llm1 ~55 s, llm2 ~35 s, total
<= 100 s (o Java espera 120 s). Clients com `timeout` explícito e `max_retries=0`.

- `PIPELINE_VERSAO=mock`: valida o pedido e devolve sempre `docs/contrato/resposta-v3-llm.json` (rollback sem LLM).
  Toda resposta leva o cabeçalho `X-Insightcall-Pipeline: real|mock`.
- `FORCAR_FALHA=llm1`: a cadeia registra falha `erro_provedor` do motor sem chamar a API, e o `/health` mostra
  `ok: false` na hora. Lida a cada pedido (pode ir no `.env`).

## `GET /health`

`{status, pipelineVersao, motores: [{motor, ok}]}`. `ok` = motor configurado E a última tentativa REAL dele não falhou
nos últimos 5 minutos (memória do processo; reinício zera). `status`: `ok` (alguma LLM ok), `degradado` (só
`local`/`regras`), `indisponivel`. Nunca chama a API de uma LLM.

## `POST /similares` (PROPOSTA, RAG-lite)

`{texto, referencias: [{id, texto}], topK?, limiar?}` -> `{similares: [{id, score}], versaoContrato: "v3"}`. Cosseno
TF-IDF ajustado a cada pedido (sem estado, sem API), `LIMIAR_SIMILARIDADE = 0.2` ainda não calibrado. Lista vazia é
resposta válida; o Java ignora falha deste endpoint em silêncio. Detalhes em `docs/contrato/similares.md`.

## Testes e smoke

```
python -m pytest -q                         # tudo; nenhum teste chama rede ou usa chave (conftest bloqueia sockets)
python -m pytest tests/test_p7_similares.py -q
python scripts/smoke_llm.py llm1            # MANUAL, com chave de desenvolvimento: imprime só contagens e tempos
python scripts/smoke_llm.py --entrada tests/fixtures/transcricao-sintetica-p90.json   # pior caso (~72 mil caracteres)
python scripts/gerar_transcricao_sintetica.py --caracteres 72000 --saida <arquivo>     # gera outra transcrição sintética
```
Em falha, o smoke imprime o código do contrato, o HTTP e o tipo do erro do provedor (`authentication_error`,
`not_found_error`...), nunca a mensagem, a chave ou texto. O prompt só conta como validado depois do smoke real
registrado em `docs/evidencias/`.

## Retreino do modelo local (P8, offline)

Scripts em `treino/`, um por etapa, todos com `--help`, imprimindo só contagens e métricas. Dependência só de treino:
`pip install -r requirements-treino.txt` (openpyxl). Ordem:

1. `treino/extrair_trechos.py` — trechos por turno, fora do holdout (por reunião e por cliente/CODT).
2. `treino/rotulos_fracos.py` — rótulo por regra (`regras_engine`); `--destilar` usa UMA LLM barata com `--teto-usd`
   (máx. 2), cache e retomada.
3. `treino/conciliar_ouro.py` — conjunto ouro (`--modo unico` ou `pares`), kappa, `ouro_final.csv`.
4. `treino/treinar.py` — candidatos de risco e interesse por `clone` do classificador atual (D17).
5. `treino/portao.py` — candidato × atual por grupo, IC95% por bootstrap; imprime o comando de promoção MANUAL ou
   "REPROVADO: mantém o atual". Ouro parcial nunca promove.

Promoção = copiar o candidato aprovado para `app/modelos/` (manual, pelo João Paulo). O interesse só passa a valer com
o artefato promovido E `INTERESSE_MODELO=1`; sem isso o `local` usa o filtro atual (regex v2 + veto de risco < 0,3).

## Regras de dados

- Corpus da TOTVS, planilhas de rotulagem, holdout, rótulos e candidatos ficam SÓ em `analise-service/dados_locais/`
  (ignorado pelo git). Texto real de transcrição nunca vai ao git, ao log, a relatórios nem a ferramentas de IA.
- Fixtures e transcrições de teste são sintéticas. Logs só com tamanhos e ids.
- `*.joblib` é pickle: carregue só artefatos do próprio repo ou gerados por `treino/treinar.py`.
- Não edite `.env`, `*.joblib`, `backend/` nem `frontend/` a partir daqui.
