# Contrato `POST /similares` (RAG-lite) — PROPOSTA

> **PROPOSTA, ainda não validada.** Este contrato só vale depois que o João Paulo e o Kelwin o validarem. Até lá o
> Python implementa exatamente o que está aqui, mas nomes, limites e o valor do limiar podem mudar. Nenhum código Java
> depende dele ainda.

Versão: proposta de 12/10/2026 (P7). Contrato principal: `contrato-v3.md`. Escopo: `docs/escopo-rag-retreino.md` §2.A.

## 1. Para que serve

Quando o cliente marca um tema como "não procede", o Java guarda o trecho. Quando surgir um tema novo, o Java pergunta
ao Python se ele se parece com algum "não procede" anterior daquele cliente; se sim, avisa o usuário ("semelhante a um
tema que você já descartou"). O Python não guarda nada: as referências vêm em cada pedido.

## 2. Pedido

```json
{
  "texto": "string, 1..2000 caracteres (sem contar espaços nas pontas)",
  "referencias": [{"id": "string, 1..100", "texto": "string, 1..2000"}],
  "topK": 3,
  "limiar": 0.2
}
```

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `texto` | string | sim | Texto do tema novo (o `texto` do tema). Vazio ou só espaços => 422 |
| `referencias` | lista | não (padrão `[]`) | 0 a 200 itens. `id` é do Java (opaco para o Python); `texto` é o trecho "não procede" |
| `topK` | inteiro | não (padrão 3) | 1 a 50. Máximo de itens devolvidos |
| `limiar` | número | não (padrão `LIMIAR_SIMILARIDADE` = 0,2) | 0 a 1. Só volta referência com `score >= limiar` |

Campos desconhecidos são ignorados (como no `/analisar`). `id` repetido não é erro: cada referência é avaliada.

## 3. Resposta `200 OK`

```json
{
  "similares": [{"id": "np-17", "score": 0.6123}],
  "versaoContrato": "v3"
}
```

- `similares` em ordem de `score` decrescente (empate: ordem de chegada), no máximo `topK`, só com `score >= limiar`.
- `score`: similaridade do cosseno, de 0 a 1, com 4 casas decimais. Referência com `score` 0 (nenhuma palavra em
  comum) nunca volta, mesmo com `limiar: 0`.
- **Lista vazia é resposta válida**: sem referências, nada acima do limiar, ou texto sem vocabulário útil (só stop words,
  só números ou pontuação) => `{"similares": [], "versaoContrato": "v3"}`, nunca erro.
- O corpo nunca repete texto do pedido: só `id` e `score`.

## 4. Erros

Mesmo formato do `contrato-v3.md` §8.1.

| HTTP | `codigo` | Quando |
|---|---|---|
| 422 | `pedido_invalido` | `texto` ausente ou vazio, mais de 200 referências, `topK` ou `limiar` fora dos limites, referência sem `id`/`texto` |
| 500 | `erro_interno` | Defeito inesperado (corpo sem stack trace e sem texto) |

O `detalhes` do 422 traz só o caminho do campo e o tipo do problema (`ausente`, `vazio`, `invalido`), nunca o valor.

**O Java ignora qualquer falha do `/similares` em silêncio**: timeout, 4xx ou 5xx => o tema segue sem
`semelhanteNaoProcede`. A análise principal (`/analisar`) não depende deste endpoint.

## 5. Como o score é calculado

TF-IDF ajustado a cada pedido sobre `referencias + texto` (sem estado entre pedidos), palavras em minúsculas e sem
acento, `ngram_range=(1, 2)`, `sublinear_tf=True`, uma lista curta de stop words do português (constante no código);
cosseno entre `texto` e cada referência. Sem API, sem LLM, sem dependência nova (`scikit-learn` já pinado).

`LIMIAR_SIMILARIDADE = 0.2` foi escolhido com frases SINTÉTICAS (paráfrases do mesmo assunto ficaram entre ~0,2 e ~0,35;
assuntos diferentes, até ~0,14). **Calibração real pendente** com o conjunto ouro (P8).

## 6. O que o Java precisa implementar (Kelwin)

1. Cliente HTTP do `/similares` (mesma base URL do `/analisar`), com timeout curto (sugestão: 3 s).
2. Para cada tema novo: enviar `texto` do tema e os trechos "não procede" do mesmo cliente como `referencias`
   (`id` = id do registro no Java).
3. Campo `semelhanteNaoProcede` (ex.: `id` da referência mais parecida, ou booleano) no tema devolvido ao frontend.
4. Ignorar falha em silêncio (log no Java, sem erro para o usuário).

## 7. Fixtures

- `pedido-similares.json` — pedido sintético com 4 referências.
- `resposta-similares.json` — resposta a esse pedido com o limiar padrão (o teste do Python confere que ela é
  exatamente o que o endpoint devolve).

## 8. Histórico

| Data | Mudança |
|---|---|
| 2026-10-12 | Primeira proposta (P7). |
