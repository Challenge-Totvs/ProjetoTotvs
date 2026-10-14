# Contrato do analise-service v3

- **Projeto:** InsightCall (FIAP × TOTVS Challenge 2026)
- **Frente:** analise-service (Python/FastAPI) ↔ backend Java
- **Consumidores:** Claude Code (implementação do Python), Kelwin (backend Java), chats de IA/ML e de interface
- **Gerado em:** 2026-10-11 · **Estado:** rascunho realinhado, para validar com o código antes de implementar
- **Fontes:** `docs/SDD.md` v3.0 §3, §5 e §6 (contrato v3) · record Java `ContratoV3` e `GravadorAnalise` (commit `fc206c2`) · `docs/DIVISAO_TRABALHO.md` · hand-offs de motores (09/10) e de backend (08/10) · decisões do João Paulo em 10 e 11/10
- **Substitui:** a versão anterior deste arquivo, que partia do contrato v1 (7 campos). O Java em `main` já não lê esse corpo **[verificado]**
- **Validade:** vale até a primeira mudança de campo. Toda mudança passa por este arquivo e pelas fixtures **antes** do código, e é combinada com o Kelwin
- **Marcas:** **[decidido]** aprovado pelo João Paulo · **[proposta]** padrão deste documento, vale até alguém contestar · **[verificado]** conferido no código ou no SDD · **[não verificado]** falta conferir · **[aberto]** sem decisão
- **Como ler:** quem implementa o Python lê as seções 3 a 8. Quem integra no Java lê a 9. Os exemplos completos estão no Apêndice A e em `docs/contrato/*.json`

> **Nome:** o SDD chama este contrato de "contrato v3" e o hand-off de motores (09/10) de "contrato da análise v2". É o mesmo contrato. Vale o nome **v3**. Os extras do hand-off (`confianca`, `eventosConduta`) entram como campos opcionais que o Java hoje ignora.

---

## 1. Objetivo e princípios

O `POST /analisar` recebe os **turnos já numerados e pseudonimizados** pelo Java e devolve temas com padrão, citações literais conferidas, papéis, resumo, compromissos e curva de sentimento.

1. **O Java é a referência do formato.** O record `ContratoV3` (pedido e resposta) é o que o consumidor lê hoje. O Python se alinha a ele, não o contrário **[verificado]**.
2. **Campo novo é opcional para quem lê.** Os records de resposta têm `@JsonIgnoreProperties(ignoreUnknown = true)` **[verificado]**, então `confianca`, `eventosConduta`, `versaoContrato` e `avisos` podem existir sem quebrar o Java.
3. **Cada serviço faz uma coisa.** Java: numera turnos, pseudonimiza, traduz de volta, grava, calcula a situação dos temas. Python: lê os turnos, analisa, **confere cada citação** e devolve (SDD §3.3) **[decidido]**.
4. **A LLM extrai, o código decide.** A LLM devolve trechos, padrões e estimativas. O código confere os trechos, escreve `motor` e `tentativas`, e monta `descartados`. Nenhum campo de controle vem da LLM.
5. **Citação é recorte literal** **[decidido, D2]**. Trecho que não existe no texto recebido é descartado e registrado, nunca devolvido como evidência.
6. **Ausente é diferente de vazio e de zero.** Campo ausente: o motor não tem essa capacidade. Lista vazia: o motor procurou e não achou. `confianca` ausente: o motor não calcula. Nunca `0` para dizer "não sei".
7. **Fonte única.** Este arquivo define o contrato do lado Python. O SDD §6.2 deve apontar para cá quando o Kelwin aprovar.

**Fora desta versão:** reconhecimento automático de entidades na pseudonimização (E8), RAG, treino do modelo local, `confianca` por concordância entre LLMs (D4), avaliação de regras de conduta (código determinístico do backend), contagem real de tokens, glossário por cliente.

---

## 2. Fluxo

```text
Java: ler turnos ─► pseudonimizar ─► POST /analisar ─────────────────────────────┐
                                                                                 ▼
              validar pedido ─► PIPELINE_VERSAO=mock? ─sim─► devolve resposta gravada
                                       │ não
                                       ▼
   llm1 ─(falhou)─► llm2 ─(falhou)─► local (classificador + regras por padrão) ─(falhou)─► regras ─(falhou)─► 503
     │                │                      │                                      │
     └──── saída da LLM (SaidaLLM) ──────────┴──────── saída determinística ────────┘
                                       ▼
             conferir citações (7.2) ─► montar resposta (código) ─► 200
```

Orçamento de tempo **[decidido, D7; calibrar no smoke]**: `llm1` ~55 s, `llm2` ~35 s, reserva ~10 s para `local` e `regras`, total ≤ 100 s. O Java desiste em 120 s (`ANALISE_SERVICE_TIMEOUT_MS`) **[verificado]**.

---

## 3. Pedido: `POST /analisar`

`Content-Type: application/json`. Campos desconhecidos são ignorados. O pedido **v1** (`conteudo` + `formatoOrigem`) deixa de ser aceito: o Java não o envia mais **[decidido, 11/10]**.

### 3.1 Campos

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `turnos` | `[{n:int, locutor:int, texto:string}]` | **sim** | De 1 a 3.000 itens. `n` consecutivo de 1 a N; `locutor` inteiro (não é sequencial e não é uma pessoa); `texto` não vazio, até 5.000 caracteres. Já vem **pseudonimizado** (`[PESSOA_1]`, `[EMPRESA_1]`, `[LOCAL_1]`). Vazio ou ausente → 422 `pedido_invalido` |
| `dataReuniao` | string `AAAA-MM-DD` | não | Só referência para a LLM entender prazos ditos ("até segunda") |
| `padroes` | `[string]` | não | Subconjunto dos 14 padrões (6.1). Ausente ou vazio = os 14. O Java envia os ativos. Chave fora da lista → 422 `padrao_desconhecido` |
| `contraexemplos` | `[{padrao, texto, motivo}]` | não | "Não procede" anteriores. `motivo` ∈ `nao_cliente`, `fora_contexto`, `tema_errado`, `outro`. O Java envia os temas marcados "não procede" (ainda vigentes) do **mesmo cliente**, do mais recente ao mais antigo, até 50: `padrao` = chave do tema, `texto` = citação do tema já pseudonimizada e cortada em 500 caracteres, `motivo` vazio vira `outro`. Cliente sem "não procede" → `[]` (tarefa E6, 14/10) |
| `contextoCliente` | `[{tipo, texto, origem, data}]` | não, **extra** | Ajuste manual por cliente. `tipo` = `ajuste_manual`; `origem` ∈ `vendedor`, `gestor`; `data` = `AAAA-MM-DD`. O Java ainda não envia |
| `glossarioTime` | `[{termo, significa, escopo}]` | não, **extra** | Siglas e nomes internos. `escopo` = `time`. O Java ainda não envia |
| `correcoesAnteriores` | `[{padrao, textoOriginal, correcao, motivo}]` | não, **extra** | Correções do vendedor. `correcao` = `nao_procede` (único valor na Release 1, **[decidido, A7]**). O Java ainda não envia |

### 3.2 Limites (protegem custo e `max_tokens`) **[decidido 11/10, refinar depois]**

| Item | Limite | Estouro |
|---|---|---|
| `turnos` | até 3.000 itens; `texto` até 5.000 caracteres | 422 `pedido_invalido` |
| `contraexemplos`, `correcoesAnteriores`, `contextoCliente`, `glossarioTime` | até 50 itens cada; campos de texto até 500 caracteres | 422 `pedido_invalido` |

O Java já recusa transcrição fora de 80 a 200.000 caracteres (SDD §5.3) e sem `[LOCUTOR n]` (422 `sem_locutor`, SDD §5.2). O Python não precisa tratar esses dois casos.

### 3.3 Como os campos opcionais entram na análise

- Entram no prompt **como dados delimitados**, nunca como instrução. O serviço neutraliza qualquer marcação que imite o delimitador (inclusive `</transcricao>`) nos turnos e nos campos opcionais **[verificado: hoje não há escape]**.
- `contraexemplos` e `correcoesAnteriores` descrevem o mesmo mecanismo ("isto não é uma ocorrência deste padrão"). O serviço junta os dois e remove duplicatas por `(padrao, texto)`.
- O serviço **não** pseudonimiza nada: confia no que o Java enviou.

---

## 4. Resposta: `200 OK`

Os nomes e tipos da tabela 4.1 são exatamente os do record Java `ContratoV3.Resposta` **[verificado]**.

### 4.1 Campos lidos pelo Java

| Campo | Tipo | Quem preenche | Regra |
|---|---|---|---|
| `motor` | `llm1` \| `llm2` \| `local` \| `regras` | **Código** | Quem respondeu. Minúsculas exatas: qualquer outro valor derruba a análise no Java (`MotorUtilizado.de`) **[verificado]** |
| `tentativas` | `[{motor, ok, erro?, duracaoMs?}]` | **Código** | Uma entrada por motor tentado, na ordem. `erro` é um código (6.5), **nunca** mensagem livre nem texto da transcrição |
| `score` | int 0 a 100 | LLM / `local` / `regras` | Sempre inteiro |
| `sentimento` | `positivo` \| `neutro` \| `negativo` | LLM / `local` / `regras` | Minúsculas exatas; outro valor derruba a análise no Java (`SentimentoGeral.de`). Sempre enviar |
| `papeis` | `{"<locutor>": "vendedor"\|"cliente"}` | LLM (como lista) → código monta o dicionário | Chave = número do locutor em texto. Locutor sem papel claro **não aparece** no mapa. Ausente em `local`/`regras` |
| `resumo` | string ≤ 1.500 | LLM | Ausente em `local`/`regras` |
| `interesse` | `[{texto, turno, citacao}]` | LLM; `local`/`regras` por classificador e palavras-chave | `texto` descreve o sinal; `citacao` é literal e conferida; `turno` int ≥ 1 |
| `proximosPassos` | `[string]` ≤ 5 itens, ≤ 200 caracteres | LLM | Substitui `recomendacaoProximosPassos` (v1), que agora é lista |
| `temas` | `[Tema]` | LLM; `local`/`regras` por expressões por padrão | Seção 4.2 |
| `compromissos` | `[{turno, texto, regra}]` | LLM | Só promessas do **vendedor**. `texto` literal e conferido; `regra` na lista 6.4. O Java calcula a data. Ausente em `local`/`regras` |
| `sentimentoSerie` | `[[turno, valor]]` | LLM (como lista de objetos) → código converte | `valor` de −1 a 1; `turno` existente; ordem crescente; até 60 pontos. Ausente em `local`/`regras` |
| `descartados` | `[{texto, motivo, origem?, padrao?}]` | **Código** | Tudo que a LLM devolveu e não passou nas regras (7.2). Sempre presente, pode ser `[]` |

### 4.2 `Tema`

| Campo | Tipo | Regra |
|---|---|---|
| `padrao` | string | Chave dos 14 padrões e presente em `padroes` do pedido. Fora disso o tema é descartado (`padrao_fora_da_lista`). O Java também descarta, por segurança |
| `titulo` | string ≤ 120 | Título curto em português |
| `tipos` | `["risco"\|"oportunidade"]` | De 1 a 2 valores, sem repetição, minúsculas exatas (o Java compara por `contains`). Padrão = tipo do padrão (6.1). Os dois valores quando o mesmo trecho recebe os dois rótulos |
| `turno` | int ≥ 1 | Turno onde o `texto` começa, **depois da conferência** (pode ser corrigido pelo serviço) |
| `turnoFim` | int ≥ `turno` | Último turno do trecho. **Sempre presente**, igual a `turno` quando o trecho cabe em um turno (segue o exemplo do SDD) |
| `tratado` | `true` \| `false` \| `null` | Regra 7.3 |
| `texto` | string 10 a 600 | Recorte literal do texto recebido (7.2) |
| `confianca` | número 0 a 1 | **Extra.** Estimativa da própria LLM (D4). Ausente em `local`/`regras`. Não é probabilidade calibrada |

### 4.3 Campos extras (o Java ignora hoje)

| Campo | Tipo | Regra |
|---|---|---|
| `eventosConduta` | `[{tipo, turno, texto, confianca}]` | LLM extrai de uma lista fechada (6.2); **não julga** se é violação (código do backend). Ausente em `local`/`regras` |
| `versaoContrato` | `"v3"` | Código. Constante |
| `avisos` | `[string]` | Código. Códigos curtos (6.6). Pode ser `[]` |

---

## 5. Matriz campo × motor (Release 1)

| Campo | `llm1` / `llm2` | `local` | `regras` |
|---|---|---|---|
| `motor`, `tentativas`, `descartados`, `versaoContrato`, `avisos` | sim (código) | sim (código) | sim (código) |
| `score` | LLM (rubrica 0–20, 21–50, 51–80, 81–100) | classificador: (1 − proporção de risco) × 100 | proporção de sinais positivos; 50 sem sinais |
| `sentimento` | LLM | pelo `score`: ≥ 70 positivo, ≥ 45 neutro, senão negativo | pelo `score`, mesma regra **[proposta]** |
| `interesse` | LLM | classificador | palavras-chave |
| `temas` | LLM | **expressões por padrão** (as mesmas das `regras`) **[decidido 11/10]** | expressões por padrão |
| `tratado` | `true`/`false`, ou `null` sem papel claro | sempre `null` | sempre `null` |
| `confianca`, `eventosConduta` | sim | ausentes | ausentes |
| `papeis`, `resumo`, `proximosPassos`, `compromissos`, `sentimentoSerie` | sim | ausentes | ausentes |

Decisão de 11/10: **as regras por padrão voltam à cadeia na Release 1**, como pedem o SDD §6.1/§6.3 e a tarefa P4. O classificador local continua com categorias próprias (risco ou neutro por trecho); mapeá-lo aos 14 padrões fica para a Release 2 (A3).

O modelo local e as regras **nunca falham em silêncio**: sem trechos analisáveis levantam erro explícito, que vira `erro: "entrada_sem_trechos"` em `tentativas`. Ambos leem os turnos recebidos; nenhum depende de `[MM:SS]`.

---

## 6. Listas fechadas

### 6.1 Os 14 padrões **[decidido, hand-off de backend, apêndice A]**

| Chave | Nome | Tipo padrão |
|---|---|---|
| `suporte_insatisfacao` | Insatisfação com o suporte | risco |
| `preco_objecao` | Objeção de preço | risco |
| `prazo_implantacao` | Prazo de implantação | risco |
| `concorrente_citado` | Concorrente citado | risco |
| `cancelamento_citado` | Cancelamento citado | risco |
| `adocao_resistencia` | Resistência da equipe | risco |
| `fiscal_problema` | Problema no fechamento fiscal | risco |
| `orcamento_restrito` | Orçamento restrito | risco |
| `expansao_unidade` | Expansão para nova unidade | oportunidade |
| `modulo_adicional` | Módulo adicional | oportunidade |
| `integracao` | Integração com outro sistema | oportunidade |
| `renovacao` | Renovação do contrato | oportunidade |
| `upgrade_licencas` | Ampliação de licenças | oportunidade |
| `treinamento` | Treinamento da equipe | oportunidade |

### 6.2 Eventos de conduta **[proposta, ilustrativa; A2 define a lista definitiva]**

`pagamento_confirmado_antes_de_dados` · `desconto_fora_da_politica` · `prazo_prometido_sem_confirmar_capacidade`. Tipo fora da lista → o evento é descartado (`evento_fora_da_lista`).

### 6.3 Papéis e valores de enum

`papeis`: `vendedor` · `cliente`. `motor`: `llm1` · `llm2` · `local` · `regras`. `sentimento`: `positivo` · `neutro` · `negativo`. `tipos`: `risco` · `oportunidade`. Tudo em minúsculas.

### 6.4 Regras de prazo dos compromissos

`sexta` · `segunda` · `sexta_semana_que_vem` · `mesmo_dia` · `mais2` · `null` (sem prazo dito). O serviço devolve só a chave; o Java calcula a data a partir da data da reunião (hand-off de backend §8.10, tarefa E1). Promessa com prazo que não cabe em nenhuma regra ("dia 15", "fim do mês") sai com `regra: null`.

### 6.5 Códigos de `tentativas[].erro`

`nao_configurado` (sem chave) · `timeout` · `limite_requisicoes` · `autenticacao` · `truncado` (saída cortada por `max_tokens`) · `sem_resposta_estruturada` · `schema_invalido` · `recusa` · `erro_provedor` · `modelo_indisponivel` · `entrada_sem_trechos` · `erro_interno`.

### 6.6 Códigos de `avisos`

`contingencia_modelo_local` · `contingencia_regras` · `saida_parcial` (parte da saída da LLM foi descartada ou cortada pelos limites 7.6).

### 6.7 Motivos de `descartados`

`evidencia_nao_localizada` (nome do SDD §5.7) · `padrao_fora_da_lista` · `evento_fora_da_lista` · `trecho_curto` · `trecho_longo`. `origem` ∈ `tema` · `interesse` · `compromisso` · `eventoConduta`.

---

## 7. Regras

### 7.1 Turnos

A numeração é feita **só no Java** (SDD §5.2). O Python consome `turnos` como chegam e não relê texto bruto **[decidido, SDD §3.3]**. Fatos do corpus **[medido]** que o prompt e a conferência precisam respeitar: o número do locutor não é sequencial (mediana de 18 por reunião, máximo 179); os turnos são curtos (mediana de 4 palavras) e quebram frases.

### 7.2 Conferência de citações **[decidido, D2 e SDD §5.7; detalhes decididos em 11/10, refinar depois]**

Vale para `temas[].texto`, `interesse[].citacao`, `compromissos[].texto` e `eventosConduta[].texto`, sempre sobre o texto **pseudonimizado** recebido.

1. **Normalizar os dois lados** antes de comparar: Unicode NFC; aspas tipográficas (`“ ” ‘ ’`) viram `"` e `'`; `–` e `—` viram `-`; `…` vira `...`; qualquer sequência de espaços e quebras vira um espaço; tirar as pontas; **ignorar maiúsculas** (SDD §5.7). Não mudar acentos.
2. **Buscar nesta ordem**, parando no primeiro acerto: (a) o turno indicado; (b) janelas de 2 e 3 turnos consecutivos (concatenados com um espaço) que contêm o turno indicado; (c) os turnos de `n−2` a `n+2`, do mais próximo para o mais distante, com as mesmas janelas.
3. **Acerto:** gravar `turno` = turno onde o trecho começa (corrigindo o devolvido pela LLM, se preciso) e `turnoFim` = último turno do trecho. O `texto` gravado é o do **texto recebido**, não o normalizado.
4. **Sem acerto:** o item sai da resposta e entra em `descartados` com `motivo: "evidencia_nao_localizada"`.
5. **Tamanho:** texto normalizado com menos de 10 caracteres → `trecho_curto`; com mais de 600 → `trecho_longo`. Ambos descartados.

Por que a tolerância: os turnos do corpus têm mediana de 4 palavras, então uma frase inteira cruza turnos e a conferência estrita descartaria citação correta.

`local` e `regras` produzem o `texto` a partir do próprio turno, então passam pela mesma função, que apenas confirma.

### 7.3 `tratado`

- `true`: o tema foi respondido na própria reunião, por alguém do papel oposto ao de quem o levantou, em turno posterior.
- `false`: ficou sem resposta na reunião.
- `null`: o motor não sabe quem falou (locutor sem papel claro, `local`, `regras`). **Nunca** `false` por falta de informação: `false` afirma que ninguém respondeu, e o Java calcula "sem retorno" a partir disso.

### 7.4 `confianca` **[decidido, D4]**

Vem da própria LLM, por tema e por evento de conduta, de 0 a 1; valores fora do intervalo são limitados a ele. Não é calibrada. `local` e `regras` não a enviam (campo ausente). Consumidores não devem esconder temas por causa dela nesta versão.

### 7.5 Papéis e compromissos

- `papeis` é inferido pela LLM e sempre exibido como inferido. Locutor sem papel claro fica fora do mapa.
- `compromissos` só inclui promessas do vendedor. Sem vendedor identificado, a lista é `[]`.

### 7.6 Limites de saída **[decidido 11/10, refinar depois]**

Até 40 `temas`, 20 `compromissos`, 20 `eventosConduta`, 60 pontos em `sentimentoSerie`, 20 `interesse`. O excedente é cortado em ordem de `confianca` decrescente e o serviço acrescenta `avisos: ["saida_parcial"]`. Existem para a saída caber em `max_tokens` (hoje 4.000, insuficiente **[verificado]**). O Java consolida vários temas do mesmo padrão em um só (`ConsolidadorTemas`), então o Python não precisa deduplicar por padrão.

### 7.6.1 Um tema por padrão por reunião **[decidido 12/10]**

Um tema por padrão por reunião: se o mesmo padrão aparecer duas vezes, escolher a primeira ocorrência sem resposta. Vale como instrução ao motor (prompt da LLM e regras); o serviço não deduplica depois, e o `ConsolidadorTemas` do Java segue como rede de segurança (7.6).

### 7.7 Segurança e privacidade **[decidido, D3 revisada, e D9]**

- O Java pseudonimiza com os nomes do cadastro (cliente, contatos, vendedor) **antes** de chamar o Python, e o Python nunca vê esses nomes (SDD §5.6) **[verificado]**. A pendência de LGPD que sobra: nomes que **não** estão no cadastro, até o reconhecimento automático de entidades (E8). O texto segue cru para Anthropic e OpenAI com essa ressalva; não prometer conformidade completa no pitch.
- Logs e `tentativas` **nunca** contêm texto de transcrição, de contexto ou de glossário. Só motor, código de erro e duração.
- Nenhum trecho do corpus da TOTVS entra no repositório; as fixtures são sintéticas.

---

## 8. Erros, versão e `/health`

### 8.1 Códigos HTTP

| HTTP | `codigo` | Quando | Observação |
|---|---|---|---|
| 200 | — | Algum motor respondeu | Inclui contingência |
| 422 | `pedido_invalido`, `padrao_desconhecido` | Pedido inválido (sem turnos, limites, padrão fora da lista) | Substitui o `{"detail": [...]}` padrão do FastAPI |
| 503 | `analise_indisponivel` | Nenhum motor respondeu dentro do prazo | Traz `tentativas`. O SDD §6.2 diz 500; o Java trata os dois igual, então a diferença é só de clareza **[proposta: atualizar o SDD]** |
| 500 | `erro_interno` | Defeito inesperado | Corpo JSON sem stack trace e sem texto da transcrição |

Corpo de erro: `{ "codigo": string, "mensagem": string, "detalhes"?: [...], "tentativas"?: [...] }`. O Java trata qualquer `RestClientException` como `AnaliseIndisponivelException` **[verificado]**.

### 8.2 `PIPELINE_VERSAO`

`PIPELINE_VERSAO=real|mock` (padrão `real`) **[decidido 11/10]**. Com `mock`, o serviço valida o pedido e devolve **sempre** a resposta gravada `resposta-v3-llm.json` (o corte de emergência do `DIVISAO_TRABALHO.md`, e a tarefa P0). A resposta carrega o cabeçalho `X-Insightcall-Pipeline: real|mock`. É o rollback da Release 1: o Java e a interface continuam funcionando sem nenhuma LLM.

### 8.3 `GET /health`

Formato que o Java já lê (`MotorStatusService`: lista `motores` com `motor` e `ok`; motor ausente conta como fora do ar) **[verificado]**, mais campos extras:

```json
{
  "status": "ok",
  "pipelineVersao": "real",
  "motores": [
    {
      "motor": "llm1",
      "ok": true
    },
    {
      "motor": "llm2",
      "ok": true
    },
    {
      "motor": "local",
      "ok": true
    },
    {
      "motor": "regras",
      "ok": true
    }
  ]
}
```

`ok` de cada motor = **configurado** E a **última tentativa real** desse motor **não falhou nos últimos 5 minutos** (estado em memória, por processo; um reinício zera). "Configurado": `llm1`/`llm2` têm chave e modelo definidos; `local` tem o artefato carregável; `regras` está sempre disponível. Uma tentativa bem-sucedida depois da falha recupera o `ok` na hora. Não contam como tentativa real as que não chamaram o motor (`nao_configurado`, sem prazo restante). O `/health` **nunca chama a API de uma LLM** (não gasta token): só lê configuração e o estado em memória. `regras` deixou de ser "sempre `true`": nasce `true` e cai para `false` por 5 minutos se falhar de verdade. `status`: `ok` (alguma LLM ok), `degradado` (só `local`/`regras`), `indisponivel` (nenhum motor ok). O app sobe mesmo sem chaves e sem o `.joblib` (AC7).

---

## 9. Compatibilidade com o Java **[verificado no commit `fc206c2`]**

| Ponto | Situação |
|---|---|
| Pedido | `AnaliseService` monta `Pedido(turnos, dataReuniao, padroes, contraexemplos)`; `contraexemplos` traz os "não procede" do mesmo cliente (§3.1), ou `[]` se não houver |
| Resposta | `ContratoV3.Resposta` e os records aninhados têm `@JsonIgnoreProperties(ignoreUnknown = true)`: campos extras são seguros. **A4 está fechada** |
| Campos que o Java exige | `motor` ∈ {llm1, llm2, local, regras} e `sentimento` ∈ {positivo, neutro, negativo} (ou nulo), senão a análise falha com 503. `tipos` com `risco`/`oportunidade` em minúsculas. `turno` inteiro em temas, interesse e compromissos |
| Tolera ausência | Listas e mapas ausentes viram vazios no construtor do record |
| Tradução de volta | `TradutorResposta` restaura nomes em `resumo`, `interesse`, `proximosPassos`, `temas.titulo/texto`, `compromissos.texto`, `descartados.texto`. Por isso o Python devolve texto **pseudonimizado**, idêntico ao recebido |
| `/health` | `MotorStatusService` lê `motores[].motor` e `motores[].ok` |
| Prazo | Java 120 s > serviço ≤ 100 s. Se o Java reduzir o timeout, o orçamento do serviço reduz junto (D7) |
| Falha no Java | Qualquer 4xx/5xx do Python vira "serviço de análise indisponível" para o usuário |

O que falta do lado Java: um teste que leia `docs/contrato/resposta-v3-*.json` em `ContratoV3.Resposta` e confirme que os valores de enum são aceitos (AC9).

---

## 10. Critérios de aceite da Release 1

| # | Critério | Como provar |
|---|---|---|
| AC1 | `POST /analisar` aceita `pedido-v3.json` e `pedido-v3-extras.json` (200) e recusa pedido sem `turnos` (422) | Teste de API |
| AC2 | A resposta valida contra `ContratoV3.Resposta`: nomes, tipos e enums exatos | Fixtures lidas no Python e no Java |
| AC3 | As LLMs preenchem `temas` (padrão da lista), `papeis`, `resumo`, `proximosPassos`, `compromissos`, `sentimentoSerie`, `interesse`, `confianca`, `eventosConduta`, `descartados`, `tentativas` | `resposta-v3-llm.json` + teste de schema |
| AC4 | Toda citação existe no texto recebido (normalizado, sem diferenciar maiúsculas, com vizinhos ±2 e `turnoFim`); senão vai para `descartados` | Testes de `conferir_citacoes`: acerto, espaços/aspas, turno vizinho, entre dois turnos, inexistente |
| AC5 | Nenhuma requisição passa de ~100 s; `llm1` falha → `llm2`; duas fora → `local`; tudo fora → 503 estruturado | Testes de orquestrador com clients simulados lentos e com falha |
| AC6 | `local` e `regras` leem `turnos`, devolvem temas por expressão de padrão no formato v3 (`tratado` nulo, sem `confianca`) e não falham em silêncio | `resposta-v3-local.json`, `resposta-v3-regras.json` + uma transcrição de exemplo por padrão |
| AC7 | O app sobe sem `.joblib` e sem chaves; `/health` no formato da seção 8.3 | Teste de import e de `/health` |
| AC8 | `PIPELINE_VERSAO=mock` devolve a resposta gravada | Teste com a flag |
| AC9 | As fixtures validam no Python e no Java | Um teste em cada lado lendo os mesmos JSON |
| AC10 | `pytest` verde sem rede e sem chaves; smoke real com as duas chaves registrado | Saída do `pytest` + `docs/evidencias/smoke-12-10.md` |

---

## 11. Fixtures (`docs/contrato/`)

| Arquivo | Conteúdo | Quem lê |
|---|---|---|
| `pedido-v3.json` | O que o Java envia para um cliente sem "não procede": `turnos`, `dataReuniao`, `padroes` (os 14), `contraexemplos: []` | Python e Java |
| `pedido-v3-extras.json` | Acrescenta `contraexemplos` preenchido, `contextoCliente`, `glossarioTime`, `correcoesAnteriores` e um subconjunto de `padroes` | Python |
| `resposta-v3-llm.json` | Resposta completa de LLM: três temas, interesse, compromisso, evento de conduta e um descartado. **É também a resposta do mock** | Python e Java |
| `resposta-v3-local.json` | Contingência do `local`, com temas por expressão | Python e Java |
| `resposta-v3-regras.json` | Contingência das `regras` | Python e Java |
| `erro-422.json`, `erro-503.json`, `health.json` | Corpos de erro e de saúde | Python |

Foram conferidas por script: cada `texto` e `citacao` existe literalmente no turno indicado, e os valores de enum são das listas fechadas.

---

## 12. Pendências

| # | Pendência | Estado | Dono |
|---|---|---|---|
| A1 | Quem numera turnos | **Fechada:** só o Java (SDD §3.3, §5.2) | — |
| A2 | Lista definitiva de eventos de conduta e quem a mantém | Aberta; vale a lista ilustrativa (6.2) | João Paulo |
| A3 | Mapear o classificador local aos 14 padrões | Release 2. Na Release 1, `temas` do `local` vêm das expressões por padrão | João Paulo |
| A4 | O Jackson do Java ignora campos desconhecidos? | **Fechada:** sim, por anotação nos records **[verificado]**. Falta só o teste do AC9 | Kelwin |
| A5 | Unidade de texto em que o classificador foi treinado | Por ora o `local` divide por turno **[decidido 11/10]**; conferir no notebook de DS na Release 2 | João Paulo |
| A6 | Transcrição sem `[LOCUTOR n]` | **Fechada:** o Java recusa com 422 `sem_locutor` (SDD §5.2) | — |
| A7 | Outros valores de `correcoesAnteriores.correcao` | **Fechada** para a Release 1: só `nao_procede` | Release 2 |
| A8 | As 14 expressões por padrão (conteúdo, dono, teste) | Aberta; nova tarefa do João Paulo (P4) | João Paulo |
| A9 | Status HTTP de falha total: 503 (este documento) ou 500 (SDD §6.2) | **Fechada [12/10]:** falha total responde 503; o Java trata qualquer erro HTTP como "análise indisponível" | — |
| A10 | O SDD §6.2 passa a apontar para este arquivo e incorpora `confianca` e `eventosConduta` como opcionais | Aberta | Kelwin + João Paulo |

---

## 13. Histórico de mudanças

| Data | Mudança |
|---|---|
| 2026-10-11 | Primeira versão como "contrato v2", baseada no corpo v1. **Substituída no mesmo dia.** |
| 2026-10-11 | Realinhada ao contrato v3 do SDD e ao `ContratoV3` do Java (commit `fc206c2`). Remove o pedido e o corpo v1. Regras por padrão voltam à cadeia na Release 1. Rollback passa a ser a resposta gravada (`PIPELINE_VERSAO=mock`). |
| 2026-10-14 | O Java passa a preencher `contraexemplos` com os "não procede" do mesmo cliente (§3.1, §9). Formato inalterado. |

Regra de mudança: campo novo opcional não muda a versão; remover ou mudar o significado de um campo que o Java lê exige conversa com o Kelwin antes.

---

## Apêndice A. Exemplos completos

### A.1 Pedido enviado hoje pelo Java: `pedido-v3.json`

```json
{
  "turnos": [
    {
      "n": 1,
      "locutor": 1,
      "texto": "Bom dia, [PESSOA_1]. Obrigado pelo horário, vamos falar da renovação."
    },
    {
      "n": 2,
      "locutor": 2,
      "texto": "Bom dia. Antes de tudo, preciso falar do suporte."
    },
    {
      "n": 3,
      "locutor": 2,
      "texto": "Abrimos um chamado sobre o fechamento do faturamento há três semanas e até hoje ninguém retornou."
    },
    {
      "n": 4,
      "locutor": 1,
      "texto": "Certo. Passando para a proposta de renovação então."
    },
    {
      "n": 5,
      "locutor": 3,
      "texto": "Na TI a migração dos cadastros terminou no mês passado, sem perda de histórico."
    },
    {
      "n": 6,
      "locutor": 1,
      "texto": "Ótimo. Posso fechar o reajuste fixo por dois anos e dar quinze por cento de desconto agora."
    },
    {
      "n": 7,
      "locutor": 2,
      "texto": "Isso ajuda bastante."
    },
    {
      "n": 8,
      "locutor": 2,
      "texto": "A diretoria quer oferecer telemedicina para os pacientes da ala nova."
    },
    {
      "n": 9,
      "locutor": 1,
      "texto": "Temos um módulo para isso, posso mostrar na próxima reunião."
    },
    {
      "n": 10,
      "locutor": 3,
      "texto": "Só que o orçamento deste ano está bem apertado."
    },
    {
      "n": 11,
      "locutor": 1,
      "texto": "Te envio a proposta de renovação até segunda, com os valores fechados para os dois anos."
    },
    {
      "n": 12,
      "locutor": 2,
      "texto": "Combinado. Obrigada."
    }
  ],
  "dataReuniao": "2026-10-07",
  "padroes": [
    "suporte_insatisfacao",
    "preco_objecao",
    "prazo_implantacao",
    "concorrente_citado",
    "cancelamento_citado",
    "adocao_resistencia",
    "fiscal_problema",
    "orcamento_restrito",
    "expansao_unidade",
    "modulo_adicional",
    "integracao",
    "renovacao",
    "upgrade_licencas",
    "treinamento"
  ],
  "contraexemplos": []
}
```

### A.2 Pedido com extras: `pedido-v3-extras.json`

```json
{
  "turnos": [
    {
      "n": 1,
      "locutor": 1,
      "texto": "Bom dia, [PESSOA_1]. Obrigado pelo horário, vamos falar da renovação."
    },
    {
      "n": 2,
      "locutor": 2,
      "texto": "Bom dia. Antes de tudo, preciso falar do suporte."
    },
    {
      "n": 3,
      "locutor": 2,
      "texto": "Abrimos um chamado sobre o fechamento do faturamento há três semanas e até hoje ninguém retornou."
    },
    {
      "n": 4,
      "locutor": 1,
      "texto": "Certo. Passando para a proposta de renovação então."
    },
    {
      "n": 5,
      "locutor": 3,
      "texto": "Na TI a migração dos cadastros terminou no mês passado, sem perda de histórico."
    },
    {
      "n": 6,
      "locutor": 1,
      "texto": "Ótimo. Posso fechar o reajuste fixo por dois anos e dar quinze por cento de desconto agora."
    },
    {
      "n": 7,
      "locutor": 2,
      "texto": "Isso ajuda bastante."
    },
    {
      "n": 8,
      "locutor": 2,
      "texto": "A diretoria quer oferecer telemedicina para os pacientes da ala nova."
    },
    {
      "n": 9,
      "locutor": 1,
      "texto": "Temos um módulo para isso, posso mostrar na próxima reunião."
    },
    {
      "n": 10,
      "locutor": 3,
      "texto": "Só que o orçamento deste ano está bem apertado."
    },
    {
      "n": 11,
      "locutor": 1,
      "texto": "Te envio a proposta de renovação até segunda, com os valores fechados para os dois anos."
    },
    {
      "n": 12,
      "locutor": 2,
      "texto": "Combinado. Obrigada."
    }
  ],
  "dataReuniao": "2026-10-07",
  "padroes": [
    "suporte_insatisfacao",
    "preco_objecao",
    "orcamento_restrito",
    "modulo_adicional",
    "renovacao",
    "cancelamento_citado"
  ],
  "contraexemplos": [
    {
      "padrao": "cancelamento_citado",
      "texto": "Vamos cancelar a reserva do salão de eventos.",
      "motivo": "fora_contexto"
    }
  ],
  "contextoCliente": [
    {
      "tipo": "ajuste_manual",
      "texto": "O cliente chama o módulo fiscal de SPED.",
      "origem": "vendedor",
      "data": "2026-09-20"
    }
  ],
  "glossarioTime": [
    {
      "termo": "SPED",
      "significa": "módulo fiscal",
      "escopo": "time"
    }
  ],
  "correcoesAnteriores": [
    {
      "padrao": "preco_objecao",
      "textoOriginal": "o valor ficou salgado",
      "correcao": "nao_procede",
      "motivo": "fora_contexto"
    }
  ]
}
```

### A.3 Resposta de LLM (e do mock): `resposta-v3-llm.json`

```json
{
  "motor": "llm1",
  "tentativas": [
    {
      "motor": "llm1",
      "ok": true,
      "duracaoMs": 18200
    }
  ],
  "score": 68,
  "sentimento": "neutro",
  "papeis": {
    "1": "vendedor",
    "2": "cliente",
    "3": "cliente"
  },
  "resumo": "Reunião de renovação. O cliente reclamou de um chamado de faturamento sem retorno, reagiu bem ao reajuste fixo, citou interesse em telemedicina e disse que o orçamento do ano está apertado. O vendedor se comprometeu a enviar a proposta até segunda.",
  "interesse": [
    {
      "texto": "Reagiu bem ao reajuste fixo com desconto",
      "turno": 7,
      "citacao": "Isso ajuda bastante."
    }
  ],
  "proximosPassos": [
    "Responder o chamado de faturamento aberto há três semanas",
    "Enviar a proposta de renovação com valores fechados para dois anos",
    "Agendar a demonstração do módulo de telemedicina"
  ],
  "temas": [
    {
      "padrao": "suporte_insatisfacao",
      "titulo": "Chamado de faturamento sem retorno",
      "tipos": [
        "risco"
      ],
      "turno": 3,
      "turnoFim": 3,
      "tratado": false,
      "texto": "Abrimos um chamado sobre o fechamento do faturamento há três semanas e até hoje ninguém retornou.",
      "confianca": 0.9
    },
    {
      "padrao": "modulo_adicional",
      "titulo": "Telemedicina para a ala nova",
      "tipos": [
        "oportunidade"
      ],
      "turno": 8,
      "turnoFim": 8,
      "tratado": true,
      "texto": "A diretoria quer oferecer telemedicina para os pacientes da ala nova.",
      "confianca": 0.82
    },
    {
      "padrao": "orcamento_restrito",
      "titulo": "Orçamento do ano apertado",
      "tipos": [
        "risco"
      ],
      "turno": 10,
      "turnoFim": 10,
      "tratado": false,
      "texto": "o orçamento deste ano está bem apertado",
      "confianca": 0.7
    }
  ],
  "compromissos": [
    {
      "turno": 11,
      "texto": "Te envio a proposta de renovação até segunda, com os valores fechados para os dois anos.",
      "regra": "segunda"
    }
  ],
  "sentimentoSerie": [
    [
      2,
      -0.2
    ],
    [
      3,
      -0.6
    ],
    [
      7,
      0.4
    ],
    [
      10,
      -0.3
    ],
    [
      12,
      0.3
    ]
  ],
  "descartados": [
    {
      "texto": "O cliente pediu cancelamento imediato do contrato.",
      "motivo": "evidencia_nao_localizada",
      "origem": "tema",
      "padrao": "cancelamento_citado"
    }
  ],
  "eventosConduta": [
    {
      "tipo": "desconto_fora_da_politica",
      "turno": 6,
      "texto": "dar quinze por cento de desconto agora",
      "confianca": 0.64
    }
  ],
  "versaoContrato": "v3",
  "avisos": []
}
```

### A.4 Resposta do modelo local: `resposta-v3-local.json`

Os valores de `score` e `sentimento` são ilustrativos: o classificador mede por trechos.

```json
{
  "motor": "local",
  "tentativas": [
    {
      "motor": "llm1",
      "ok": false,
      "erro": "timeout",
      "duracaoMs": 55000
    },
    {
      "motor": "llm2",
      "ok": false,
      "erro": "limite_requisicoes",
      "duracaoMs": 1300
    },
    {
      "motor": "local",
      "ok": true,
      "duracaoMs": 240
    }
  ],
  "score": 67,
  "sentimento": "neutro",
  "interesse": [
    {
      "texto": "Sinal de interesse identificado pelo classificador",
      "turno": 7,
      "citacao": "Isso ajuda bastante."
    }
  ],
  "temas": [
    {
      "padrao": "suporte_insatisfacao",
      "titulo": "Insatisfação com o suporte",
      "tipos": [
        "risco"
      ],
      "turno": 3,
      "turnoFim": 3,
      "tratado": null,
      "texto": "Abrimos um chamado sobre o fechamento do faturamento há três semanas e até hoje ninguém retornou."
    },
    {
      "padrao": "orcamento_restrito",
      "titulo": "Orçamento restrito",
      "tipos": [
        "risco"
      ],
      "turno": 10,
      "turnoFim": 10,
      "tratado": null,
      "texto": "Só que o orçamento deste ano está bem apertado."
    }
  ],
  "descartados": [],
  "versaoContrato": "v3",
  "avisos": [
    "contingencia_modelo_local"
  ]
}
```

### A.5 Resposta das regras: `resposta-v3-regras.json`

```json
{
  "motor": "regras",
  "tentativas": [
    {
      "motor": "llm1",
      "ok": false,
      "erro": "nao_configurado",
      "duracaoMs": 1
    },
    {
      "motor": "llm2",
      "ok": false,
      "erro": "nao_configurado",
      "duracaoMs": 1
    },
    {
      "motor": "local",
      "ok": false,
      "erro": "modelo_indisponivel",
      "duracaoMs": 3
    },
    {
      "motor": "regras",
      "ok": true,
      "duracaoMs": 12
    }
  ],
  "score": 33,
  "sentimento": "negativo",
  "interesse": [
    {
      "texto": "Palavra de interesse encontrada",
      "turno": 7,
      "citacao": "Isso ajuda bastante."
    }
  ],
  "temas": [
    {
      "padrao": "suporte_insatisfacao",
      "titulo": "Insatisfação com o suporte",
      "tipos": [
        "risco"
      ],
      "turno": 3,
      "turnoFim": 3,
      "tratado": null,
      "texto": "Abrimos um chamado sobre o fechamento do faturamento há três semanas e até hoje ninguém retornou."
    },
    {
      "padrao": "orcamento_restrito",
      "titulo": "Orçamento restrito",
      "tipos": [
        "risco"
      ],
      "turno": 10,
      "turnoFim": 10,
      "tratado": null,
      "texto": "Só que o orçamento deste ano está bem apertado."
    }
  ],
  "descartados": [],
  "versaoContrato": "v3",
  "avisos": [
    "contingencia_regras"
  ]
}
```

### A.6 Erros

`erro-503.json`:

```json
{
  "codigo": "analise_indisponivel",
  "mensagem": "Nenhum motor de análise respondeu dentro do prazo.",
  "tentativas": [
    {
      "motor": "llm1",
      "ok": false,
      "erro": "timeout",
      "duracaoMs": 55000
    },
    {
      "motor": "llm2",
      "ok": false,
      "erro": "autenticacao",
      "duracaoMs": 420
    },
    {
      "motor": "local",
      "ok": false,
      "erro": "modelo_indisponivel",
      "duracaoMs": 3
    },
    {
      "motor": "regras",
      "ok": false,
      "erro": "erro_interno",
      "duracaoMs": 2
    }
  ]
}
```

`erro-422.json`:

```json
{
  "codigo": "pedido_invalido",
  "mensagem": "O pedido não tem turnos.",
  "detalhes": [
    {
      "campo": "turnos",
      "problema": "vazio"
    }
  ]
}
```

---

## Apêndice B. De-para: contrato v1 (retirado) → v3

Quem ler hand-offs ou código antigo encontra os nomes da esquerda. **Valem os da direita.**

| v1 (retirado) | v3 |
|---|---|
| `conteudo` + `formatoOrigem` | `turnos` (numerados e pseudonimizados pelo Java) |
| `scoreEngajamento` | `score` |
| `sentimentoGeral`: `POSITIVO`/`NEUTRO`/`NEGATIVO` | `sentimento`: `positivo`/`neutro`/`negativo` |
| `motorUtilizado`: `LLM_PRIMARIA`/`LLM_SECUNDARIA`/`MODELO_LOCAL`/`REGEX_FALLBACK` | `motor`: `llm1`/`llm2`/`local`/`regras` |
| `pontosInteresse[]` `{descricao, trecho}` | `interesse[]` `{texto, turno, citacao}` |
| `pontosDesinteresse[]`, `oportunidadesVenda[]` | `temas[]` com `tipos` `risco` / `oportunidade` |
| `recomendacaoProximosPassos` (string) | `proximosPassos` (lista) |
| `GET /health` → `{"status":"ok"}` | `{"status", "pipelineVersao", "motores":[{motor, ok}]}` |
