# Portão do modelo local — H2 Parte B (destilação real) — 2026-10-14

Só métricas; nenhum texto de trecho. Gerado por `treino/portao.py`.

Esta é a rodada do candidato treinado com a destilação real do H1 (233.267 trechos, 70.783 com rótulo
`fonte=llm`, 162.484 por regra), excluindo os trechos marcados como suspeitos pelo confident learning
(`treino/rotulos_suspeitos.py`, GroupKFold agrupado por cliente, 267 clientes, 5 dobras): 43.057 excluídos em
risco (18,5%) e 30.658 em interesse (13,1%). Antes desta rodada, o portão só tinha sido rodado contra o
candidato da destilação-piloto (300 trechos, `2026-10-13_2`) — ver `docs/evidencias/portao-2026-10-14.md`.
O ouro usado é o mesmo PARCIAL (83 trechos) nas duas rodadas; o P9 no ouro real/completo ainda não rodou
(pendência registrada em `CLAUDE.md`), então esta comparação antes/depois é sobre o candidato, não sobre
o ouro.

- Candidato: `2026-10-14` (scikit-learn 1.9.1, dados sha256 `8ab621b8911f`, mudanças de hiperparâmetro: 0)
- Ouro: modo **unico**, **PARCIAL**; kappas: {}
- Trechos avaliados: 79 (fora por dúvida: 4)
- Limiares: risco >= 0.6; filtro atual de interesse = palavra-chave E risco < 0.3; candidato de interesse >= 0.5
- Limitação: Rotulador único (João Paulo), sem validação cruzada entre pessoas; ele também escreveu as expressões regulares. A concordância medida é teste-reteste (consigo mesmo).

## Por grupo

| Grupo / lado | precisão (Wilson 95%) | revocação (Wilson 95%) | F1 | positivos/n | matriz de confusão |
|---|---|---|---|---|---|
| risco — atual | 0.3333 ([0.1518, 0.5829]) | 0.4167 ([0.1933, 0.6805]) | 0.3704 | 12/79 | tp=5 fp=10 fn=7 tn=57 |
| risco — candidato | 0.25 ([0.1325, 0.4211]) | 0.6667 ([0.3906, 0.8619]) | 0.3636 | 12/79 | tp=8 fp=24 fn=4 tn=43 |
| risco — baseline Dummy (sem sinal) | 0.3636 ([0.1517, 0.6462]) | 0.3333 ([0.1381, 0.6094]) | 0.3478 | 12/79 | tp=4 fp=7 fn=8 tn=60 |
| interesse — atual | 1.0 ([0.6756, 1.0]) | 0.1111 ([0.0574, 0.2042]) | 0.2 | 72/79 | tp=8 fp=0 fn=64 tn=7 |
| interesse — candidato | 0.8 ([0.4902, 0.9433]) | 0.1111 ([0.0574, 0.2042]) | 0.1951 | 72/79 | tp=8 fp=2 fn=64 tn=5 |
| interesse — baseline Dummy (sem sinal) | 0.9014 ([0.8102, 0.9514]) | 0.8889 ([0.7958, 0.9426]) | 0.8951 | 72/79 | tp=64 fp=7 fn=8 tn=0 |
| oportunidade — atual | 0.5333 ([0.3012, 0.7519]) | 0.5333 ([0.3012, 0.7519]) | 0.5333 | 15/79 | tp=8 fp=7 fn=7 tn=57 |
| oportunidade — candidato | — | — | — | — | — |
| risco — referência: só regex | 0.3636 ([0.1973, 0.5705]) | 0.6667 ([0.3906, 0.8619]) | 0.4706 | 12/79 | tp=8 fp=14 fn=4 tn=53 |

## Decisão

- **risco**: IC95% da diferença de F1 = [-0.25, 0.2261]; IC95% da diferença de precisão = [-0.3131, 0.1167]; discordância atual×candidato = 27 trecho(s); REPROVADO: mantém o atual
  - motivos: F1 0.3636 < atual 0.3704
- **interesse**: IC95% da diferença de F1 = [-0.165, 0.1565]; IC95% da diferença de precisão = [-0.5, 0.0]; discordância atual×candidato = 16 trecho(s); REPROVADO: mantém o atual
  - motivos: F1 0.1951 < atual 0.2
- **oportunidade**: sem candidato (expressões nos dois lados); só informativo.

## Antes (destilação-piloto) × depois (destilação real + confident learning)

| Grupo | F1 antes (`2026-10-13_2`) | F1 depois (`2026-10-14`) | Diferença |
|---|---|---|---|
| risco | 0.1333 | 0.3636 | +0.2303 (melhora, mas ainda abaixo do atual: 0.3704) |
| interesse | 0.241 | 0.1951 | -0.0459 (piora) |

O candidato de risco melhorou bastante com dados reais (mais recall: tp 5→8 de 12 positivos), mas ainda não
supera o atual nem passa no portão — o F1 ficou perto (0.3636 vs 0.3704) com IC95% largo ([-0.25, 0.2261]),
o que é esperado com só 79 trechos de ouro. O candidato de interesse piorou de precisão com a exclusão de
suspeitos (1.0→0.8 no antes/depois anterior já não era o caso; aqui 0.8 vs atual 1.0) sem ganhar recall
(continua 0.1111 — baseline Dummy tem 0.8889 de recall porque a classe é desbalanceada a favor de interesse,
então o "sem sinal" já acerta a maioria). Em ambos os grupos, **REPROVADO: mantém o atual**. A amostra de
ouro PARCIAL (79-83 trechos) é a limitação central: os IC95% das duas rodadas incluem zero, não dá para
afirmar melhora nem piora com confiança — o resultado muda de verdade quando o ouro completo (P9) rodar.

## Por padrão (APENAS INDICATIVO: ~8 trechos por padrão)

| Padrão | trechos no ouro | regex acerta | regex alarme falso |
|---|---|---|---|
| suporte_insatisfacao | 0 | 0 | 0 |
| preco_objecao | 0 | 0 | 2 |
| prazo_implantacao | 2 | 2 | 2 |
| concorrente_citado | 1 | 1 | 2 |
| cancelamento_citado | 6 | 3 | 0 |
| adocao_resistencia | 0 | 0 | 2 |
| fiscal_problema | 2 | 1 | 3 |
| orcamento_restrito | 1 | 1 | 3 |
| expansao_unidade | 1 | 1 | 2 |
| modulo_adicional | 3 | 1 | 1 |
| integracao | 6 | 2 | 1 |
| renovacao | 0 | 0 | 2 |
| upgrade_licencas | 3 | 2 | 0 |
| treinamento | 2 | 2 | 1 |
