# Relatório do lote da tarde — 12/10/2026

Lote sem supervisão (~2 h), autorizado a seguir sem aprovação de plano. O plano de cada item é escrito aqui antes de
implementar. Sem texto de transcrição neste arquivo (só contagens e métricas). Commits em nome de Joao, sem coautoria.
Sem push.

Baseline do pytest no início do lote (`analise-service/.venv`): `414 passed in 14.69s`.

## Item 1 — Reorganizar os CLAUDE.md
**Plano:** (a) `CLAUDE.md` da raiz fica só com o que vale para o grupo: mapa do repo, contrato, prazos, estado atual,
arquitetura em 5 linhas, regras de dados e de commit (regras 11 e 12 mantêm o número) e "ler sob demanda" do que é do
grupo. (b) `analise-service/CLAUDE.md` novo: regras invioláveis 1-10 (texto preservado), "não edite backend/ e
frontend/", comandos, tarefas por ID, ciclo fixo, fora do escopo, ler sob demanda. (c) `CLAUDE.local.md` na raiz com as
preferências do João; o `.gitignore` já tem a linha `CLAUDE.local.md` (conferido com `git check-ignore`), então nada a
acrescentar. (d) `.claude/skills/p8-retreino/SKILL.md`: só a linha da seção REGRAS DE DADOS sobre ler texto real.
**Antes → depois (nomes de seção):**
- `CLAUDE.md` (raiz) antes: Mapa · Estado atual · Comandos · Arquitetura · Regras invioláveis (1-12) · Como trabalhar ·
  Fora do escopo · Ler sob demanda. Depois: Mapa (sem "NÃO edite") · Contrato · Estado atual · Arquitetura · Regras de
  dados e de commit (11, 12 + decisão do corpus anonimizado) · Ler sob demanda.
- `analise-service/CLAUDE.md` (novo): Não edite · Comandos · Regras invioláveis (1-10) · Como trabalhar (tarefas por ID,
  ciclo fixo) · Fora do escopo · Ler sob demanda.
- `CLAUDE.local.md` (novo, ignorado pelo git): preferências de commit e de comunicação.
- `p8-retreino/SKILL.md`: só a primeira linha da seção REGRAS DE DADOS sobre ler texto real.
**Status:** concluído.

## Item 2 — `docs/evidencias/smoke-12-10.md`
**Plano:** criar o arquivo (a pasta `docs/evidencias/` ainda não existe) só com os fatos informados pelo João; não tocar
em `PROMPT_VALIDADO_COM_LLM_REAL`.
**Status:** concluído (`PROMPT_VALIDADO_COM_LLM_REAL` intocado). Sem mudança de código; suíte inalterada (414).

## Item 3 — `conciliar_ouro` no layout REAL da planilha
**Plano:** (1) `ler_planilha` lê SEMPRE a aba `Rotular` (erro claro se faltar; só `divergencias_PRONTO.xlsx`, gerado por
nós, continua lendo a 1ª aba). (2) Defaults `--col-id ID` e `--col-texto "TRECHO ALVO|texto"` (alternativas separadas
por `|`; a comparação já ignora maiúsculas/acento/espaço), então o layout antigo dos testes continua valendo. (3)
`lista_de_padroes`: lê a aba `Listas` e junta todo valor de célula textual, normalizado, como vocabulário permitido;
`padrao_1`/`padrao_2` fora dele só incrementam `invalidos["fora_da_lista"]` (nunca impressos). Sem a aba `Listas`, não
valida (compatível com planilhas antigas). (4) Teste com planilha SINTÉTICA no layout real: abas Leia-me, Rotular,
Padrões, Listas; cabeçalho na linha 1; coluna C oculta; a aba Rotular NÃO é a primeira.
**Limite:** tentei ler só a estrutura (abas e aba Listas) de `ouro_rotulador_1.xlsx` para ver o layout real das listas e
o classificador de segurança negou a ação. Não contornei: o formato da aba `Listas` é suposição (vocabulário = todas as
células de texto), registrada como decisão para o João validar.
**Status:** concluído. Suíte: 421 passed (+7 em `tests/test_p8_conciliar_ouro_layout.py`; os testes antigos de
planilha ganharam a aba `Rotular` e a nova chave `fora_da_lista` em `invalidos`). O `--verificar` agora também informa
quantos valores a aba `Listas` tem (`valores_na_aba_listas`).

## Item 4 — P9: `treino/validar_professora.py`
**Plano (duas etapas, um commit por etapa):**
- Etapa 1, núcleo puro: `comparar(ouro, cache)` (por grupo risco/oportunidade/interesse: n, positivos, revocação nos
  positivos, alarme falso = FP/negativos, precisão, F1 via `portao.metricas`, kappa LLM × João via
  `conciliar_ouro.kappa_cohen`) e `veredito` (`usar` se kappa >= 0,6 e revocação >= 0,7; senão "NÃO usar para rótulos
  fracos nesse grupo"). Trechos com `duvida`=1, rótulo vazio e itens sem resposta da LLM ficam fora (contados).
- Etapa 2, CLI: lê `ouro_final.csv` (+ `ouro_final.json` para modo e completo/parcial), roda
  `rotulos_fracos.destilar` (cliente injetável, cache e retomada em `dados_locais/professora/`, separado do cache da
  destilação porque os ids do ouro são outros), `--teto-usd` obrigatório e <= 0,5 (validado antes de `destilar`, que
  continua com o seu limite de US$ 2), preços por milhão obrigatórios; escreve `docs/evidencias/professora-<data>.md`
  só com métricas. Testes sintéticos com cliente simulado.
- Não vou rodar o script sobre o `ouro_final.csv` real (regra do lote: não abrir) nem com API.
**Status:** concluído em duas etapas. Suíte: 434 passed (13 testes em `tests/test_p9_professora.py`, todos sintéticos e
com cliente simulado; nenhum acessa rede ou chave).
**Commits:** `846221b feat(P9): metricas e veredito da professora contra o ouro` · `feat(P9): validar_professora CLI`.
**Como rodar (João, nos dados reais):**
`python treino/validar_professora.py --teto-usd 0.5 --preco-entrada <US$/Mtok> --preco-saida <US$/Mtok>`
(retoma sozinho se parar no teto; relatório em `docs/evidencias/professora-<data>.md`).

## Item 5 — Dados reais (extração e rótulos por regra)
**Plano:** os dois arquivos existem em `dados_locais/`. (a) `--verificar` e extração com `--col-reuniao ID_MEETING
--col-cliente CODT --col-texto ANON_TRANSCRICAO`; (b) `rotulos_fracos.py` sem `--destilar`. Só contagens.
**Achados no `--verificar` (sem texto):**
1. O arquivo NÃO é UTF-8 puro: 88 bytes inválidos em ~46 MB (o resto é UTF-8). O leitor passou a usar
   `errors="replace"` (fix com teste; efeito: um caractere `�` no lugar do byte solto).
2. O CSV está num formato quebrado: lido de forma padrão, dá 334.501 "linhas" em vez de reuniões, porque só a primeira e a
   última linha física de cada registro vêm entre aspas (com `"` dobradas) e as linhas do meio vêm soltas. Um contador
   de início de registro (`"<id>,<data hora>,`) acha 1.147 reuniões (~291 linhas físicas cada). Não é erro de coluna nem
   de holdout, então não parei o item: escrevi um leitor de reparo para esse formato (decisão 5-D1), com teste sintético
   e validação rígida (registro que não fecha é só contado). No corpus real: 1.147 registros, 0 inválidos, 0 linhas
   órfãs, 18 campos em todos.
3. 7 `ID_MEETING` aparecem repetidos (21 linhas extras), todos 100% idênticos entre si. `extrair` parava com "reunião
   repetida"; agora ignora e conta a repetição idêntica (conteúdo diferente continua parando; decisão 5-D2).

**Resultados (só contagens):**
- `extrair_trechos.py --verificar`: corpus 18 colunas (ID_MEETING, CODT e ANON_TRANSCRICAO presentes), 1.147 reuniões;
  holdout 3 colunas (ID_MEETING, CODT, no_ouro), 345 linhas.
- Extração: reuniões lidas 1.147 · excluídas pelo holdout 345 (199 clientes no holdout) · repetições idênticas ignoradas
  17 · sem turnos `[LOCUTOR n]` 28 · reuniões usadas 757 · **trechos gerados 233.267**.
- `rotulos_fracos.py` (só regra, sem `--destilar`): positivos de risco 958, oportunidade 1.241, interesse 1.500
  (de 233.267 trechos; nenhum rótulo da LLM).
- Nada de `dados_locais/` entrou no git (`git status` limpo para essa pasta; está no `.gitignore`).
- Pendência para o João: 28 reuniões sem turnos `[LOCUTOR n]` (formato diferente ou transcrição vazia?).
**Status:** concluído. Commits: `892e395 fix(P8): leitor do corpus tolera bytes invalidos e o formato quebrado de aspas`
· `c6c5d66 fix(P8): reuniao repetida identica no corpus e ignorada e contada`. Suíte: 441 passed.

## Item 6 — Ensaio de falha da cadeia (demo da banca)
**Leitura do comportamento atual (sem mudar nada):**
- `FORCAR_FALHA` (lista separada por vírgula, valores fora dos 4 motores ignorados) é lida por `config.motores_forcados()`
  a CADA chamada de `os.environ`. Em `cadeia.executar_cadeia`, motor forçado levanta `ErroMotor("erro_provedor")` sem
  chamar o motor; isso entra em `tentativas` e é registrado em `saude` como falha REAL (`real=True`).
- A cadeia é llm1 -> llm2 -> local -> regras; o primeiro que responde escreve `motor`, `tentativas` e `versaoContrato`;
  `local` e `regras` acrescentam o aviso `contingencia_modelo_local` / `contingencia_regras`; sem nenhum, `AnaliseIndisponivel`
  vira 503 `analise_indisponivel` com `tentativas`.
- `/health`: `ok` = configurado E fora de `FORCAR_FALHA` E última tentativa real sem falha nos últimos 300 s;
  `status` = ok (alguma LLM ok) · degradado (só local/regras) · indisponivel.
**Plano:** (a) `scripts/ensaio_falha.py`: ambiente simulado (chaves e modelos FICTÍCIOS, `.env` ignorado, clients de LLM
substituídos por fakes em `llm_engine.obter_cliente`, restaurados no fim), `TestClient` do app real com
`PIPELINE_VERSAO=real`, a fixture `tests/fixtures/transcricao-sintetica-p90.json`, 5 cenários via `FORCAR_FALHA` (a mesma
alavanca da demo), estado do `/health` zerado entre cenários (equivale a reiniciar o serviço) e lido depois de cada um;
tabela só com nomes e contagens. (b) `docs/roteiro-ensaio-falha.md`. (c) `tests/test_ensaio_falha.py`: roda o script e
confere a tabela contra o esperado do contrato/SDD; divergência vira anotação aqui, sem mexer em `cadeia`/`saude`.
**Resultado do ensaio (script real, tabela completa em `python scripts/ensaio_falha.py`):**

| # | FORCAR_FALHA | motor | tentativas | HTTP | /health depois |
|---|---|---|---|---|---|
| 1 | (vazio) | llm1 | llm1:ok | 200 | ok (4 motores ok) |
| 2 | llm1 | llm2 | llm1:erro_provedor > llm2:ok | 200 | ok (llm1 X) |
| 3 | llm1,llm2 | local | 2 × erro_provedor > local:ok · aviso contingencia_modelo_local | 200 | degradado (llm1, llm2 X) |
| 4 | llm1,llm2,local | regras | 3 × erro_provedor > regras:ok · aviso contingencia_regras | 200 | degradado (só regras ok) |
| 5 | os 4 | nenhum | 4 × erro_provedor | 503 `analise_indisponivel` | indisponivel (4 X) |

Os tempos ficam em 0,01 a 0,3 s (P90 sintético; local é o mais lento). O comportamento real BATE com o contrato v3
(§6, §8.1, §8.3) em todos os 5 cenários. Os comandos PowerShell do roteiro foram validados contra um uvicorn real de teste
(porta 8765, sem chaves, `.env` ignorado, depois encerrado) nos cenários "só regras" e "503".
**Observações (nada foi corrigido, conforme pedido):**
- 6-O1: o SDD §6.2 diz "500 se todos os motores falharem"; o código e o contrato v3 §8.1 dizem 503
  `analise_indisponivel`. É a divergência já conhecida do contrato ("proposta: atualizar o SDD"); falta só atualizar o SDD.
- 6-O2: `docs/decisoes.md` (Item 4 do P5) diz que `FORCAR_FALHA` "é lida a cada chamada, então pode ir no `.env`". É
  verdade só para o `os.environ`: o `.env` é lido uma vez na subida (`main.py`). Mudar o `.env` com o serviço no ar não
  tem efeito; para trocar de cenário é preciso reiniciar. O roteiro já diz isso.
- 6-O3: falha forçada entra no `/health` como falha REAL (a cadeia a registra em `saude`). Tirar `FORCAR_FALHA` sem reiniciar
  deixa o motor com `ok: false` por até 5 min (ou até a próxima tentativa bem-sucedida). Reiniciar zera.
**Status:** concluído. Arquivos: `scripts/ensaio_falha.py`, `docs/roteiro-ensaio-falha.md`, `tests/test_ensaio_falha.py`
(9 testes, sem rede e sem chave).
