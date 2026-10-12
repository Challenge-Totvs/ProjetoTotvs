# Escopo — RAG-lite e retreino do modelo local (até a banca de 15/10)

Status: decisões validadas por João Paulo em 11/10. Dono: João Paulo (Python) · Kelwin (Java/React).

## 1. Objetivo
Mostrar na banca o que a solução entrega com a amostra da TOTVS (1.147 reuniões) e como escala: (a) avisar quando um tema
novo lembra algo que o cliente já descartou; (b) um modelo local que melhora com dados, com portão de qualidade medido
por um conjunto ouro rotulado à mão.

## 2. Entregas
**A. `POST /similares` (P7, RAG-lite).** Sem API, sem dependência nova: cosseno TF-IDF, sem estado. O Java envia o texto do
tema novo e os trechos "não procede" do cliente; o Python devolve pares `{id, score}`; o Java guarda `semelhanteNaoProcede`
e ignora falha em silêncio. O endpoint ainda NÃO existe: contrato e fixtures primeiro (Python), depois o cliente Java (Kelwin).
`/evidencias` (busca de citações para relatórios) fica para depois da banca.

**B. Pipeline de retreino (P8).** Offline, em lote. Dois modelos: risco (retreinado) e interesse (novo, opção D).
Etapas: extrair trechos → rótulos fracos (regex v2 + destilação por LLM em ~3.000 trechos candidatos) → conciliar o conjunto
ouro → treinar → portão. O modelo novo só é promovido se superar o atual no ouro. Se reprovar, mostramos o relatório do
portão mesmo assim. Enquanto não houver modelo promovido, `local` mantém o filtro atual (regex v2 + veto de risco < 0,3).

## 3. Conjunto ouro (mede, nunca treina)
- 300 trechos: 110 de padrões (8 por padrão; `orcamento_restrito` só 6, pois há 6 reuniões no pool), 80 candidatos a
  interesse (7 deles com risco no mesmo turno), 110 negativos aleatórios.
- Rótulo por trecho: `padrao_1`, `padrao_2` (opcional), `interesse` (sim/nao), `duvida`. Contexto: turno alvo + 2 anteriores.
  Os rotuladores não veem o estrato nem os acertos de regex.
- Rotulagem POR ORA: João Paulo é o único rotulador (planilhas `ouro_rotulador_1` = metade A e `ouro_rotulador_3` = metade B;
  as de número 2 e 4 ficam sem uso). Sem segundo rotulador não há kappa entre pessoas. Substituto: TESTE-RETESTE, re-rotular
  40 trechos sorteados (`ouro_reteste.xlsx`) pelo menos 24 h depois, sem consultar as respostas anteriores, e medir a
  concordância consigo mesmo (kappa por campo). Limitação registrada nos relatórios: rotulador único, sem validação cruzada, e
  o rotulador também escreveu as regexes (por isso a planilha esconde estrato e acertos de regex).
- Se surgirem mais rotuladores, volta o protocolo de pares (cada trecho por 2 pessoas, kappa por par e campo, divergências
  arbitradas por João Paulo). Kappa < 0,6 => revisar definições antes de usar o campo.
- Tempo estimado: ~50 min por metade (150 trechos). Ordem de trabalho: metade A primeiro; as metades são amostras aleatórias
  estratificadas equivalentes, então a metade A sozinha já permite um portão preliminar.
- Para que servem os rótulos: MEDEM, não treinam. Servem (1) de gabarito do portão do modelo local (risco e interesse);
  (2) para validar a LLM usada na destilação (a "professora") antes de confiar nos rótulos fracos que ela gera, e medir
  recall nos trechos positivos e alarme falso nos negativos; (3) para calibrar limiares (veto 0,3 do interesse,
  `LIMIAR_SIMILARIDADE`). Validar as regexes é consequência, não o objetivo.
- Limite honesto: com ~8 trechos por padrão, o resultado por padrão é só indicativo; o portão decide por grupo
  (risco, oportunidade, interesse) com IC95% por bootstrap.

## 4. Separação treino × ouro
Holdout por cliente (CODT = código do cliente/lead): 30% das reuniões (345 reuniões de 199 clientes, sem clientes com mais
de 10 reuniões) ficam fora do treino; os 300 trechos saem delas (184 reuniões, 128 clientes). Treino usa as outras 802 reuniões.
A lista está em `holdout_reunioes.csv` (fora do git).

## 5. Critérios de aceite
- RT1 `/similares` tem contrato, fixtures, endpoint e testes sintéticos; falha do Java é inócua.
- RT2 Cada etapa do pipeline roda com `--help`, tem teste com dados sintéticos e não imprime texto de trecho.
- RT3 O ouro tem concordância medida: kappa por par e campo (rotuladores em pares) ou kappa teste-reteste (rotulador único),
  e os relatórios dizem qual modo foi usado.
- RT4 `portao.py` gera relatório só com métricas e decide promover ou manter.
- RT5 O interesse treinado só ativa com artefato promovido e `INTERESSE_MODELO=1`; sem isso, o fallback atual.

## 6. Cronograma
- Seg 12/10: João rotula a metade A; P7 e etapas 1 a 4 do P8; chaves de desenvolvimento com o Kelwin até a noite.
  Se aparecerem rotuladores extras, distribuir as planilhas 2 a 4.
- Ter 13/10, 18h: metade B e reteste prontos (reteste pelo menos 24 h depois da metade A); noite: conciliação.
- Qua 14/10: manhã treino e portão; 12h congelamento; tarde ensaio.
- Qui 15/10: banca.
Contingência: sem chaves na segunda à noite, rótulo fraco só por regra (o modelo de interesse tende a reproduzir a regra:
demonstra pipeline e portão, não ganho); rotulagem incompleta => portão com ouro parcial, sem recomendar promoção.

## 7. Orçamento de LLM (US$ 5 ou R$ 20 por provedor)
Chave de desenvolvimento (smoke e destilação, até ~US$ 2,5 por provedor; destilação só no modelo barato, teto US$ 2) e
chave de demonstração separada, criada na quarta, com o saldo restante. Estimativas de custo são ordem de grandeza.

## 8. Segurança e privacidade
Corpus, planilhas e holdout só em `analise-service/dados_locais/` (ignorado pelo git). Texto real de transcrição nunca vai
ao git, ao log, ao relatório nem ao Claude Code. `joblib` é pickle: só artefatos próprios; promoção para `app/` é manual.
Testes nunca chamam API real. Chaves só em `.env`.

## 9. Argumento de escala para o pitch (sem exagerar)
Treino é lote (~28 s para 200 mil trechos, 2 vCPU, medido por proxy); inferência local ~120 ms por reunião mediana. Camadas de
custo: LLM (por token) → local (marginal ~zero) → regras (zero), com `ORDEM_MOTORES` opcional como roadmap. NÃO afirmar
autoscaling implementado.

## 10. Fora do escopo
`/evidencias`, spaCy/E8, mapeamento classificador → 14 padrões (Release 2), regras de conduta (backend), autoscaling real.

## 11. Pendências para o Kelwin
Cliente Java do `/similares` e campo `semelhanteNaoProcede`; AC9 (teste Java lendo as fixtures); A10 (SDD §6.2); chaves de API;
frontend mostra "Evidência não localizada." antes de qualquer `descartados[].motivo` (ajustar antes de criar motivos novos).
