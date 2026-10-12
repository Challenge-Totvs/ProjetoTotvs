---
name: p7-similares
description: Tarefa P7 — POST /similares (RAG-lite sem API): similaridade TF-IDF entre um tema novo e os trechos "não procede" do cliente. Contrato e fixtures primeiro, depois endpoint e testes.
disable-model-invocation: true
---
Tarefa P7. Ciclo do `CLAUDE.md`. Modelo sugerido: sonnet (esforço médio).
Autorizada pelo João Paulo: `/similares` sai do "Fora do escopo" do `CLAUDE.md` (RAG-lite apenas).

Leia: `docs/escopo-rag-retreino.md` §2.A; `docs/contrato/contrato-v3.md` §3, §8.1 (formato de erro);
`app/router.py`, `app/schemas.py`; `analise-service/tests/conftest.py`.

Para que serve (uma frase para o resumo): quando o cliente marca um tema como "não procede", o Java guarda o trecho;
quando surgir um tema novo, o Java pergunta ao Python se ele se parece com algum "não procede" anterior daquele cliente
e, se sim, avisa o usuário ("semelhante a um tema que você já descartou").

Contrato PROPOSTO (ajuste só se o código do Java exigir; a decisão final é do João Paulo):
- Pedido: `{"texto": str (1..2000), "referencias": [{"id": str, "texto": str}] (0..200), "topK": int (padrão 3),
  "limiar": float 0..1 (opcional)}`
- Resposta 200: `{"similares": [{"id": str, "score": float}], "versaoContrato": "v3"}` ordenada por score decrescente,
  só com score >= limiar; lista vazia é resposta válida.
- Erro: 422 `pedido_invalido` no formato do §8.1. Nada de stack trace nem texto no corpo.

Escopo, nesta ordem:
1. CONTRATO ANTES DO CÓDIGO: documente em `docs/contrato/similares.md` e crie as fixtures
   `docs/contrato/pedido-similares.json` e `resposta-similares.json` (sintéticas). Avise o João Paulo no resumo
   (ele avisa o Kelwin, que cria o cliente Java; o Java ignora falha do `/similares` em silêncio).
2. `app/similares.py`: sem API e sem dependência nova (`scikit-learn` já está pinado). `TfidfVectorizer` ajustado a cada
   pedido sobre `referencias + texto` (sem estado entre pedidos), minúsculas, sem acento, `ngram_range=(1, 2)`,
   `sublinear_tf=True`; similaridade do cosseno entre `texto` e cada referência. Limiar como CONSTANTE NOMEADA
   (`LIMIAR_SIMILARIDADE`); escolha o valor inicial com exemplos sintéticos e deixe a calibração real para depois.
   Sem referências ou texto sem vocabulário útil => lista vazia, nunca erro.
3. `POST /similares` no router, validado por schemas Pydantic (limites acima). Logs só com tamanhos e quantidades.
4. Testes sintéticos: frase quase igual casa; frases de assuntos diferentes não casam; ordem por score; `topK`;
   sem referências; texto vazio => 422; limite de 200 referências; resposta valida contra a fixture; nenhuma chamada de rede.
5. `python -m pytest -q` verde. Commit `feat(P7): POST /similares (TF-IDF, sem API)`.

Não faça: embeddings, chamada a LLM, persistência de referências no Python, mudança em `backend/` ou `frontend/`.
Pendências para o resumo: cliente Java (Kelwin), campo `semelhanteNaoProcede` na resposta do Java (Kelwin),
calibração do `LIMIAR_SIMILARIDADE` com o conjunto ouro (P8).
