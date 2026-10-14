# Contrato `POST /evidencias` (busca no histórico do cliente) — PROPOSTA

> **PROPOSTA, ainda não validada.** Só vale depois que o João Paulo e o Kelwin a validarem. Até lá o Python implementa
> exatamente o que está aqui, mas nomes e limites podem mudar. Mesmo molde do `similares.md`.

Versão: proposta de 14/10/2026. Contrato principal: `contrato-v3.md`. Irmão de `similares.md`: mesmo motor (cosseno
TF-IDF), pergunta diferente.

## 1. Para que serve

Na página do cliente, o vendedor digita uma pergunta ("o que falaram sobre prazo?") e vê os trechos das reuniões
anteriores que mais se parecem com ela. O Java carrega os turnos das transcrições do cliente, pseudonimiza e manda
junto com a consulta; o Python devolve só os `id` mais parecidos e o `score`. O Python não guarda nada: os trechos
vêm em cada pedido, e o corpo da resposta nunca repete texto.

## 2. Pedido

```json
{
  "consulta": "string, 1..500 caracteres (sem contar espaços nas pontas)",
  "trechos": [{"id": "string, 1..100", "texto": "string, 1..2000"}],
  "topK": 10
}
```

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `consulta` | string | sim | O que o usuário digitou. Vazio ou só espaços => 422 |
| `trechos` | lista | não (padrão `[]`) | 0 a 500 itens. `id` é do Java (opaco para o Python); `texto` é um turno da transcrição |
| `topK` | inteiro | não (padrão 10) | 1 a 50. Máximo de itens devolvidos |

Campos desconhecidos são ignorados. `id` repetido não é erro: cada trecho é avaliado. Não há `limiar` no pedido: volta
tudo o que tiver pelo menos uma palavra em comum (`score > 0`), até `topK`; quem corta por qualidade é a tela.

## 3. Resposta `200 OK`

```json
{
  "evidencias": [{"id": "12:3", "score": 0.1912}],
  "versaoContrato": "v3"
}
```

- `evidencias` em ordem de `score` decrescente (empate: ordem de chegada), no máximo `topK`.
- `score`: cosseno de 0 a 1, 4 casas decimais. Trecho com `score` 0 nunca volta.
- **Lista vazia é resposta válida**: sem trechos, nenhuma palavra em comum, ou consulta sem vocabulário útil (só stop
  words, números ou pontuação) => `{"evidencias": [], "versaoContrato": "v3"}`, nunca erro.

## 4. Erros

Mesmo formato do `contrato-v3.md` §8.1.

| HTTP | `codigo` | Quando |
|---|---|---|
| 422 | `pedido_invalido` | `consulta` ausente ou vazia, mais de 500 trechos, `topK` fora dos limites, trecho sem `id`/`texto` ou com `texto` acima de 2.000 |
| 500 | `erro_interno` | Defeito inesperado (corpo sem stack trace e sem texto) |

O `detalhes` do 422 traz só o caminho do campo e o tipo do problema, nunca o valor.

## 5. Como o score é calculado

É o de `similares.md` §5 (função `buscar_similares`): TF-IDF ajustado a cada pedido sobre `trechos + consulta`, sem
acento, `ngram_range=(1, 2)`, `sublinear_tf=True`, stop words do português; cosseno entre a `consulta` e cada trecho.
Sem API, sem LLM, sem estado. Por ser lexical, não acha sinônimo ("caro" não casa com "preço alto"); a calibração e a
troca por embeddings ficam para depois.

## 6. Como o Java usa

`GET /api/clientes/{id}/evidencias?q=` (JWT; só cliente que o usuário pode ver, senão 404).

1. Carrega as transcrições do cliente, da reunião mais recente para a mais antiga: até 20 transcrições e até 500
   turnos no total (os mais recentes). Turno vira `id` = `"{reuniaoId}:{n}"`.
2. Pseudonimiza `consulta` e turnos com o mesmo `Pseudonimizador` (cliente, contatos e consultores das reuniões
   carregadas), corta cada turno em 2.000 e envia com `topK: 10` e timeout de 3 s.
3. Resposta ao front: `{"evidencias": [{"texto", "reuniaoId", "turno", "data", "score"}], "aviso": null | "..."}`. O `texto`
   é o turno original, que nunca saiu do Java; o Python só viu o pseudônimo. `turno` é o `n` do turno na reunião (a
   tela abre `/reunioes/{reuniaoId}?turno={turno}`); `data` é a data e hora da reunião.
4. Qualquer falha (timeout, 4xx, 5xx, corpo inválido) vira `evidencias: []` com `aviso`, nunca 500. Cliente sem
   transcrição também vem vazio, com aviso próprio, e sem chamar o Python.

## 7. Fixtures

- `pedido-evidencias.json` — pedido sintético com 4 trechos.
- `resposta-evidencias.json` — resposta a esse pedido (o teste do Python confere que é exatamente o que o endpoint
  devolve).

## 8. Histórico

| Data | Mudança |
|---|---|
| 2026-10-14 | Primeira proposta. |
