# Checagem pré-demo — 13/10/2026 (`scripts/pre_demo.py`)

Só status, contagens e tempos; nenhum texto de transcrição. Pedidos sintéticos: o curto do contrato
(`docs/contrato/pedido-v3.json`, 12 turnos) e o grande de `scripts/gerar_transcricao_sintetica.py` (399 turnos, ~72 mil
caracteres, semente 42). `/similares` com 3 referências sintéticas do próprio script. Serviço local em
`127.0.0.1:8000`, chaves do `.env` (`ANTHROPIC_API_KEY` removida da sessão), reiniciado a cada cenário.

## Comandos exatos (a partir de `analise-service/`)

| Cenário | Subida do serviço | Checagem |
|---|---|---|
| normal | `unset ANTHROPIC_API_KEY FORCAR_FALHA PIPELINE_VERSAO; .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000` | `.venv/Scripts/python.exe scripts/pre_demo.py` |
| llm1 forçada a falhar | `unset ANTHROPIC_API_KEY PIPELINE_VERSAO; FORCAR_FALHA=llm1 .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000` | `.venv/Scripts/python.exe scripts/pre_demo.py` |
| mock | `unset ANTHROPIC_API_KEY FORCAR_FALHA; PIPELINE_VERSAO=mock .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000` | `.venv/Scripts/python.exe scripts/pre_demo.py` |

## Resultado

| Item | normal | `FORCAR_FALHA=llm1` | `PIPELINE_VERSAO=mock` |
|---|---|---|---|
| a) `GET /health` | OK · 0,0 s · status ok, 4 motores ok | FALHOU · 0,1 s · status ok, llm1 X | OK · 0,0 s · pipeline mock, 4 motores ok |
| b) `/analisar` curta (12 turnos) | OK · **5,5 s** · llm1 · 5 temas · 0 turnos inválidos | FALHOU · **8,7 s** · llm2 (llm1: erro_provedor > llm2: ok) · 3 temas · 0 inválidos | OK · 0,0 s · llm1 (resposta gravada) · 3 temas |
| c) `/analisar` grande (399 turnos) | OK · **6,4 s** · llm1 · 6 temas · 0 turnos inválidos | FALHOU · **21,0 s** · llm2 (llm1: erro_provedor > llm2: ok) · 6 temas · 0 inválidos | OK · 0,0 s · llm1 (resposta gravada) · 3 temas |
| d) `/similares` (3 referências) | OK · 0,0 s · 1 similar | OK · 0,0 s · 1 similar | OK · 0,0 s · 1 similar |
| e) resumo | **PRONTO PARA A DEMO** (saída 0) | **NAO PRONTO**: a, b, c (saída 2) | **PRONTO PARA A DEMO** (saída 0) |
| tempo total do script | 12 s | 30 s | 0 s |

Antes de subir o serviço, o script avisou em uma linha `FALHOU servico fora do ar em http://localhost:8000` e saiu
com código 1.

## Leitura
- Normal: as duas transcrições respondem pela llm1 em ~6 s, bem abaixo dos 120 s do Java.
- `FORCAR_FALHA=llm1`: o script acusa a queda (health e motor), e a cadeia segue respondendo pela llm2. A llm2 é
  mais lenta na transcrição grande (21 s), ainda dentro do prazo.
- Mock: o script dá PRONTO porque não exige `pipelineVersao=real`. A linha do health mostra `pipeline=mock`: confira
  isso antes da banca.
- O host padrão é `127.0.0.1`. No Windows, `localhost` tenta IPv6 primeiro e somou ~2 s a cada chamada na primeira
  rodada.
