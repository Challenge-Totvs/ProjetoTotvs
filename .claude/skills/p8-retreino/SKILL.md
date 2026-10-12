---
name: p8-retreino
description: Tarefa P8 — pipeline offline de retreino do modelo local (risco + interesse): trechos, rótulos fracos (regex + destilação por LLM), conciliação do conjunto ouro, treino, portão de qualidade. Rode planejando em opus (opusplan) e executando em sonnet.
disable-model-invocation: true
---
Tarefa P8. Ciclo do `CLAUDE.md`, mas com PLANO obrigatório e aprovação antes de codar (use `/model opusplan`).
Autorizada pelo João Paulo: retreino sai do "Fora do escopo" do `CLAUDE.md`, nos termos de `docs/escopo-rag-retreino.md`.

Leia: `docs/escopo-rag-retreino.md` inteiro; `docs/decisoes.md` (A8 v2, filtro de interesse);
`app/engines/modelo_local_engine.py`, `app/engines/regras_engine.py`; `scripts/` existentes.

REGRAS DE DADOS (invioláveis nesta tarefa)
- O corpus real (CSV da TOTVS), as planilhas de rotulagem e o `holdout_reunioes.csv` ficam em
  `analise-service/dados_locais/`, que DEVE estar no `.gitignore` (confira e corrija ANTES de criar qualquer arquivo).
- Você NUNCA lê, imprime nem copia texto real de transcrição, nem abre as planilhas preenchidas. Escreva os scripts e
  teste com dados SINTÉTICOS em `tests/fixtures/`. Quem roda os scripts nos dados reais é o João Paulo.
- Relatórios e logs só com métricas e contagens, jamais com texto de trecho.
- Chaves só em `.env` (nunca ler). Teste nunca chama API real. A destilação usa o cliente de LLM simulado nos testes.
- Não edite `*.joblib`. Os candidatos treinados ficam em `dados_locais/candidatos/`; a PROMOÇÃO para `app/` é manual,
  feita pelo João Paulo (o portão imprime o comando).
- `joblib` é pickle: só artefatos produzidos por este pipeline no próprio repo.

PIPELINE (um script por etapa em `analise-service/treino/`, todos com `--help` e testes)
1. `extrair_trechos.py`: lê o CSV, descarta as reuniões do holdout (todas as reuniões dos clientes/CODT do pool),
   divide por turno (`[LOCUTOR N]: texto`), gera trechos (turno alvo + 2 turnos de contexto) em `dados_locais/`.
2. `rotulos_fracos.py`: (a) rótulo por regra, usando `regras_engine` como FONTE ÚNICA (risco, oportunidade, interesse;
   interesse = palavra-chave v2 sem veto); (b) `--destilar`: envia uma amostra de trechos candidatos (~3.000) a UMA LLM
   barata e grava rótulos de risco/oportunidade/interesse; exige `--teto-usd` e interrompe ao atingi-lo, mantém cache
   em disco e retoma de onde parou. Não use reuniões inteiras (custo). Teto de gasto da destilação: US$ 2.
3. `conciliar_ouro.py`, com DOIS modos (lê `.xlsx` com `openpyxl`, dependência só de TREINO em `requirements-treino.txt`;
   NÃO a coloque no `requirements.txt` do serviço):
   - `--modo unico` (padrão por ora, João é o único rotulador): lê `ouro_rotulador_1_PRONTO.xlsx` (metade A) e
     `ouro_rotulador_3_PRONTO.xlsx` (metade B; aceita só a A e marca "parcial"), sem divergências nem kappa entre pessoas.
     Se existir `ouro_reteste_PRONTO.xlsx` + `reteste_mapa.csv` (ids R01.. -> G..), calcula o kappa de Cohen
     teste-reteste (concordância dele consigo mesmo) para `padrao` e `interesse`. Escreve `ouro_final.csv`.
   - `--modo pares`: lê os 4 arquivos, kappa por par e campo, `divergencias.xlsx` para arbitragem, depois `ouro_final.csv`.
   Kappa < 0,6 em algum campo => aviso explícito: revisar definições antes de usar aquele campo. Todo relatório declara o
   modo (rotulador único, sem validação cruzada) e se o ouro está completo ou parcial.
4. `treinar.py`: treina DOIS modelos: risco e interesse (novo). O risco parte dos hiperparâmetros do classificador ATUAL,
   que o João Paulo inspecionou com `scripts/inspecionar_modelo.py` e estão registrados em `docs/decisoes.md` (D17): em
   código, `sklearn.base.clone` dos steps do `app/modelos/classificador_risco.joblib` (artefato do próprio repo), o que herda
   inclusive a lista de stop words (315, não impressa). Esses hiperparâmetros são o BASELINE do portão: mudar qualquer um
   exige registrar no `metadata.json` e justificar. O interesse começa da mesma família (TF-IDF + regressão logística).
   Treina SÓ com rótulos fracos e SÓ com reuniões fora do holdout. O conjunto ouro nunca entra no treino (só mede).
   Salva em `dados_locais/candidatos/<data>/` com `metadata.json` (data, hash dos dados, versão do scikit-learn, tamanhos).
5. `portao.py`: avalia candidato × modelo/filtro atual no `ouro_final.csv`, por GRUPO (risco, oportunidade, interesse),
   com F1, precisão e revocação e IC95% por bootstrap da diferença (n pequeno: avise que por padrão os números são
   apenas indicativos, ~8 trechos cada). Regra de aprovação: F1 do candidato >= baseline E precisão não cai mais de
   0,02 E o IC95% da diferença de F1 não fica inteiramente abaixo de zero. Escreve `docs/evidencias/portao-<data>.md`
   (somente métricas) e imprime o comando de promoção manual se aprovou, ou "REPROVADO: mantém o atual".
6. Encaixe do interesse em `modelo_local_engine.analisar` (descrito no relatório do item 2 do lote anterior): interface
   mínima = entrada lista `(n, texto)` em NFC, saída `p(interesse)` por turno, limiar nomeado (`LIMIAR_P_INTERESSE`),
   fallback ao filtro atual (regex v2 + veto de risco < 0,3) se o artefato faltar ou falhar, sem derrubar o motor.
   DESLIGADO por padrão: só ativa quando existir artefato promovido e `INTERESSE_MODELO=1`. A citação continua
   passando por `conferir_citacoes`.

PLANO DE CONTINGÊNCIA (documente no resumo)
- Sem chaves até segunda à noite: `rotulos_fracos.py` roda só (a), e o resumo avisa que o modelo de interesse tende a
  reproduzir a regra, valendo como demonstração do pipeline e do portão, não como ganho.
- Rotulagem incompleta (por exemplo só a metade A): o portão roda com o ouro parcial, marca "parcial" no relatório e
  NÃO recomenda promoção.
- Esforço: o plano (aprovação antes de codar) merece esforço alto; a execução, médio.

Entrega por commits pequenos (`feat(P8): extrair trechos`, etc.), um por etapa, `python -m pytest -q` verde em cada um,
resumo final de no máximo 20 linhas com o que o João precisa rodar nos dados reais, na ordem.
Não faça: mapeamento classificador → 14 padrões (Release 2), spaCy, `/evidencias`, mudança em `backend/` ou `frontend/`.
