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
