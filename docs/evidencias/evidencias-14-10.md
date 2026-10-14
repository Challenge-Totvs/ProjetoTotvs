# Busca no histórico do cliente (`/evidencias`) — relatório de 14/10

Branch `evidencias`, a partir de `origin/integracao-14-10` (3152746). Contrato: `docs/contrato/evidencias.md`
(PROPOSTA, no molde do `similares.md`).

## O que entrou

| Camada | O que | Onde |
|---|---|---|
| Contrato | Doc + fixtures sintéticas de pedido e resposta | `docs/contrato/evidencias.md`, `pedido-evidencias.json`, `resposta-evidencias.json` |
| Python | `POST /evidencias`, sem estado, cosseno TF-IDF via `buscar_similares` (limiar 0, só `score > 0`) | `app/router.py`, `app/schemas.py`, `tests/test_evidencias.py` |
| Java | `GET /api/clientes/{id}/evidencias?q=`: 20 transcrições mais recentes, até 500 turnos, pseudonimiza, timeout de 3 s | pacote `domain/evidencia` |
| Front | Seção "Buscar no histórico" na página do cliente: caixa, lista (trecho, data, link "Abrir na reunião") | `components/cliente/BuscaHistorico.tsx` |

Limites (os mesmos no Python e no Java): consulta 1..500 caracteres; até 500 trechos de 1..2.000 caracteres; `topK`
1..50 (Java manda 10).

## Decisões que fugiram do texto do pedido

- **Resposta do Python é um objeto**, `{"evidencias": [{id, score}], "versaoContrato": "v3"}`, não uma lista nua:
  mesmo molde do `/similares` e deixa espaço para campos novos.
- **Resposta do Java** é `{evidencias: [{texto, reuniaoId, turno, data, score}], aviso}`. `turno` é acréscimo: a
  página da reunião já abre em `?turno=N`, então o link cai direto no trecho. `aviso` carrega a mensagem de falha.
- **Pseudonimização**: a consulta e os turnos usam o mesmo `Pseudonimizador` (cliente, contatos, consultores das reuniões
  carregadas e o usuário). O texto devolvido ao front é o turno original, que nunca saiu do Java. A regra de montar as
  entidades (nome completo + primeiro nome) foi copiada do `AnaliseService` para não mexer no `/analisar`.
- **Acesso**: o cliente passa pela mesma regra de `GET /api/clientes/{id}` (404 se não é do usuário). Para isso,
  `ClienteService.podeVer` passou de `private` para `public`; é a única mudança em código existente além do método novo
  em `TranscricaoRepository`.
- **Consulta vazia ou com mais de 500 caracteres** é 400 (`consulta_vazia`, `consulta_longa`); falha do Python é lista
  vazia com aviso, nunca 500.
- Cliente sem transcrição: lista vazia com aviso próprio, sem chamar o Python.
- A busca é lexical (TF-IDF): "caro" não casa com "preço alto". Embeddings ficam para depois.

Não foram tocados: `/analisar`, a cadeia de motores, `/similares`, `*.joblib`, `.env`, contratos existentes.

## Verificação (14/10)

| Checagem | Resultado |
|---|---|
| `pytest` (analise-service) | 507 passaram (47 só de `/evidencias` + `/similares`) |
| `mvn test` (JDK 25) | 172 testes, 1 erro: `ApiApplicationTests.contextLoads` (falta o Oracle), como previsto |
| Testes Java novos | `EvidenciaServiceTest` (sucesso, timeout, 5xx, Python fora do ar, sem transcrição, nada parecido, consulta inválida) e `HistoricoDoClienteTest` (ordem, limite de turnos, 404) |
| `npm run build` | ok |
| `npm run lint` | 0 erros (os avisos que já existiam em `AppContext`, `AuthContext` e `PadroesPage` continuam) |

**Não testado ponta a ponta**: o backend não sobe sem o Oracle nesta máquina, então a tela nunca falou com o Java real.
O roteiro abaixo cobre isso.

## Roteiro de teste manual (5 passos)

Pré-requisito: Oracle no ar, Python (`uvicorn app.main:app`), Java e front rodando; um cliente da demo com pelo menos
uma reunião analisada (a transcrição fica guardada).

1. **Abrir o cliente.** Entre como o vendedor dono do cliente e abra `/clientes/{id}`. A seção "Buscar no histórico"
   aparece entre o mapa de temas e a tabela de reuniões; o botão Buscar fica desabilitado com a caixa vazia.
2. **Busca com resultado.** Digite uma palavra que existe numa transcrição (por exemplo `suporte`) e envie. Aparecem até
   10 trechos entre aspas, com data/hora da reunião, em ordem de relevância.
3. **Link para a reunião.** Clique em "Abrir na reunião": abre `/reunioes/{id}?turno=N` com aquele turno destacado.
4. **Sem resultado e privacidade.** Busque algo que não aparece em nenhuma conversa (`zzzz`): "Nada encontrado", sem
   aviso amarelo. Busque pelo nome do cliente ou de um contato: acha o trecho, e nos logs do Python (`evidencias:
   consulta=… trechos=…`) aparecem só tamanhos, nunca texto.
5. **Falha do Python.** Pare o `uvicorn` e busque de novo: a tela mostra o aviso amarelo "A busca está indisponível no
   momento…", sem erro e sem tela quebrada (o Java responde 200 com lista vazia). Suba o Python de novo e repita a busca:
   volta a funcionar. Bônus: entre como outro vendedor e abra a URL do mesmo cliente; deve dar "Cliente não encontrado".
