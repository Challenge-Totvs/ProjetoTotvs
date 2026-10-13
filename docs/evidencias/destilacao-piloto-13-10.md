# Piloto de destilação — 13/10/2026

Só contagens e métricas; nenhum texto de trecho. Comando (a partir de `analise-service/`):

    python treino/rotulos_fracos.py --trechos dados_locais/trechos.csv --destilar --motor llm1 --modelo claude-haiku-5-5 --amostra 300 --teto-usd 0.30 --preco-entrada 0.10 --preco-saida 0.50

- Professora: `claude-haiku-5-5` (llm1), a opção mais barata (preço oficial: US$ 0,10 por milhão de tokens de entrada e
  US$ 0,50 de saída).
- Amostra: 300 trechos candidatos (70% com acerto de regra, 30% sem; semente 42), de 233.267 trechos fora do holdout.
- Resultado: **300 rotulados**, 0 sem resposta, 15 chamadas (lotes de 20), sem erro, **não chegou ao teto**.
- **Custo real: US$ 0,0162** (117.152 tokens de entrada × 0,10 + 8.949 de saída × 0,50, por milhão), contra um teto de
  US$ 0,30. Lote mais caro: US$ 0,0015.

## Concordância LLM × regra (nos 300 destilados)

| Grupo | concordância | regra 1 / LLM 1 | regra 1 / LLM 0 | regra 0 / LLM 1 | regra 0 / LLM 0 |
|---|---|---|---|---|---|
| risco | 0,810 | 33 | 23 | 34 | 210 |
| oportunidade | 0,803 | 37 | 32 | 27 | 204 |
| interesse | 0,760 | 34 | 60 | 12 | 194 |

Leitura: concordância **não é acerto**. A amostra foi feita para ter 70% de trechos com acerto de regra, então não
representa o corpus. Em interesse, a LLM marca bem menos que a regra (46 contra 94 positivos): a regra de palavra-chave
tende a marcar demais, ou a LLM é mais rígida. Só o P9 (`validar_professora.py`, contra o ouro do João) diz qual das
duas acerta. Até lá, o `metadata.json` do treino registra esses rótulos como `sem_veredito`.

Efeito no `rotulos_fracos.csv` (rótulo de treino = LLM quando houver, senão regra): positivos de risco 958 => 969,
oportunidade 1.241 => 1.236, interesse 1.500 => 1.452.

Destilação completa NÃO foi rodada. Estimativa para os ~3.000 do escopo, no mesmo custo por trecho: ~US$ 0,16.
