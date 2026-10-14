# Contrato `POST /similares` (RAG-lite) — PROPOSTA

> **PROPOSTA, ainda não validada.** Este contrato só vale depois que o João Paulo e o Kelwin o validarem. Até lá o
> Python implementa exatamente o que está aqui, mas nomes, limites e o valor do limiar podem mudar. Desde 14/10 o
> Java consome o endpoint (§6), sempre de forma opcional: se ele sumir, a análise segue igual.

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
| `limiar` | número | não (padrão `LIMIAR_SIMILARIDADE` = 0,25) | 0 a 1. Só volta referência com `score >= limiar` |

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

`LIMIAR_SIMILARIDADE = 0.25` (decisão do João Paulo em 12/10; era 0,2). Com frases SINTÉTICAS, paráfrases do mesmo
assunto ficaram entre ~0,2 e ~0,35 e assuntos diferentes até ~0,14. Com 0,25 as paráfrases mais distantes deixam de
casar: a `np-104` da fixture ("Os chamados do faturamento estão sem resposta do suporte há duas semanas.", score
0,2301) saiu de `resposta-similares.json`. Quem quiser o corte antigo manda `limiar: 0.2` no pedido.
**Calibração real pendente** com o conjunto ouro (P8).

## 6. Como o Java usa (implementado em 14/10)

1. `ClienteSimilares`: mesma base URL do `/analisar`, timeout de 3 s (conexão e leitura), `topK: 1`, sem `limiar`
   (vale o padrão do Python, 0,25).
2. Depois do `/analisar`, uma consulta por padrão dos temas devolvidos: `texto` = `texto` do tema (já
   pseudonimizado), `referencias` = os "não procede" vigentes do mesmo cliente (até 200; `id` = **id do tema**
   marcado no Java, em string; `texto` = a citação desse tema, pseudonimizada com o mesmo mapa e cortada em 2.000).
   Cliente sem "não procede" => nenhuma chamada.
3. Só o tema **novo** guarda o resultado (`Tema.semelhanteNaoProcedeId`, coluna anulável). O frontend recebe
   `semelhanteNaoProcede: {id, texto, clienteNome} | null`; volta `null` se o tema de referência deixou de ser
   "não procede".
4. Qualquer falha (timeout, 4xx, 5xx, corpo inválido) vira só um log sem texto; as consultas restantes daquela
   análise são puladas, para nunca somar 3 s por tema. O `/analisar` nunca falha por causa do `/similares`.

## 7. Fixtures

- `pedido-similares.json` — pedido sintético com 4 referências.
- `resposta-similares.json` — resposta a esse pedido com o limiar padrão (o teste do Python confere que ela é
  exatamente o que o endpoint devolve).

## 8. Histórico

| Data | Mudança |
|---|---|
| 2026-10-12 | Primeira proposta (P7). |
| 2026-10-14 | Java passa a consumir (§6): `id` = id do tema, `topK: 1`, timeout 3 s, falha ignorada. Formato do endpoint inalterado. |
