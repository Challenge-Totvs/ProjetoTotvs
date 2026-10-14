# Decisões e pendências — analise-service

Última atualização: 12/10/2026. Registre aqui toda decisão tomada durante as tarefas.
A numeração D1–D9 é deste arquivo; no contrato, "D2", "D3", "D4" e "D9" citam as decisões do guia anterior.

## Decididas
| # | Decisão | Origem |
|---|---|---|
| D1 | Fonte do formato = `ContratoV3.java` + SDD §6.2; arquivo do lado Python = `docs/contrato/contrato-v3.md`. O contrato v1 foi retirado. | 11/10 |
| D2 | Citação é recorte literal; conferência no Python com vizinhos ±2 e `turnoFim` | SDD §5.7 |
| D3 | O Java numera e pseudonimiza (nomes do cadastro). Pendência de LGPD que sobra: nomes fora do cadastro (E8) | 11/10 |
| D4 | `confianca` só nas LLMs; ausente nos demais motores | 11/10 |
| D5 | Regex por padrão volta na Release 1 (tarefa P4) | João Paulo, 11/10 |
| D6 | Orçamento de tempo: llm1 ~55 s, llm2 ~35 s, reserva ~10 s, total <= 100 s; Java espera 120 s. Calibrar no smoke | 11/10 |
| D7 | Rollback/mock: `PIPELINE_VERSAO=real|mock`; `mock` devolve `resposta-v3-llm.json` | João Paulo, 11/10 |
| D8 | A5: o modelo local divide o texto por turno "por ora"; revisar na Release 2 | João Paulo, 11/10 |
| D9 | A7: `descartados` com motivo `nao_procede` só no fluxo do Java | João Paulo, 11/10 |

## Abertas
| # | Pendência | Dono |
|---|---|---|
| A2 | Lista definitiva dos eventos de conduta | João Paulo |
| A3 | Mapeamento classificador -> 14 padrões (Release 2) | João Paulo |
| A8 | Conteúdo das 14 expressões regulares (primeira versão sai na P4; revisar) | João Paulo |
| A9 | 503 ou 500 quando a análise falha | João Paulo e Kelwin |
| A10 | Atualizar SDD §6.2 para apontar ao `contrato-v3.md` | Kelwin |
| AC9 | Teste Java lendo as fixtures v3 | Kelwin |

## Registro de execução (pytest)
### P0 — commit e50a25b
```
...................                                                      [100%]
19 passed in 2.67s
```
### P1 — schemas v3
Nota: o `AnaliseResponse` v1 virou `AnaliseResponseV1` (usado só por `orchestrator` e `engines`, que P2/P4 reescrevem). Limites do §3.2 e `padrao_desconhecido` do pedido ficaram na P1 (a P0 os adiou).
```
..................................................                       [100%]
50 passed in 2.10s
```
### P3 — conferência de citações
Decisão de leitura do §7.2(c): todas as janelas (1, 2 e 3 turnos) ficam dentro de n−2..n+2; um trecho que comece fora desse intervalo é descartado. `conferir_citacoes(turnos, itens, *, origem, campo_texto)` devolve `(confirmados, descartados)`; `turnoFim` é sempre preenchido (quem monta o `Interesse` o ignora).
```
........................................................................ [ 98%]
.                                                                        [100%]
73 passed in 2.19s
```
### P5 — health por motor e erros estruturados
- `/health`: `llm1`/`llm2` ok = chave **e** modelo definidos (sem chamar API); `local` = artefato existe e `joblib.load` funciona (carga preguiçosa, em cache); `regras` sempre true. `status`: ok / degradado / indisponivel (§8.3).
- 503/500 no formato do §8.1 com o header `X-Insightcall-Pipeline`; o 500 não loga nem devolve a mensagem da exceção (só o tipo).
- `app/cadeia.py`: `executar_cadeia(pedido, [(motor, fn)])` escreve `motor`, `tentativas`, `versaoContrato` e os avisos de contingência pelo código. Ainda NÃO está ligada ao router: depende dos motores v3 (P2/P4). Até lá, `PIPELINE_VERSAO=real` responde 503 com `tentativas: []`.
- A9 (503 vs 500): segui o §8.1 (503 quando nenhum motor responde, 500 só para defeito inesperado). Sem divergência do Java, que trata qualquer 4xx/5xx igual.
- Teste da P0 `test_ac7_health_no_formato_do_contrato` passou a definir chaves fictícias, pois o `ok` fixo era provisório.
- Observação: nenhum código carrega `analise-service/.env` (`load_dotenv` não é chamado). Para o modo `real`, as variáveis precisam estar no ambiente do processo. Fica para o João Paulo decidir (dependência `python-dotenv` já existe em requirements).
```
....................................................................... [ 72%]
100 passed in 4.38s
```

## Decisões de 12/10 (autorizadas pelo João Paulo)
| # | Decisão | Onde |
|---|---|---|
| D10 | Um tema por padrão por reunião; se o padrão aparecer duas vezes, escolher a primeira ocorrência sem resposta. Instrução ao motor (prompt e regras), sem deduplicação posterior | `contrato-v3.md` §7.6.1 |
| D11 | A9 fechada: falha total responde 503; o Java trata qualquer erro HTTP como "análise indisponível" | `contrato-v3.md` §12 |
| D12 | RAG-lite (`POST /similares`, P7) e retreino do modelo local (P8) autorizados; saem do "Fora do escopo". Escopo, entregas, critérios e cronograma em `docs/escopo-rag-retreino.md` | João Paulo, 12/10 |
| D13 | Conjunto ouro com rotulador único (João Paulo): sem kappa entre pessoas; substituto = teste-reteste de 40 trechos sorteados, pelo menos 24 h depois, sem consultar as respostas anteriores. Limitação declarada nos relatórios (rotulador único, sem validação cruzada, e ele também escreveu as regexes). Se surgirem mais rotuladores, volta o protocolo de pares | João Paulo, 12/10 |
| D14 | Orçamento de LLM: US$ 5 ou R$ 20 por provedor, duas chaves (desenvolvimento e demonstração). Destilação só no modelo barato, com teto de US$ 2 (`--teto-usd`) | João Paulo, 12/10 |
| D15 | O filtro de compromissos por `papeis` (só do vendedor) fica só no prompt até a banca. O Java lê `descartados[].motivo` como texto livre (`String`, sem enum), mas o frontend sempre prefixa "Evidência não localizada." antes do motivo; motivo novo de descarte depende de ajuste do Kelwin | João Paulo, 12/10 |
| D16 | `openpyxl` autorizado como dependência de TREINO (P8): `analise-service/requirements-treino.txt` fixa `openpyxl==3.1.5` (versão instalada no `.venv`); o `requirements.txt` do serviço não muda | João Paulo, 12/10 |
| D17 | O treino do candidato de risco parte dos hiperparâmetros do `classificador_risco.joblib` atual (abaixo), e eles são o baseline do portão | João Paulo, 12/10 |

Nota de numeração: a mensagem de 12/10 pedia "D10 a D13"; como D10 e D11 já existiam (acima, e citados no prompt e no contrato), os quatro itens novos entraram como D12 a D15, na mesma ordem (RAG e retreino, rotulador único, orçamento de LLM, filtro de compromissos).

## Bloqueios
(nenhum até agora)

## Registro de execução — lote de 12/10
### Item 1 — .env via python-dotenv
`carregar_dotenv()` em `app/config.py`, chamado por `main.py`: só carrega se `analise-service/.env` existir, `override=False`. O `conftest.py` liga `INSIGHTCALL_IGNORAR_DOTENV=1` para que nenhum teste leia o `.env` real. O arquivo nunca foi lido por mim.
```
105 passed in 5.70s
```

### Item 2 — P4 regras e modelo local
- `regras_engine`: 14 expressões (casam sem acento), primeira ocorrência por padrão (D10), respeita `padroes` e suprime turnos iguais a `contraexemplos`/`correcoesAnteriores`. Score = interesse + temas de oportunidade sobre todos os sinais; 50 sem sinais; limiares 70/45 (constantes nomeadas).
- `modelo_local_engine` v3: carga preguiçosa (`ErroMotor modelo_indisponivel`), trechos por turno (A5), classificador dá `score` e filtra o `interesse` (palavra-chave E risco < 0,3, proposta); temas vêm das regex.
- `orchestrator.py` v3 sobre `cadeia.py`: llm1/llm2 entram pelo parâmetro `llms` (item 3). Pipeline real passou a responder 200 (local/regras) ou 503.
- Testes provisórios ajustados: o 503 de 'pipeline não migrado' (P0, P5) e a checagem de módulo no AC7 (agora: `joblib`/`sklearn` não carregam no import).

#### A8 — as 14 expressões, para aprovação do João Paulo (primeira versão)
1. `suporte_insatisfacao` (risco): `\b(suporte|atendimento|chamado|ticket)\b.{0,80}\b(demor\w*|ninguem\s+(retorn\w*|respond\w*)|sem\s+(retorno|resposta)|nao\s+(retorn\w*|respond\w*|resolv\w*)|lent[oa]|pessim\w*|ruim|horriv\w*|insatisf\w*|reclam\w*)|\b(demor\w*|ninguem\s+retorn\w*)\b.{0,80}\b(suporte|atendimento|chamado)\b`
2. `preco_objecao` (risco): `\b(muito\s+caro|ficou\s+caro|esta\s+caro|e\s+caro|salgad[oa]|preco\s+(\w+\s+){0,2}(alto|elevado|puxado)|valor\s+(\w+\s+){0,2}(alto|elevado|puxado|salgad[oa])|mais\s+barat[oa]|acima\s+do\s+(nosso\s+)?(orcamento|mercado))\b`
3. `prazo_implantacao` (risco): `\b(prazo|cronograma)\b.{0,60}\b(implanta\w*|implementa\w*|go[- ]?live|virada|migra\w*)|\b(implanta\w*|implementa\w*|migra\w*)\b.{0,60}\b(prazo|atras\w*|demor\w*)|\batras\w*\b.{0,40}\b(implanta\w*|projeto|go[- ]?live|cronograma)`
4. `concorrente_citado` (risco) **[v2]**: `\b(concorrent\w*|outro\s+fornecedor|outra\s+solucao|omie|bling)\b` (`sap` e `oracle` saíram em 13/10, ver abaixo)
5. `cancelamento_citado` (risco) **[v2]**: `\b(cancel\w*|rescind\w*|rescis\w*)\b.{0,40}\b(contrato|assinatura|licenca\w*|plano|servico|sistema|produto|conta)\b|\b(contrato|assinatura|licenca\w*|plano|servico|sistema|produto|conta)\b.{0,40}\b(cancel\w*|rescind\w*|rescis\w*)\b|\bencerrar\s+(o\s+)?contrato\b|\bnao\s+(vamos|vou|pretendemos)\s+renovar\b|\bdeixar\s+de\s+usar\b`
6. `adocao_resistencia` (risco): `\b(equipe|time|pessoal|usuarios|funcionarios|colaboradores)\b.{0,60}\b(resist\w*|nao\s+(usa\w*|quer\w*|adaptou|se\s+adapt\w*|gost\w*)|dificuldade)|\b(resistencia|ninguem\s+usa)\b`
7. `fiscal_problema` (risco): `\b(fiscal|sped|nfe|nf-e|imposto\w*|tribut\w*|apuracao)\b.{0,80}\b(erro\w*|problema\w*|falh\w*|travou|nao\s+(fecha|fechou|bate|gera\w*)|divergen\w*|rejei\w*)|\b(erro\w*|problema\w*|falh\w*|divergen\w*|rejei\w*)\b.{0,80}\b(fiscal|sped|nfe|nf-e|imposto\w*|tribut\w*|apuracao)\b`
8. `orcamento_restrito` (risco): `\b(orcamento|verba|caixa|budget)\b.{0,60}\b(apertad\w*|curto|limitad\w*|restrit\w*|cortad\w*|congelad\w*|estourad\w*|sem\s+folga)|\b(sem\s+verba|sem\s+orcamento|corte\s+de\s+(custos|orcamento)|congelamento\s+de\s+(gastos|orcamento)|congel\w+\s+(novas\s+)?compras)\b`
9. `expansao_unidade` (oportunidade): `\b(nova|novo|outra|mais\s+uma)\s+(unidade|filial|loja|sede|clinica)\b|\b(unidade|filial|loja|sede)\s+nova\b|\b(abrir|abrindo|inaugur\w*|expandir)\b.{0,50}\b(unidade|filial|loja|sede|clinica)\b|\bexpansao\b`
10. `modulo_adicional` (oportunidade) **[v2]**: `\b(queremos|querem|quero|gostaria\w*|interesse\s+em|precisamos\s+de|contratar|adquirir|comprar|adicionar|incluir|acrescentar|adicional)\b.{0,40}\b(modulos?|add-?on|business\s+intelligence|telemedicina|dashboard|painel|bi)\b|\bmodulos?\s+(adicional|adicionais|extra|extras|novo|novos)\b|\b(add-?on|business\s+intelligence|telemedicina)\b`
11. `integracao` (oportunidade) **[v2]**: `\b(integra\w*|api|webservice|web\s+service|sincroniz\w*|conectar\s+com)\b.{0,60}\b(queremos|querem|quero|preciso|precisamos|gostaria\w*|necessidade|tem\s+como|da\s+para|consegue\w*|possivel|possibilidade)\b|\b(queremos|querem|quero|preciso|precisamos|gostaria\w*|necessidade\s+de|tem\s+como|da\s+para|consegue\w*|possibilidade\s+de)\b.{0,60}\b(integra\w*|api|webservice|web\s+service|sincroniz\w*|conectar\s+com)\b`
12. `renovacao` (oportunidade): `\b(renova\w*|prorrog\w*|continuidade\s+do\s+contrato|estender\s+o\s+contrato)\b`
13. `upgrade_licencas` (oportunidade): `\b(mais|novas|adicionais|ampliar|aumentar|comprar)\b.{0,30}\blicenc\w*|\blicenc\w*\b.{0,30}\b(adicionais|extras?)\b|\bupgrade\b|\bmais\s+usuarios\b|\busuarios\s+adicionais\b|\bplano\s+(maior|superior)\b`
14. `treinamento` (oportunidade) **[v2]**: `\b(precisamos|queremos|quero|preciso|gostaria\w*|necessidade\s+de|solicit\w*|agendar|contratar|oferecer|fazer|novo|novos)\b.{0,30}\b(treinament\w*|capacita\w*|workshop|onboarding|reciclagem)\b|\b(treinament\w*|capacita\w*)\s+(adicional|adicionais|extra|extras|para\s+(a\s+|o\s+|os\s+|as\s+)?(equipe|time|usuarios|funcionarios|colaboradores))\b|\baprender\s+a\s+usar\b`

Interesse (palavras-chave) **[v2, sem otimo/perfeito/combinado/fechado]**: `\b(ajuda\s+bastante|ajuda\s+muito|gostei\w*|interessante|interessad[oa]|excelente|vamos\s+fechar|pode\s+enviar|manda\s+a\s+proposta|queremos\s+avancar)\b`

**Nota A8 v2:** proposta v2 por contagem no corpus; calibrar com o conjunto ouro. Cinco padrões e as palavras de interesse passaram a exigir contexto de demanda/objeto (a v1 casava vocabulário comum do domínio: integracao 75,6% das reuniões, modulo_adicional 51,2%, treinamento 50,0%, concorrente_citado 47,5%, cancelamento_citado 32,2%, interesse 90,8%; a v2 estimada em 35,1%, 10,8%, 11,8%, 31,4%, 8,5% e 68,2%; só contagens agregadas, sem texto do corpus). Os outros 9 padrões não mudaram. O veto de risco do `interesse` do `local` (risco < 0,3) permanece. Fonte única: `regras_engine.py` (o `local` usa as mesmas expressões).
```
......                                                                   [100%]
150 passed in 4.99s
```

### Item 3 — P2 prompt e llm_engine v3
**Prompt NÃO validado com LLM real.** Todos os testes usam clients simulados; a validação é o smoke manual `analise-service/scripts/smoke_llm.py` (AC10), a cargo do João Paulo. Constante `PROMPT_VALIDADO_COM_LLM_REAL = False` em `llm_engine.py`.
- `montar_prompt`: turnos `[turno N | locutor L]`, só os padrões ativos, regra D10 ("um tema por padrão por reunião..."), extras só se presentes, contraexemplos + correções sem duplicata por `(padrao, texto)`, `neutralizar()` para `transcricao`, `contraexemplos`, `contexto_cliente`, `glossario_time` em todos os campos vindos do pedido. Efeito colateral: uma citação que contenha uma dessas marcações chega à LLM trocada por colchetes e é descartada na conferência.
- Clients criados com `timeout` (55 s / 35 s) e `max_retries=0`, SDKs importados só na hora do uso, uma tentativa por motor (sem retry interno). `Prazo` compartilhado (100 s − 10 s de reserva) limita o `timeout` de cada chamada; sem prazo restante vira `timeout` sem chamar a API.
- Erros dos SDKs traduzidos pelo nome da classe para os códigos do §6.5; `max_tokens` = 8.000 (4.000 era insuficiente, §7.6); `stop_reason=max_tokens` vira `truncado`.
- `processar_saida` (ponto de extensão): `conferir_citacoes` (P3), padrão/evento fora da lista, limites do §7.6, `papeis`/`sentimentoSerie` montados em código, `avisos=["saida_parcial"]` se houve descarte ou corte.
- Não implementado: validar que `compromissos` são do vendedor no código (fica só no prompt; não há motivo de descarte previsto no §6.7).
- Pipeline real: llm1 → llm2 → local → regras → 503. Sem chaves, as duas LLMs aparecem em `tentativas` como `nao_configurado`.
- `conftest.py` agora remove `LLM_*` do ambiente em todo teste.
```
.....................................................                    [100%]
197 passed in 7.39s
```

### Item 4 — P5 ajuste: /health por tentativa real e FORCAR_FALHA
- `ok` de cada motor = configurado **e** não forçado **e** a última tentativa real dele não falhou nos últimos 300 s (estado em memória, por processo; reinício zera). Uma tentativa bem-sucedida depois da falha recupera na hora.
- Não contam como tentativa real: `nao_configurado` e "sem prazo restante" (`ErroMotor(..., real=False)`), porque a API não foi chamada.
- Divergência consciente do contrato §8.3 ("`ok` de `regras` = sempre `true`"): com esta regra, `regras`/`local` também ficam `false` por 5 min se falharem de verdade. **Decidido e aplicado ao contrato §8.3 (commit docs(contrato): semantica do /health).**
- `FORCAR_FALHA=llm1` (lista separada por vírgula; vazia por padrão; nomes inválidos ignorados) faz a `cadeia` registrar falha `erro_provedor` desse motor sem chamar a API, e o `/health` o mostra com `ok: false` imediatamente (para a demo "derrubar a LLM principal"). Vale para qualquer um dos quatro motores. Lida a cada chamada, então pode ir no `.env`.
```
..................................................................       [100%]
210 passed in 7.40s
```

### Item 5 — P6 suíte do orquestrador e do contrato
Nenhum bug de produção encontrado pelos testes novos. O prompt e o AC10 (smoke real) ficam pendentes de propósito.

| AC | Testes (arquivo::função) | Estado |
|---|---|---|
| AC1 | `test_p0_mock::test_ac1_aceita_pedidos_v3`, `::test_ac1_recusa_pedido_invalido_com_422_estruturado` | coberto |
| AC2 | `test_p1_schemas::test_ac2_fixtures_validam`, `test_p6_contrato::*` (enums e campos contra `MotorUtilizado.java`, `SentimentoGeral.java`, `ContratoV3.Resposta`) | coberto |
| AC3 | `test_p2_llm::test_llm1_responde_e_a_saida_bate_com_a_fixture`, `test_p1_schemas::test_saida_llm_schema_e_estrito` | coberto com client simulado; **prompt NÃO validado com LLM real** |
| AC4 | `test_p3_citacoes` (acerto, espaços/aspas, vizinho, entre dois turnos, inexistente, fixtures) | coberto |
| AC5 | `test_p6_orquestrador` (llm1; llm1→llm2; duas fora→local; local fora→regras; tudo fora→503; LLM lenta com relógio simulado, total <= 100 s) | coberto |
| AC6 | `test_p4_regras` (um teste por padrão, 14), `test_modelo_local_engine` | coberto |
| AC7 | `test_p0_mock::test_ac7_*`, `test_p5_health` | coberto |
| AC8 | `test_p0_mock::test_ac8_mock_devolve_fixture_e_header` | coberto |
| AC9 | lado Python: `test_p1_schemas::test_ac2_fixtures_validam`, `test_p6_contrato::test_fixtures_usam_so_valores_que_o_java_aceita` | **lado Java pendente (Kelwin)** |
| AC10 | `test_rede_bloqueada`, `test_p6_rastreabilidade::test_ac10_sem_rede_e_sem_chaves`; suíte em ~8 s (< 30 s) | **smoke real pendente (João Paulo)**: `scripts/smoke_llm.py` → `docs/evidencias/smoke-12-10.md` |

`test_p6_rastreabilidade.py` confere por código que cada teste citado na tabela existe.

**Pendências abertas (contrato §12):** A2 (lista definitiva de eventos de conduta, João Paulo) · A3 (classificador → 14 padrões, Release 2) · A5 (unidade de treino do classificador; hoje por turno) · A8 (aprovar as 14 expressões da seção do item 2, João Paulo) · A10 (SDD §6.2 apontar para o contrato v3, Kelwin + João Paulo). Fechadas: A1, A4, A6, A7, **A9 (503, hoje)**.
**Kelwin precisa:** (1) AC9, teste Java lendo `docs/contrato/resposta-v3-*.json` em `ContratoV3.Resposta`; (2) A10, atualizar o SDD §6.2; (3) saber que `PIPELINE_VERSAO=real` agora responde de verdade (llm1 → llm2 → local → regras) e que sem chaves as duas LLMs aparecem em `tentativas` como `nao_configurado`; (4) `tentativas[].duracaoMs`, `erro`, `avisos` e `versaoContrato` são campos extras que o Java ignora.
**Para o João Paulo decidir:** §8.3 diz `ok` de `regras` = sempre `true`, mas o item 4 permite `false` após falha real; o filtro de `interesse` do `local` (palavra-chave + risco < 0,3) é proposta minha; validar `compromissos` só do vendedor no código não foi feito.
```
.......................                                                  [100%]
239 passed in 7.49s
```

### §8.3 — semântica do /health (decisão)
- `ok` do motor = configurado E última tentativa real não falhou nos últimos 5 min (memória, por processo). A frase "`ok` de `regras` = sempre `true`" saiu do contrato. O `/health` nunca chama a API da LLM.
- `health.json` não muda (é o estado saudável). Testes que citam `regras: True` (`test_p5_estado.py`, `test_p5_health.py`) tratam estado saudável e continuam válidos; nenhum teste ou fixture afirma "regras sempre true" como regra.

### Baseline: estrutura do classificador de risco atual (D17)
Obtido com `python scripts/inspecionar_modelo.py` (scikit-learn 1.9.1). Só estrutura e hiperparâmetros; sem vocabulário nem texto.
- `Pipeline`: `tfidf=TfidfVectorizer` -> `clf=LogisticRegression`; `classes_ = [0, 1]` (1 = risco); `coef_.shape = (1, 20000)`.
- `TfidfVectorizer`: `analyzer='word'`, `lowercase=True`, `strip_accents=None`, `ngram_range=(1, 2)`, `min_df=5`, `max_df=0.6`, `max_features=20000` (vocabulário aprendido: 20000), `sublinear_tf=True`, `use_idf=True`, `smooth_idf=True`, `norm='l2'`, `binary=False`, `token_pattern='(?u)\b\w\w+\b'`, `stop_words` = lista de 315 itens (não impressa), `preprocessor=None`, `tokenizer=None`.
- `LogisticRegression`: `C=1.0`, `class_weight='balanced'`, `solver='lbfgs'`, `max_iter=1000`, `tol=0.0001`, `fit_intercept=True`, `random_state=42`, `l1_ratio=0.0` (`penalty='deprecated'`, comportamento da 1.9 equivalente a L2).
- Atenção ao reproduzir: `strip_accents=None` (o texto entra com acento) e a lista de stop words vem do artefato (`clone` dos steps), não de uma lista nova.

### 12/10 — smoke real das duas LLMs (prompt validado)
- llm1 (claude-haiku-5-5) e llm2 (gpt-4.1-mini) responderam e validaram no contrato v3, no pedido curto e na fixture P90
  (pior caso: 17,4 s, llm2). Fatos em `docs/evidencias/smoke-12-10.md`. O timeout do Java fica em 120 s.
- `PROMPT_VALIDADO_COM_LLM_REAL = True`; o aviso do `smoke_llm.py` só aparece se a constante voltar a falso (ex.: depois de
  mudar o prompt). Fecha a ressalva "prompt NÃO validado com LLM real" do AC3 e o smoke real pendente do AC10.

### 13/10 — `concorrente_citado` sem `sap` e `oracle` (decisão do João Paulo)
- Motivo: no corpus anonimizado, `oracle` aparece quase sempre como banco de dados ou nuvem do cliente, e `sap` não casa em nenhum trecho. Nome de concorrente é difícil de pegar pela palavra; o caminho é o contexto (llm1, llm2 e o classificador local).
- Medido sobre os 233.267 trechos (só contagens): a expressão casava em 467; 151 (32%) casavam só por `oracle` (nenhum por `sap`). Dos trechos que a destilação com `claude-haiku-5-5` também viu, a LLM marcou risco em 16 de 83 (19%) entre os que só casavam por `oracle`, contra 71 de 173 (41%) nos demais. A marca de risco da LLM é geral, não só concorrente: serve de indício, não de prova.
- Efeito: menos falso alarme de "concorrente citado" na demo e nos rótulos fracos que alimentam o retreino do modelo local. `rotulos_fracos.csv` precisa ser regerado antes do retreino.
- Contrato v3 e fixtures não mudam: o padrão continua o mesmo, só a expressão ficou mais estreita.
