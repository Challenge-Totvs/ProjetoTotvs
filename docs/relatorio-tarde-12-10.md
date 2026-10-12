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
**Status:** concluído em duas etapas. Suíte: 439 passed (13 testes em `tests/test_p9_professora.py`, todos sintéticos e
com cliente simulado; nenhum acessa rede ou chave).
**Commits:** `846221b feat(P9): metricas e veredito da professora contra o ouro` · `feat(P9): validar_professora CLI`.
**Como rodar (João, nos dados reais):**
`python treino/validar_professora.py --teto-usd 0.5 --preco-entrada <US$/Mtok> --preco-saida <US$/Mtok>`
(retoma sozinho se parar no teto; relatório em `docs/evidencias/professora-<data>.md`).
