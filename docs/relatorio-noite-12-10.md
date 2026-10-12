# Relatório do lote da noite — 12/10/2026

Lote sem supervisão. Regras: commits pequenos em nome de Joao, sem coautoria, pytest verde em cada commit, sem push,
nenhum texto de trecho em log ou relatório (só contagens e métricas), sem abrir `*_PRONTO.xlsx` nem `ouro_final.csv`, sem
editar `backend/`, `frontend/`, `*.joblib` nem `.env*`.

**Baseline do pytest:** `450 passed in 17.42s`.

**Mensagem cortada.** O pedido chegou truncado nas duas pontas: começa em "...os em nome de Joao" e termina no meio da
alínea 1b ("treinar.py registra no metadata.json, por grupo, se"). Este lote faz só o que chegou inteiro (item 0 e 1a) e a
1b na leitura mais conservadora (ver plano). O que vinha depois não chegou e não foi adivinhado.

As anotações do João em `docs/relatorio-tarde-12-10.md` (alteração local, não commitada) não foram tocadas nem commitadas.

---

## Item 0 — Smoke da llm1 e validação do prompt (um commit, com teste)

**Plano**
- a) `docs/evidencias/smoke-12-10.md`: a seção "llm1 PENDENTE" vira o resultado das 2 execuções (fatos do João, sem
  acrescentar nada): pedido curto (`docs/contrato/pedido-v3.json`, 12 turnos e 740 caracteres, conferido no arquivo) e
  fixture P90; conclusão "timeout do Java fica em 120 s".
- b) `PROMPT_VALIDADO_COM_LLM_REAL = True` em `app/engines/llm_engine.py` (e a docstring do módulo deixa de dizer que o
  prompt não foi validado). `scripts/smoke_llm.py`: o aviso "prompt NÃO validado" só é impresso se a constante for
  falsa. Testes: aviso some com a constante verdadeira e volta com ela falsa (monkeypatch, `rodar` simulado, sem rede);
  `test_p6_rastreabilidade`: AC10 sai de `PENDENTE` (o smoke real foi feito).
- c) `CLAUDE.md` da raiz, "Estado atual": smokes das duas LLMs ok.
- Coerência (mesmo commit, só texto): `docs/roteiro-ensaio-falha.md` (tira a pendência da llm1) e uma nota datada em
  `docs/decisoes.md` (o histórico antigo não é reescrito).

**Status:** concluído. Constante em `True`; aviso do smoke condicionado (`AVISO_PROMPT_NAO_VALIDADO`); 2 testes novos em
`test_smoke_script.py`; `test_gerar_transcricao_sintetica` deixou de supor que o aviso é a 1ª linha da saída; AC10 saiu
de `PENDENTE` (fica só o AC9, do Kelwin). Na evidência, "eventos de conduta" da P90 ficou "não registrado" (o dado não veio
no pedido). pytest: `452 passed`.

## Item 1a — LIMIAR_SIMILARIDADE 0.20 -> 0.25 (um commit, com teste)

**Plano**
- Medido antes de mudar (frases sintéticas já versionadas, scores com limiar 0): a fixture `pedido-similares.json` tem
  `np-101` = 0,259 e `np-104` = 0,2301. Com 0,25, a `np-104` (paráfrase) deixa de casar. Seguindo a regra do pedido, o
  limiar NÃO volta: a fixture de resposta passa a ter só `np-101`, e a frase e o score ficam registrados abaixo.
- Ordem: doc e fixture antes do código (`docs/contrato/similares.md` §2 e §5, `resposta-similares.json`), depois
  `app/similares.py`. Teste novo: o padrão é 0,25 e a paráfrase `np-104` só volta com `limiar=0.2` explícito.

## Item 1b — Veredito da professora no treino (um commit, com teste)

**Plano** (o texto do pedido acaba em "registra no metadata.json, por grupo, se")
- Rótulo de treino (3-D4) NÃO muda: LLM quando houver, senão regra.
- `validar_professora.py` grava `dados_locais/professora_veredito.json` no formato pedido:
  `{"risco": "usar"|"nao_usar", "oportunidade": ..., "interesse": ..., "data": "AAAA-MM-DD"}`. Opção `--veredito` para o
  caminho (os testes usam `tmp_path`; nenhum teste escreve em `dados_locais/`). Rodada PRELIMINAR (trecho sem resposta
  da LLM) não grava nem sobrescreve o arquivo: veredito só de comparação completa.
- `treinar.py` lê esse arquivo (opção `--veredito`, mesmo padrão) e registra no `metadata.json`, para cada modelo treinado
  (risco e interesse): o veredito da professora (`usar`, `nao_usar` ou `sem_veredito`) e quantos rótulos daquele grupo
  vieram da LLM e quantos da regra. Leitura escolhida para o "se" cortado: "se o rótulo da LLM usado no grupo foi
  aprovado pela professora". Grupo com rótulo da LLM e sem `usar` ganha um aviso no `metadata.json` (só contagem).

**Status 1a:** concluído. Limiar mantido em 0,25, como pedido. Paráfrases sintéticas que deixam de casar com o padrão
(frases já versionadas em `docs/contrato/` e `tests/`, nenhuma do corpus):

| Frase (sintética) | Referência | Score |
|---|---|---|
| "Os chamados do faturamento estão sem resposta do suporte há duas semanas." (`np-104`) | texto de `pedido-similares.json` | 0,2301 |
| "Ninguém do suporte retornou." | `SUPORTE` de `test_p7_similares.py` | 0,2055 |

A primeira mudou a fixture `resposta-similares.json` (só `np-101`, 0,259); a segunda não quebra teste (o teste dela manda
`limiar` explícito). Teste novo: padrão = 0,25 e a `np-104` só volta com `limiar: 0.2`. Também atualizados
`docs/contrato/similares.md` (§2 e §5) e `docs/handoff-kelwin-12-10.md` (exemplo e nota do limiar). **Avisar o Kelwin:** a
fixture de resposta do `/similares` perdeu um item (o formato não mudou). pytest: `453 passed`.

**Status 1b:** concluído na leitura conservadora (o fim da frase não chegou). `validar_professora.py` grava
`professora_veredito.json` só em rodada completa (`veredito_gravado` na saída diz o nome ou `null`). `treinar.py` lê o
arquivo (`ler_veredito`: sem arquivo => `sem_veredito`; JSON inválido ou valor fora de `usar`/`nao_usar` => para, sem
mostrar o conteúdo) e grava em `metadata.json` a chave `professora`: `arquivo`, `data` e, para risco e interesse,
`veredito`, `rotulos_llm` e `rotulos_regra`, mais `avisos` quando um grupo tem rótulo da LLM sem `usar`. Oportunidade
não entra porque o `treinar.py` não treina modelo de oportunidade. Testes novos: 2 no P9 e 5 no treino. Os testes
antigos passaram a usar caminhos temporários para o veredito; nada foi gravado em `dados_locais/`. pytest: `460 passed`.

---

## Fechamento

- pytest final: `460 passed` (baseline 450: +2 no item 0, +1 no 1a, +7 no 1b).
- Commits do lote (todos em nome de Joao, sem coautoria, sem push): `8b83c77` plano · `84a7473` item 0 · `ec26fd5` 1a ·
  `082376e` 1b · e o deste fechamento.
- `git ls-files`: nenhum `.xlsx` nem `.csv`; só os dois `.env.example` e o `classificador_risco.joblib` que já existiam.
  `backend/`, `frontend/` e `*.joblib` sem mudança. Nenhum teste gravou em `dados_locais/`.
- **Não chegou:** o resto da alínea 1b e o que vinha depois. Nada disso foi adivinhado.

### Decisões para o João validar
1. **Mensagem cortada:** só o item 0, a 1a e a 1b foram feitos; o resto do pedido não chegou.
2. **Smoke (item 0):** na P90 da llm1, "eventos de conduta" ficou "não registrado" e não "0", porque o dado não veio.
   Também não escrevi "validou" para a P90, pelo mesmo motivo.
3. **Item 0:** AC10 saiu de `PENDENTE` no teste de rastreabilidade; `decisoes.md` ganhou uma nota datada (o histórico de
   11/10 não foi reescrito); o roteiro da demo perdeu a pendência da llm1.
4. **1a:** a fixture `resposta-similares.json` perdeu a `np-104` (0,2301) e o `handoff-kelwin-12-10.md` foi atualizado.
   Falta avisar o Kelwin.
5. **1b, o "se" cortado:** registra por modelo o veredito da professora e quantos rótulos vieram da LLM e da regra, com
   aviso quando há rótulo da LLM sem `usar`. O rótulo de treino não mudou (3-D4).
6. **1b:** rodada PRELIMINAR não grava nem sobrescreve o `professora_veredito.json`.
7. **1b:** o `metadata.json` registra só risco e interesse (os modelos treinados). Oportunidade fica só no veredito.
8. **1b:** um `professora_veredito.json` inválido para o treino com erro claro, em vez de seguir como `sem_veredito`.
