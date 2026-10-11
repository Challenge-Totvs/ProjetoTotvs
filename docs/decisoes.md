# Decisões e pendências — analise-service

Última atualização: 11/10/2026. Registre aqui toda decisão tomada durante as tarefas.
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

## Bloqueios
(nenhum até agora)

## Registro de execução — lote de 12/10
