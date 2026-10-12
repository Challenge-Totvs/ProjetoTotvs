---
paths:
  - "analise-service/**"
---

# Convenções do analise-service

Contrato: leia `docs/contrato/contrato-v3.md` (§3 pedido, §4 resposta) antes de mexer em
schemas, motores ou testes. Fixtures em `docs/contrato/*.json`.

- Python com type hints; Pydantic v2 (`model_validate`, `model_json_schema`).
- Dois schemas distintos: `SaidaLLM` (o que a LLM preenche) e `AnaliseResponse` (o que a API devolve).
  `motor`, `tentativas`, `versaoContrato` e `descartados` são preenchidos pelo código, nunca pela LLM.
- `SaidaLLM` precisa ser compatível com saída estruturada estrita da OpenAI: sem `dict` livre
  nem tuplas; use listas de objetos. Dicts do contrato (ex.: `papeis`) são montados depois, em código.
- Enums do contrato (`motor`: llm1|llm2|local|regras; `sentimento` em minúsculas; os 14 padrões)
  são fechados. Valor fora da lista faz o Java responder 503 ao usuário: nunca invente valor.
- Pedido: aceitar campos extras (`contextoCliente`, `glossarioTime`, `correcoesAnteriores`) sem erro.
- Configuração lida em um único módulo `app/config.py` (variáveis de ambiente, timeouts,
  `PIPELINE_VERSAO`). Nada de `os.environ[...]` espalhado.
- Erros do domínio em `app/erros.py` (ex.: `AnaliseIndisponivel`). O router converte em
  503 `analise_indisponivel` com corpo JSON (contrato §8.1).
- Log com `logging.getLogger(__name__)`; nunca `print`; nunca texto de transcrição.
- Nada de rede nem I/O pesado no import. O app sobe sem `.joblib` e sem chaves; o modelo
  local é carregado de forma preguiçosa, com erro explícito.
- Clients de LLM criados com `timeout` explícito e `max_retries=0`; a política de retry é do nosso código.
- Testes: `pytest`, `monkeypatch` nos clients, transcrições sintéticas em `tests/fixtures/`.
  Um teste por critério de aceite (AC1..AC10 em `docs/contrato/contrato-v3.md` §10).
  O `conftest.py` (hoje vazio; P0 o preenche) bloqueia sockets em teste: depois de criado, não remova.
