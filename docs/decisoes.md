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
4. `concorrente_citado` (risco): `\b(concorrent\w*|outro\s+fornecedor|outra\s+empresa|outro\s+sistema|outra\s+solucao|sap|oracle|omie|bling)\b`
5. `cancelamento_citado` (risco): `\b(cancel\w*|rescind\w*|rescis\w*|encerrar\s+(o\s+)?contrato|nao\s+(vamos|vou|pretendemos)\s+renovar|deixar\s+de\s+usar)\b`
6. `adocao_resistencia` (risco): `\b(equipe|time|pessoal|usuarios|funcionarios|colaboradores)\b.{0,60}\b(resist\w*|nao\s+(usa\w*|quer\w*|adaptou|se\s+adapt\w*|gost\w*)|dificuldade)|\b(resistencia|ninguem\s+usa)\b`
7. `fiscal_problema` (risco): `\b(fiscal|sped|nfe|nf-e|imposto\w*|tribut\w*|apuracao)\b.{0,80}\b(erro\w*|problema\w*|falh\w*|travou|nao\s+(fecha|fechou|bate|gera\w*)|divergen\w*|rejei\w*)|\b(erro\w*|problema\w*|falh\w*|divergen\w*|rejei\w*)\b.{0,80}\b(fiscal|sped|nfe|nf-e|imposto\w*|tribut\w*|apuracao)\b`
8. `orcamento_restrito` (risco): `\b(orcamento|verba|caixa|budget)\b.{0,60}\b(apertad\w*|curto|limitad\w*|restrit\w*|cortad\w*|congelad\w*|estourad\w*|sem\s+folga)|\b(sem\s+verba|sem\s+orcamento|corte\s+de\s+(custos|orcamento)|congelamento\s+de\s+(gastos|orcamento)|congel\w+\s+(novas\s+)?compras)\b`
9. `expansao_unidade` (oportunidade): `\b(nova|novo|outra|mais\s+uma)\s+(unidade|filial|loja|sede|clinica)\b|\b(unidade|filial|loja|sede)\s+nova\b|\b(abrir|abrindo|inaugur\w*|expandir)\b.{0,50}\b(unidade|filial|loja|sede|clinica)\b|\bexpansao\b`
10. `modulo_adicional` (oportunidade): `\b(modulos?|add-?on|business\s+intelligence|telemedicina)\b|\b(queremos|querem|gostaria\w*|interesse\s+em|precisamos\s+de)\b.{0,40}\b(dashboard|painel|bi)\b`
11. `integracao` (oportunidade): `\b(integra\w*|api|webservice|web\s+service|sincroniz\w*|conectar\s+com)\b`
12. `renovacao` (oportunidade): `\b(renova\w*|prorrog\w*|continuidade\s+do\s+contrato|estender\s+o\s+contrato)\b`
13. `upgrade_licencas` (oportunidade): `\b(mais|novas|adicionais|ampliar|aumentar|comprar)\b.{0,30}\blicenc\w*|\blicenc\w*\b.{0,30}\b(adicionais|extras?)\b|\bupgrade\b|\bmais\s+usuarios\b|\busuarios\s+adicionais\b|\bplano\s+(maior|superior)\b`
14. `treinamento` (oportunidade): `\b(treinament\w*|treinar|capacita\w*|onboarding|workshop|reciclagem|aprender\s+a\s+usar)\b`

Interesse (palavras-chave): `\b(ajuda\s+bastante|ajuda\s+muito|gostei\w*|interessante|interessad[oa]|otimo|excelente|perfeito|combinado|fechado|vamos\s+fechar|pode\s+enviar|manda\s+a\s+proposta|queremos\s+avancar)\b`
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
