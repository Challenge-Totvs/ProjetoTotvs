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
