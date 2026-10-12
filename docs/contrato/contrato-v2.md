# Contrato do analise-service v2

> **SUPERADO em 11/10 (tarde).** O Java do repositório (commit `fc206c2`) já usa o contrato v3 do `docs/SDD.md` §6.2 (`turnos`, `motor`, `score`, `sentimento`, `interesse`, `proximosPassos`), e não o contrato v1. A premissa "superconjunto da v1" e os nomes `scoreEngajamento`/`motorUtilizado` deste arquivo não valem mais. Não implemente a partir daqui; aguarde a versão realinhada.


- **Projeto:** InsightCall (FIAP × TOTVS Challenge 2026)
- **Frente:** analise-service (Python/FastAPI) ↔ backend Java
- **Consumidores:** Claude Code (implementação), Kelwin (backend Java), chats de IA/ML e de interface
- **Gerado em:** 2026-10-11 · **Estado:** aprovado para a Release 1 em 11/10 (João Paulo). Itens marcados "refinar depois" valem agora e serão revistos após a conclusão. Substitui a proposta da seção 5 do guia de workflow
- **Fontes:** `analise-service/app/schemas.py` e record Java `ResultadoAnalise` (commit `3c15f80`), hand-off de motores v4 (09/10), hand-off de backend (08/10), decisões D1 a D9 de 10/10 e confirmação do João Paulo em 11/10
- **Validade:** vale até a primeira mudança de campo. Toda mudança passa por este arquivo e pelas fixtures **antes** do código
- **Marcas:** **[decidido]** aprovado pelo João Paulo · **[proposta]** sugestão deste documento, vale como padrão até alguém contestar (não foi revisada item a item) · **[verificado]** conferido no código · **[não verificado]** plausível, falta conferir · **[aberto]** sem decisão
- **Como ler:** quem implementa lê as seções 3 a 8. Quem integra no Java lê a 9 e o Apêndice B. Os exemplos completos estão no Apêndice A e em `docs/contrato/*.json`

---

## 1. Objetivo e princípios

O `POST /analisar` ganha uma resposta mais rica (temas com padrão, papéis, resumo, compromissos, curva de sentimento, eventos de conduta, confiança) sem quebrar quem já consome a v1.

1. **A v2 é superconjunto da v1** **[decidido, D6]**. Os 7 campos atuais continuam presentes, com o mesmo nome, tipo e significado. Campo novo é opcional para quem lê. Nenhum valor novo entra nos enums que o Java já conhece (`SentimentoGeral`, `MotorUtilizado`): o Jackson, por padrão, falha em constante de enum desconhecida.
2. **A v1 continua disponível.** Com `PIPELINE_VERSAO=v1` o serviço devolve exatamente o corpo v1 (rollback N1) **[decidido, D1]**.
3. **A LLM extrai, o código decide.** A LLM devolve trechos, padrões e estimativas. O código confere cada trecho no texto, monta as listas da v1, escreve `motorUtilizado`, `tentativas` e `descartados`. Nenhum campo de controle vem da LLM.
4. **Citação é recorte literal** **[decidido, D2]**. Trecho que não existe no texto recebido é descartado e registrado, nunca devolvido como evidência.
5. **Ausente é diferente de vazio e de zero.** Campo ausente: o motor não tem essa capacidade. Lista vazia: o motor procurou e não achou. `confianca` ausente: o motor não calcula. Nunca `0` para dizer "não sei".
6. **Fonte única.** Este arquivo define o contrato. Hand-offs, `CLAUDE.md` e prompts apontam para cá.

**Fora desta versão:** pseudonimização antes da LLM (D3), RAG, treino do modelo local, `confianca` por concordância entre LLMs (D4), avaliação de regras de conduta (código determinístico do backend), contagem real de tokens, glossário por cliente, regex como 4ª camada.

---

## 2. Fluxo

```text
Java ──POST /analisar──► validar pedido ──► numerar turnos (regra única, 6.1)
                                              │
                    PIPELINE_VERSAO=v1 ◄──────┤ (corpo v1, sem etapas abaixo)
                                              ▼
              LLM principal ─(falhou)─► LLM secundária ─(falhou)─► modelo local ─(falhou)─► 503
                    │                         │                         │
                    └──────────── saída da LLM (SaidaLLM) ──────────────┘
                                              ▼
            conferir citações (6.2) ► derivar listas v1 (6.3) ► montar AnaliseResponse ► 200
```

Orçamento de tempo **[decidido, D7; calibrar no smoke]**: principal ~55 s, secundária ~35 s, reserva ~10 s para o modelo local, total ≤ 100 s. O Java desiste em 120 s (`ANALISE_SERVICE_TIMEOUT_MS`) **[verificado]**.

---

## 3. Pedido: `POST /analisar`

`Content-Type: application/json`. Campos desconhecidos são ignorados. Campos opcionais vazios (`[]` ou ausentes) não mudam o comportamento.

### 3.1 Campos

| Campo | Tipo | Obrigatório | Regra |
|---|---|---|---|
| `conteudo` | string | **sim** (v1) | Texto bruto com `[LOCUTOR n]`. De 80 a 200.000 caracteres |
| `formatoOrigem` | string | **sim** (v1) | Hoje `"TXT"`. Não altera o comportamento |
| `turnos` | `[{n:int, locutor:int\|null, texto:string}]` | não | Se presente, **vence** `conteudo` para numerar, montar o prompt e conferir citações. `n` consecutivo de 1 a N; `texto` não vazio. Se ausente, o serviço numera `conteudo` pela regra 6.1 **[proposta]** |
| `dataReuniao` | string `AAAA-MM-DD` | não | Só referência para a LLM entender prazos ditos ("até segunda") |
| `padroes` | `[string]` | não | Subconjunto dos 14 padrões (seção 6.1). Ausente ou vazio = os 14. Chave fora da lista → 422 `padrao_desconhecido` |
| `contraexemplos` | `[{padrao, texto, motivo}]` | não | "Não procede" anteriores. `motivo` ∈ `nao_cliente`, `fora_contexto`, `tema_errado`, `outro` |
| `contextoCliente` | `[{tipo, texto, origem, data}]` | não | Ajuste manual por cliente. `tipo` = `ajuste_manual` (único valor nesta versão); `origem` ∈ `vendedor`, `gestor`; `data` = `AAAA-MM-DD` |
| `glossarioTime` | `[{termo, significa, escopo}]` | não | Siglas e nomes internos. `escopo` = `time` (único valor nesta versão) |
| `correcoesAnteriores` | `[{padrao, textoOriginal, correcao, motivo}]` | não | Correções do vendedor. `correcao` = `nao_procede` (único valor nesta versão, **[aberto A7]**) |

### 3.2 Limites (protegem custo e `max_tokens`) **[decidido 11/10, refinar depois]**

| Item | Limite | Estouro |
|---|---|---|
| `conteudo` | 80 a 200.000 caracteres | 422 `conteudo_curto` / `conteudo_longo` |
| `turnos` | até 3.000 itens; `texto` até 5.000 caracteres | 422 `turnos_invalidos` |
| `contraexemplos`, `correcoesAnteriores` | até 50 itens cada; `texto` até 500 caracteres | 422 `pedido_invalido` |
| `contextoCliente`, `glossarioTime` | até 50 itens cada; `texto`/`significa` até 500 caracteres | 422 `pedido_invalido` |

### 3.3 Como os campos opcionais entram na análise

- Entram no prompt **como dados delimitados**, nunca como instrução. O serviço neutraliza qualquer marcação que imite o delimitador (inclusive `</transcricao>`) em `conteudo`, `turnos` e nos campos opcionais **[verificado: hoje não há escape]**.
- `contraexemplos` e `correcoesAnteriores` descrevem o mesmo mecanismo ("isto não é uma ocorrência deste padrão"). O serviço junta os dois e remove duplicatas por `(padrao, texto)`. Qual dos dois o Java passa a enviar é decisão do Kelwin; `correcoesAnteriores` é o nome canônico daqui em diante **[proposta]**.
- Os campos opcionais **não** são pseudonimizados pelo serviço (D3).

---

## 4. Resposta: `200 OK`

### 4.1 Campos da v1 (sempre presentes, mesmo nome e tipo)

| Campo | Tipo | Quem preenche | Regra |
|---|---|---|---|
| `pontosInteresse` | `[{descricao, trecho, turno?}]` | LLM; modelo local: classificador | Pode ser `[]`. `trecho` é literal e conferido. `turno` é novo e opcional |
| `pontosDesinteresse` | `[{descricao, trecho, turno?}]` | **Código**, derivado de `temas` com `risco` (caminho LLM); classificador (modelo local) | Regra 6.3 |
| `oportunidadesVenda` | `[{descricao, trecho, turno?}]` | **Código**, derivado de `temas` com `oportunidade` (caminho LLM); classificador (modelo local) | Regra 6.3 |
| `scoreEngajamento` | int 0 a 100 | LLM / modelo local | Sempre inteiro; o Java o lê como `int` primitivo |
| `sentimentoGeral` | `POSITIVO` \| `NEUTRO` \| `NEGATIVO` | LLM / modelo local | Maiúsculas. Sem outros valores |
| `recomendacaoProximosPassos` | string ≤ 500 \| `null` | **Código**, a partir de `proximosPassos` | Passos unidos por `"; "`, cortados em 500 caracteres no limite de palavra **[decidido 11/10, refinar depois]**. `null` quando não há passos (modelo local). A chave sempre existe |
| `motorUtilizado` | `LLM_PRIMARIA` \| `LLM_SECUNDARIA` \| `MODELO_LOCAL` \| `REGEX_FALLBACK` | **Código** | Quem respondeu. `REGEX_FALLBACK` não é emitido enquanto a 4ª camada não existir **[verificado: arquivo vazio]** |

### 4.2 Campos novos da v2

Campo ausente = o motor não tem a capacidade (seção 5). Campo `[]` = procurou e não achou. Campos ausentes são **omitidos**, nunca enviados como `null`.

| Campo | Tipo | Quem preenche | Regra |
|---|---|---|---|
| `versaoContrato` | `"v2"` | Código | Constante. Ausente na resposta v1 |
| `temas` | `[Tema]` | LLM | Seção 4.3. Modelo local: `[]` **[aberto A3]** |
| `papeis` | `{"<locutor>": "vendedor"\|"cliente"\|"nao_identificado"}` | LLM (como lista) → código monta o dicionário | Chave = número do locutor em texto. Locutor sem papel claro → `nao_identificado`. Reuniões do corpus chegam a 179 locutores **[medido]** |
| `resumo` | string ≤ 1.500 | LLM | |
| `proximosPassos` | `[string]` ≤ 5 itens, ≤ 200 caracteres cada | LLM | Origem de `recomendacaoProximosPassos` |
| `compromissos` | `[{turno, texto, regra}]` | LLM | Só promessas do **vendedor**. `regra` na lista 6.4. O **prazo em data é calculado pelo backend**, não por aqui |
| `sentimentoSerie` | `[[turno, valor]]` | LLM (como lista de objetos) → código converte | `valor` de −1 a 1; `turno` existente; ordem crescente; até 60 pontos |
| `eventosConduta` | `[{tipo, turno, texto, confianca}]` | LLM extrai | `tipo` da lista fechada 6.2. **O serviço não julga se é violação** (é código do backend) |
| `descartados` | `[{origem, texto, motivo, padrao?}]` | **Código** | Tudo que a LLM devolveu e não passou nas regras. Seção 7.2 |
| `tentativas` | `[{motor, ok, erro?, duracaoMs}]` | **Código** | Uma entrada por motor tentado, na ordem. `erro` é um código (seção 6.5), **nunca** mensagem livre nem texto da transcrição |
| `turnos` | `[{n, locutor, texto}]` | **Código** | A numeração que o serviço usou. Permite ao Java gravar a numeração que o serviço usou, sem reaplicar a regra **[decidido 11/10, refinar depois]** |
| `avisos` | `[string]` | **Código** | Códigos curtos, seção 6.6. Pode ser `[]` |

### 4.3 `Tema`

| Campo | Tipo | Regra |
|---|---|---|
| `padrao` | string | Chave dos 14 padrões e presente em `padroes` do pedido. Fora disso o tema é descartado (`padrao_invalido`) |
| `titulo` | string ≤ 120 | Título curto em português |
| `tipos` | `[risco\|oportunidade]` | De 1 a 2 valores, sem repetição. Padrão = tipo do padrão (6.1). Os dois valores quando o mesmo trecho recebe os dois rótulos (tema duplo) |
| `turno` | int ≥ 1 | Turno onde o `texto` começa, **depois da conferência** (pode ser corrigido pelo serviço) |
| `turnoFim` | int | Só quando o trecho atravessa turnos seguidos. Ausente nos demais casos **[proposta]** |
| `tratado` | `true` \| `false` \| `null` | Regra 7.3 |
| `texto` | string 10 a 600 | Recorte literal do texto recebido (regra 7.2) |
| `confianca` | número 0 a 1 | Estimativa da própria LLM (D4). Ausente no modelo local. Não é probabilidade calibrada |

---

## 5. Matriz campo × motor (Release 1)

| Campo | LLM principal / secundária | Modelo local | Regras (`REGEX_FALLBACK`) |
|---|---|---|---|
| 7 campos da v1 | sim | sim (classificador; `recomendacaoProximosPassos` = `null`) | não existe nesta release |
| `versaoContrato`, `tentativas`, `descartados`, `turnos`, `avisos` | sim (código) | sim (código) | — |
| `temas` | sim | `[]` **[aberto A3]** | — |
| `tratado` dentro de `temas` | `true`/`false`, ou `null` sem papel claro | não se aplica | — |
| `confianca` | sim | **ausente** | — |
| `papeis`, `resumo`, `proximosPassos`, `compromissos`, `sentimentoSerie`, `eventosConduta` | sim | **ausentes** | — |
| `turno` dentro dos itens v1 | sim | ausente | — |

O modelo local, depois da correção mínima (Fase 2), lê `[LOCUTOR n]`, divide o texto pela mesma numeração de turnos, devolve os 7 campos e **nunca falha em silêncio**: sem trechos analisáveis ele levanta erro explícito, que vira `erro: "entrada_sem_trechos"` em `tentativas`.

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

| Chave | Descrição |
|---|---|
| `pagamento_confirmado_antes_de_dados` | Vendedor fecha pagamento antes de confirmar os dados cadastrais do cliente |
| `desconto_fora_da_politica` | Desconto oferecido fora da faixa combinada, sem citar aprovação |
| `prazo_prometido_sem_confirmar_capacidade` | Prazo prometido ao cliente sem mencionar checagem interna |

Tipo fora da lista → o evento é descartado (`evento_invalido`).

### 6.3 Derivação das listas da v1 (caminho LLM)

Para cada tema que passou na conferência:
- Se `risco` ∈ `tipos`: entra em `pontosDesinteresse` com `{descricao: titulo, trecho: texto, turno}`.
- Se `oportunidade` ∈ `tipos`: entra em `oportunidadesVenda` com o mesmo formato.
- Tema duplo aparece nas duas listas. A ordem segue a de `temas`.
- Tema com `tratado = true` **continua listado**: ser respondido na reunião não apaga a objeção. O backend decide como exibir.

`pontosInteresse` vem da LLM, passa pela mesma conferência e carrega `turno`.

No **modelo local** as três listas vêm direto do classificador (como hoje), sem `turno`.

### 6.4 Regras de prazo dos compromissos

`sexta` · `segunda` · `sexta_semana_que_vem` · `mesmo_dia` · `mais2` · `null` (sem prazo dito). O serviço devolve só a chave; o backend calcula a data a partir da data da reunião (hand-off de backend, seção 8.10). Promessa com prazo que não cabe em nenhuma regra ("dia 15", "fim do mês") sai com `regra: null` **[aberto: data absoluta]**.

### 6.5 Códigos de `tentativas[].erro`

`nao_configurado` (sem chave) · `timeout` · `limite_requisicoes` · `autenticacao` · `truncado` (saída cortada por `max_tokens`) · `sem_resposta_estruturada` (a LLM não devolveu a ferramenta/formato) · `schema_invalido` · `recusa` · `erro_provedor` · `modelo_indisponivel` · `entrada_sem_trechos` · `erro_interno`.

### 6.6 Códigos de `avisos`

`contingencia_modelo_local` (resposta do modelo local, sem resumo/papéis/compromissos) · `sem_marcacao_locutor` (texto sem `[LOCUTOR n]`, ver 7.1) · `saida_parcial` (parte da saída da LLM foi descartada) **[proposta]**.

### 6.7 Outras listas

- `descartados[].motivo`: `nao_localizado` · `padrao_invalido` · `evento_invalido` · `trecho_curto` · `trecho_longo`.
- `descartados[].origem`: `tema` · `pontoInteresse` · `compromisso` · `eventoConduta`.
- `papeis`: `vendedor` · `cliente` · `nao_identificado`.

---

## 7. Regras

### 7.1 Numeração de turnos (regra única) **[decidido, hand-off de backend, seção 8.2]**

Precisa ser a mesma no Python e no Java: a régua, as citações e "Ver no contexto" dependem dela.

```text
1. Trocar \r\n e \r por \n.
2. Linha que casa com ^\s*\[LOCUTOR\s*(\d+)\]\s*:?\s*(.*)$ (sem diferenciar maiúsculas)
   abre um turno: locutor = o número; texto = o resto da linha, sem espaços nas pontas.
3. Linha não vazia sem a marcação é anexada ao texto do turno anterior, com um espaço.
   Linhas antes da primeira marcação são descartadas.
4. Turnos com texto vazio são removidos.
5. Os turnos que sobram são numerados 1, 2, 3...
```

Fatos do corpus **[medido]** que a implementação precisa respeitar: o número do locutor **não** é sequencial (31% não começam em 1; mediana de 18 locutores por reunião; máximo 179); os turnos são curtos (mediana de 4 palavras) e quebram frases; 43 das 988 transcrições (4,4%) não têm nenhuma marcação.

**Texto sem nenhuma marcação `[LOCUTOR n]`** **[decidido 11/10, refinar depois]**: não falhar. Cada linha não vazia vira um turno com `locutor: null`; se sobrar uma linha só, é um turno único. A resposta traz `avisos: ["sem_marcacao_locutor"]`, `papeis` vazio (`{}`) e `tratado = null` em todos os temas.

### 7.2 Conferência de citações **[decidido, D2; detalhes decididos em 11/10, refinar depois]**

Vale para `temas[].texto`, `pontosInteresse[].trecho`, `compromissos[].texto` e `eventosConduta[].texto`.

1. **Normalizar os dois lados** antes de comparar: Unicode NFC; aspas tipográficas (`“ ” ‘ ’`) viram `"` e `'`; `–` e `—` viram `-`; `…` vira `...`; qualquer sequência de espaços e quebras vira um espaço; tirar as pontas. Não mudar letras nem acentos. A comparação é de substring e diferencia maiúsculas.
2. **Buscar nesta ordem**, parando no primeiro acerto: (a) o turno indicado; (b) janelas de 2 e 3 turnos consecutivos (concatenados com um espaço) que contêm o turno indicado; (c) os turnos de `n−2` a `n+2`, do mais próximo para o mais distante, com as mesmas janelas.
3. **Acerto:** gravar `turno` = turno onde o trecho começa (corrigindo o devolvido pela LLM, se preciso) e `turnoFim` se atravessar turnos. O `texto` gravado é o do **texto recebido**, não o normalizado.
4. **Sem acerto:** o item sai da resposta e entra em `descartados` com `motivo: "nao_localizado"`. Se o item era um tema, as entradas derivadas na v1 também não existem.
5. **Tamanho:** texto normalizado com menos de 10 caracteres → `trecho_curto`; com mais de 600 → `trecho_longo`. Ambos descartados.

Por que a tolerância: os turnos do corpus têm mediana de 4 palavras, então uma frase inteira cruza turnos e a conferência estrita descartaria citação correta.

### 7.3 `tratado`

- `true`: o tema foi respondido na própria reunião, por alguém do papel oposto ao de quem o levantou, em turno posterior.
- `false`: ficou sem resposta na reunião.
- `null`: o motor não sabe quem falou (papel `nao_identificado`, texto sem marcação, ou modelo local). **Nunca** `false` por falta de informação: `false` afirma que ninguém respondeu.

### 7.4 `confianca` **[decidido, D4]**

Vem da própria LLM, por tema e por evento de conduta, de 0 a 1; valores fora do intervalo são limitados a ele. Não é calibrada. O modelo local não a envia (campo ausente). Consumidores não devem tratar `confianca` como probabilidade nem esconder temas por causa dela nesta versão.

### 7.5 Papéis e compromissos

- `papeis` é inferido pela LLM a partir do texto e sempre deve ser exibido como inferido.
- `compromissos` só inclui promessas do vendedor. Sem papel do vendedor identificado, a lista é `[]`.

### 7.6 Limites de saída **[decidido 11/10, refinar depois]**

Até 40 `temas`, 20 `compromissos`, 20 `eventosConduta`, 60 pontos em `sentimentoSerie`, 20 `pontosInteresse`. O excedente é cortado em ordem de `confianca` decrescente e o serviço acrescenta `avisos: ["saida_parcial"]`. Existem para a saída caber em `max_tokens` (hoje 4.000, insuficiente para a v2 **[verificado]**).

### 7.7 Segurança e privacidade **[decidido, D3 e D9]**

- O texto vai cru para Anthropic e OpenAI. Aceitável só com o corpus anonimizado; com dados reais é pendência de LGPD. Não prometer conformidade no pitch.
- Logs e `tentativas` **nunca** contêm texto de transcrição, de contexto ou de glossário. Só motor, código de erro e duração.
- Nenhum trecho do corpus da TOTVS entra no repositório; as fixtures são sintéticas.

---

## 8. Erros, versão e `/health`

### 8.1 Códigos HTTP

| HTTP | `codigo` | Quando | Observação |
|---|---|---|---|
| 200 | — | Algum motor respondeu | Inclui contingência do modelo local |
| 422 | `conteudo_curto`, `conteudo_longo`, `turnos_invalidos`, `padrao_desconhecido`, `pedido_invalido` | Pedido inválido | Corpo abaixo; substitui o `{"detail": [...]}` padrão do FastAPI |
| 503 | `analise_indisponivel` | Nenhum motor respondeu dentro do prazo | Traz `tentativas` |
| 500 | `erro_interno` | Defeito inesperado | Corpo JSON sem stack trace e sem texto da transcrição |

Corpo de erro: `{ "codigo": string, "mensagem": string, "detalhes"?: [...], "tentativas"?: [...] }` (exemplos no Apêndice A). O Java trata qualquer 4xx/5xx como `AnaliseIndisponivelException` **[verificado]**, então a validação de tamanho precisa acontecer **antes** no Java para o usuário não ver "indisponível" por texto curto.

### 8.2 Versão do pipeline

`PIPELINE_VERSAO=v1|v2` (padrão `v2`). A resposta carrega o cabeçalho `X-Insightcall-Pipeline: v1|v2`. Com `v1`: o corpo tem só os 7 campos, os campos novos do pedido são ignorados e o comportamento é o de hoje.

### 8.3 `GET /health`

Superconjunto do atual (`{"status":"ok"}`), sem chamar nenhuma API externa (não gasta token):

```json
{
  "status": "ok",
  "pipelineVersao": "v2",
  "motores": [
    {"motor": "LLM_PRIMARIA", "configurado": true},
    {"motor": "LLM_SECUNDARIA", "configurado": true},
    {"motor": "MODELO_LOCAL", "configurado": true, "carregado": true}
  ]
}
```

`status`: `ok` (alguma LLM configurada e o modelo local carregado), `degradado` (só o modelo local), `indisponivel` (nenhum motor). `configurado` = chave presente; `carregado` = artefato do modelo local lido. O app sobe mesmo sem chaves e sem o `.joblib` (AC7).

---

## 9. Compatibilidade com o Java

**Estado atual** **[verificado no commit `3c15f80`]**: `AnaliseRequest(conteudo, formatoOrigem)` com `"TXT"` fixo; `ResultadoAnalise` com os 7 campos (`int scoreEngajamento`, enums `SentimentoGeral` e `MotorUtilizado`); `RestClient.builder()` estático com read timeout de 120 s e connect de 5 s; qualquer `RestClientException` vira `AnaliseIndisponivelException`.

| O quê | Obrigatório para a Release 1? | Detalhe |
|---|---|---|
| Continuar enviando só `conteudo` + `formatoOrigem` | Nada a mudar | O serviço numera os turnos |
| O record atual ler a resposta v2 sem quebrar | **Teste obrigatório (A4)** | O `RestClient` criado por `RestClient.builder()` usa o conversor Jackson padrão do Spring, que em geral ignora campos desconhecidos **[não verificado em execução]**. Teste: ler `docs/contrato/resposta-v2-llm.json` e `resposta-v2-local.json` em `ResultadoAnalise` |
| Proteger o record | Recomendado | `@JsonIgnoreProperties(ignoreUnknown = true)` em `ResultadoAnalise` e `ItemAnalise`. O `turno` dentro dos itens também depende disso |
| Ler os campos novos | Opcional | Acrescentar ao record com tipos que aceitam ausência (`List`, `Map`, `Double`, `Integer`, nunca primitivos) |
| Enums | **Não acrescentar valores** | `SentimentoGeral` e `MotorUtilizado` ficam como estão. O serviço só emite os 4 valores de motor atuais |
| Gravar `turnos`, `descartados`, `tentativas` | Decisão do Kelwin | Colunas JSON/CLOB na análise (modelo de dados proposto no hand-off de backend) |
| Enviar `turnos`, `dataReuniao`, contexto, glossário, correções | Release 2 do lado Java | Quando enviar `turnos`, a numeração deles é a que vale |
| Validar tamanho antes de chamar | Recomendado | 80 a 200.000 caracteres; o serviço também valida (422) |

Prazos: Java 120 s > serviço ≤ 100 s. Se o Java reduzir o timeout, o serviço precisa reduzir o orçamento junto (D7).

---

## 10. Critérios de aceite da Release 1

| # | Critério | Como provar |
|---|---|---|
| AC1 | `POST /analisar` aceita o pedido v1 **e** o v2; os dois respondem 200 | Teste de API com `pedido-v1.json` e `pedido-v2.json` |
| AC2 | A resposta v2 é superconjunto da v1: os 7 campos presentes e válidos | Teste de contrato contra `resposta-v1.json` e o record Java |
| AC3 | As LLMs preenchem `temas` (padrão da lista de 14), `papeis`, `resumo`, `compromissos`, `sentimentoSerie`, `eventosConduta`, `confianca`, `descartados`, `tentativas` | `resposta-v2-llm.json` + teste de schema |
| AC4 | Toda citação existe literalmente no texto; senão vai para `descartados` | Testes de `conferir_citacoes`: acerto, quebra de frase, invenção |
| AC5 | Nenhuma requisição passa de ~100 s; duas LLMs fora → modelo local responde 200; falha total → 503 estruturado | Testes de orquestrador com clients simulados lentos e com falha |
| AC6 | O modelo local lê `[LOCUTOR n]`, não falha em silêncio e responde no formato v2 | `resposta-v2-local.json` + testes com texto real e sem marcação |
| AC7 | O app sobe sem `.joblib` e sem chaves; `/health` informa cada motor | Teste de import e de `/health` |
| AC8 | `PIPELINE_VERSAO=v1` devolve o comportamento v1 | Teste que roda as duas versões sobre a mesma entrada |
| AC9 | As fixtures validam no Python e no Java | Um teste em cada lado lendo os mesmos JSON |
| AC10 | `pytest` verde sem rede e sem chaves; smoke real com as duas chaves registrado | Saída do `pytest` + `docs/evidencias/smoke-12-10.md` |

---

## 11. Fixtures (`docs/contrato/`)

| Arquivo | Conteúdo | Quem lê |
|---|---|---|
| `pedido-v1.json` | `{conteudo, formatoOrigem}` | Python e Java |
| `pedido-v2.json` | v1 + `turnos`, `dataReuniao`, `padroes` e os quatro campos de contexto | Python |
| `resposta-v1.json` | Os 7 campos | Python e Java |
| `resposta-v2-llm.json` | Resposta completa de LLM: três temas, um evento de conduta, um compromisso e um descartado | Python e Java |
| `resposta-v2-local.json` | Contingência do modelo local | Python e Java |
| `erro-422.json`, `erro-503.json`, `health.json` | Corpos de erro e de saúde | Python |

Os exemplos do Apêndice A são esses arquivos. Foram conferidos por script: cada `texto` existe literalmente no turno indicado, as listas da v1 batem com a derivação 6.3 e os valores são das listas fechadas.

---

## 12. Pendências

| # | Pendência | Padrão adotado até decidir | Dono |
|---|---|---|---|
| A1 | Quem numera os turnos para a interface ("Ver no contexto") | **Adotado:** o serviço numera e devolve `turnos`; o Java grava o que veio. Falta combinar com o Kelwin | João Paulo + Kelwin |
| A2 | Lista definitiva de eventos de conduta e quem a mantém | As 3 ilustrativas (6.2) | João Paulo |
| A3 | O modelo local ganha mapeamento para os 14 padrões ou devolve padrão genérico? | `temas: []` na Release 1 | Release 2 |
| A4 | O Jackson do Java ignora campos desconhecidos? | Assumir que sim e provar com o teste do AC9 | Kelwin |
| A5 | Em que unidade de texto o classificador foi treinado (linha, turno, janela) | **Decidido por ora (11/10):** dividir o texto do modelo local por turno na Fase 2. Conferir no notebook de DS na Release 2 | João Paulo |
| A6 | Transcrição sem nenhuma marcação `[LOCUTOR n]` (4,4% do corpus) | **Adotado (11/10, refinar depois):** não falhar; um turno por linha, `locutor: null`, aviso (7.1) | João Paulo |
| A7 | Outros valores de `correcoesAnteriores.correcao` (ex.: leitura corrigida) | **Fechado para a Release 1 (11/10):** só `nao_procede`. Reabrir na Release 2 | Release 2 |

---

## 13. Histórico de mudanças

| Data | Mudança |
|---|---|
| 2026-10-11 | Primeira versão, aprovada no mesmo dia para a Release 1 (decisões "refinar depois": limites, `turnos` na resposta, texto sem marcação, conferência tolerante, junção de `recomendacaoProximosPassos`; A5 por turno, A7 só `nao_procede`). Define pedido e resposta v2 como superconjunto da v1, conferência de citações, erros, `/health` e compatibilidade com o Java |

Regra de mudança: campo novo opcional não muda a versão; remover ou mudar o significado de um campo da v1 exige `v3` e conversa com o Kelwin.

---

## Apêndice A. Exemplos completos

### A.1 Pedido v1: `pedido-v1.json`

```json
{
  "conteudo": "[LOCUTOR 1] Bom dia, [PESSOA]. Obrigado pelo horário, vamos falar da renovação.\n[LOCUTOR 2] Bom dia. Antes de tudo, preciso falar do suporte.\n[LOCUTOR 2] Abrimos um chamado sobre o fechamento do faturamento há três semanas e até hoje ninguém retornou.\n[LOCUTOR 1] Certo. Passando para a proposta de renovação então.\n[LOCUTOR 3] Na TI a migração dos cadastros terminou no mês passado, sem perda de histórico.\n[LOCUTOR 1] Ótimo. Posso fechar o reajuste fixo por dois anos e dar quinze por cento de desconto agora.\n[LOCUTOR 2] Isso ajuda bastante.\n[LOCUTOR 2] A diretoria quer oferecer telemedicina para os pacientes da ala nova.\n[LOCUTOR 1] Temos um módulo para isso, posso mostrar na próxima reunião.\n[LOCUTOR 3] Só que o orçamento deste ano está bem apertado.\n[LOCUTOR 1] Te envio a proposta de renovação até segunda, com os valores fechados para os dois anos.\n[LOCUTOR 2] Combinado. Obrigada.",
  "formatoOrigem": "TXT"
}
```

### A.2 Pedido v2: `pedido-v2.json`

```json
{
  "conteudo": "[LOCUTOR 1] Bom dia, [PESSOA]. Obrigado pelo horário, vamos falar da renovação.\n[LOCUTOR 2] Bom dia. Antes de tudo, preciso falar do suporte.\n[LOCUTOR 2] Abrimos um chamado sobre o fechamento do faturamento há três semanas e até hoje ninguém retornou.\n[LOCUTOR 1] Certo. Passando para a proposta de renovação então.\n[LOCUTOR 3] Na TI a migração dos cadastros terminou no mês passado, sem perda de histórico.\n[LOCUTOR 1] Ótimo. Posso fechar o reajuste fixo por dois anos e dar quinze por cento de desconto agora.\n[LOCUTOR 2] Isso ajuda bastante.\n[LOCUTOR 2] A diretoria quer oferecer telemedicina para os pacientes da ala nova.\n[LOCUTOR 1] Temos um módulo para isso, posso mostrar na próxima reunião.\n[LOCUTOR 3] Só que o orçamento deste ano está bem apertado.\n[LOCUTOR 1] Te envio a proposta de renovação até segunda, com os valores fechados para os dois anos.\n[LOCUTOR 2] Combinado. Obrigada.",
  "formatoOrigem": "TXT",
  "turnos": [
    {"n": 1, "locutor": 1, "texto": "Bom dia, [PESSOA]. Obrigado pelo horário, vamos falar da renovação."},
    {"n": 2, "locutor": 2, "texto": "Bom dia. Antes de tudo, preciso falar do suporte."},
    {
      "n": 3,
      "locutor": 2,
      "texto": "Abrimos um chamado sobre o fechamento do faturamento há três semanas e até hoje ninguém retornou."
    },
    {"n": 4, "locutor": 1, "texto": "Certo. Passando para a proposta de renovação então."},
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
    {"n": 7, "locutor": 2, "texto": "Isso ajuda bastante."},
    {"n": 8, "locutor": 2, "texto": "A diretoria quer oferecer telemedicina para os pacientes da ala nova."},
    {"n": 9, "locutor": 1, "texto": "Temos um módulo para isso, posso mostrar na próxima reunião."},
    {"n": 10, "locutor": 3, "texto": "Só que o orçamento deste ano está bem apertado."},
    {
      "n": 11,
      "locutor": 1,
      "texto": "Te envio a proposta de renovação até segunda, com os valores fechados para os dois anos."
    },
    {"n": 12, "locutor": 2, "texto": "Combinado. Obrigada."}
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
    {"termo": "SPED", "significa": "módulo fiscal", "escopo": "time"}
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

### A.3 Resposta v1: `resposta-v1.json`

```json
{
  "pontosInteresse": [
    {"descricao": "Reagiu bem ao reajuste fixo com desconto", "trecho": "Isso ajuda bastante."}
  ],
  "pontosDesinteresse": [
    {
      "descricao": "Chamado de faturamento sem retorno",
      "trecho": "Abrimos um chamado sobre o fechamento do faturamento há três semanas e até hoje ninguém retornou."
    },
    {"descricao": "Orçamento do ano apertado", "trecho": "o orçamento deste ano está bem apertado"}
  ],
  "oportunidadesVenda": [
    {
      "descricao": "Telemedicina para a ala nova",
      "trecho": "A diretoria quer oferecer telemedicina para os pacientes da ala nova."
    }
  ],
  "scoreEngajamento": 68,
  "sentimentoGeral": "NEUTRO",
  "recomendacaoProximosPassos": "Responder o chamado de faturamento aberto há três semanas; Enviar a proposta de renovação com valores fechados para dois anos; Agendar a demonstração do módulo de telemedicina",
  "motorUtilizado": "LLM_PRIMARIA"
}
```

### A.4 Resposta v2 de LLM: `resposta-v2-llm.json`

```json
{
  "pontosInteresse": [
    {"descricao": "Reagiu bem ao reajuste fixo com desconto", "trecho": "Isso ajuda bastante.", "turno": 7}
  ],
  "pontosDesinteresse": [
    {
      "descricao": "Chamado de faturamento sem retorno",
      "trecho": "Abrimos um chamado sobre o fechamento do faturamento há três semanas e até hoje ninguém retornou.",
      "turno": 3
    },
    {
      "descricao": "Orçamento do ano apertado",
      "trecho": "o orçamento deste ano está bem apertado",
      "turno": 10
    }
  ],
  "oportunidadesVenda": [
    {
      "descricao": "Telemedicina para a ala nova",
      "trecho": "A diretoria quer oferecer telemedicina para os pacientes da ala nova.",
      "turno": 8
    }
  ],
  "scoreEngajamento": 68,
  "sentimentoGeral": "NEUTRO",
  "recomendacaoProximosPassos": "Responder o chamado de faturamento aberto há três semanas; Enviar a proposta de renovação com valores fechados para dois anos; Agendar a demonstração do módulo de telemedicina",
  "motorUtilizado": "LLM_PRIMARIA",
  "versaoContrato": "v2",
  "temas": [
    {
      "padrao": "suporte_insatisfacao",
      "titulo": "Chamado de faturamento sem retorno",
      "tipos": ["risco"],
      "turno": 3,
      "tratado": false,
      "texto": "Abrimos um chamado sobre o fechamento do faturamento há três semanas e até hoje ninguém retornou.",
      "confianca": 0.9
    },
    {
      "padrao": "modulo_adicional",
      "titulo": "Telemedicina para a ala nova",
      "tipos": ["oportunidade"],
      "turno": 8,
      "tratado": true,
      "texto": "A diretoria quer oferecer telemedicina para os pacientes da ala nova.",
      "confianca": 0.82
    },
    {
      "padrao": "orcamento_restrito",
      "titulo": "Orçamento do ano apertado",
      "tipos": ["risco"],
      "turno": 10,
      "tratado": false,
      "texto": "o orçamento deste ano está bem apertado",
      "confianca": 0.7
    }
  ],
  "papeis": {"1": "vendedor", "2": "cliente", "3": "cliente"},
  "resumo": "Reunião de renovação. O cliente reclamou de um chamado de faturamento sem retorno, reagiu bem ao reajuste fixo, citou interesse em telemedicina e disse que o orçamento do ano está apertado. O vendedor se comprometeu a enviar a proposta até segunda.",
  "proximosPassos": [
    "Responder o chamado de faturamento aberto há três semanas",
    "Enviar a proposta de renovação com valores fechados para dois anos",
    "Agendar a demonstração do módulo de telemedicina"
  ],
  "compromissos": [
    {
      "turno": 11,
      "texto": "Te envio a proposta de renovação até segunda, com os valores fechados para os dois anos.",
      "regra": "segunda"
    }
  ],
  "sentimentoSerie": [[2, -0.2], [3, -0.6], [7, 0.4], [10, -0.3], [12, 0.3]],
  "eventosConduta": [
    {
      "tipo": "desconto_fora_da_politica",
      "turno": 6,
      "texto": "dar quinze por cento de desconto agora",
      "confianca": 0.64
    }
  ],
  "descartados": [
    {
      "origem": "tema",
      "padrao": "cancelamento_citado",
      "texto": "O cliente pediu cancelamento imediato do contrato.",
      "motivo": "nao_localizado"
    }
  ],
  "tentativas": [
    {"motor": "LLM_PRIMARIA", "ok": true, "duracaoMs": 18200}
  ],
  "turnos": [
    {"n": 1, "locutor": 1, "texto": "Bom dia, [PESSOA]. Obrigado pelo horário, vamos falar da renovação."},
    {"n": 2, "locutor": 2, "texto": "Bom dia. Antes de tudo, preciso falar do suporte."},
    {
      "n": 3,
      "locutor": 2,
      "texto": "Abrimos um chamado sobre o fechamento do faturamento há três semanas e até hoje ninguém retornou."
    },
    {"n": 4, "locutor": 1, "texto": "Certo. Passando para a proposta de renovação então."},
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
    {"n": 7, "locutor": 2, "texto": "Isso ajuda bastante."},
    {"n": 8, "locutor": 2, "texto": "A diretoria quer oferecer telemedicina para os pacientes da ala nova."},
    {"n": 9, "locutor": 1, "texto": "Temos um módulo para isso, posso mostrar na próxima reunião."},
    {"n": 10, "locutor": 3, "texto": "Só que o orçamento deste ano está bem apertado."},
    {
      "n": 11,
      "locutor": 1,
      "texto": "Te envio a proposta de renovação até segunda, com os valores fechados para os dois anos."
    },
    {"n": 12, "locutor": 2, "texto": "Combinado. Obrigada."}
  ],
  "avisos": []
}
```

### A.5 Resposta v2 do modelo local (contingência): `resposta-v2-local.json`

Os valores de `scoreEngajamento` e `sentimentoGeral` aqui são ilustrativos: o modelo local mede por trechos, não por turnos.

```json
{
  "pontosInteresse": [
    {"descricao": "Sinal de interesse identificado pelo classificador", "trecho": "Isso ajuda bastante."}
  ],
  "pontosDesinteresse": [
    {
      "descricao": "Sinal de risco identificado pelo classificador",
      "trecho": "Abrimos um chamado sobre o fechamento do faturamento há três semanas e até hoje ninguém retornou."
    },
    {
      "descricao": "Sinal de risco identificado pelo classificador",
      "trecho": "Só que o orçamento deste ano está bem apertado."
    }
  ],
  "oportunidadesVenda": [],
  "scoreEngajamento": 67,
  "sentimentoGeral": "NEUTRO",
  "recomendacaoProximosPassos": null,
  "motorUtilizado": "MODELO_LOCAL",
  "versaoContrato": "v2",
  "temas": [],
  "descartados": [],
  "tentativas": [
    {"motor": "LLM_PRIMARIA", "ok": false, "erro": "timeout", "duracaoMs": 55000},
    {"motor": "LLM_SECUNDARIA", "ok": false, "erro": "limite_requisicoes", "duracaoMs": 1300},
    {"motor": "MODELO_LOCAL", "ok": true, "duracaoMs": 240}
  ],
  "turnos": [
    {"n": 1, "locutor": 1, "texto": "Bom dia, [PESSOA]. Obrigado pelo horário, vamos falar da renovação."},
    {"n": 2, "locutor": 2, "texto": "Bom dia. Antes de tudo, preciso falar do suporte."},
    {
      "n": 3,
      "locutor": 2,
      "texto": "Abrimos um chamado sobre o fechamento do faturamento há três semanas e até hoje ninguém retornou."
    },
    {"n": 4, "locutor": 1, "texto": "Certo. Passando para a proposta de renovação então."},
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
    {"n": 7, "locutor": 2, "texto": "Isso ajuda bastante."},
    {"n": 8, "locutor": 2, "texto": "A diretoria quer oferecer telemedicina para os pacientes da ala nova."},
    {"n": 9, "locutor": 1, "texto": "Temos um módulo para isso, posso mostrar na próxima reunião."},
    {"n": 10, "locutor": 3, "texto": "Só que o orçamento deste ano está bem apertado."},
    {
      "n": 11,
      "locutor": 1,
      "texto": "Te envio a proposta de renovação até segunda, com os valores fechados para os dois anos."
    },
    {"n": 12, "locutor": 2, "texto": "Combinado. Obrigada."}
  ],
  "avisos": ["contingencia_modelo_local"]
}
```

### A.6 Erros

`erro-503.json`:

```json
{
  "codigo": "analise_indisponivel",
  "mensagem": "Nenhum motor de análise respondeu dentro do prazo.",
  "tentativas": [
    {"motor": "LLM_PRIMARIA", "ok": false, "erro": "timeout", "duracaoMs": 55000},
    {"motor": "LLM_SECUNDARIA", "ok": false, "erro": "autenticacao", "duracaoMs": 420},
    {"motor": "MODELO_LOCAL", "ok": false, "erro": "modelo_indisponivel", "duracaoMs": 3}
  ]
}
```

`erro-422.json`:

```json
{
  "codigo": "conteudo_curto",
  "mensagem": "O conteúdo tem menos de 80 caracteres.",
  "detalhes": [
    {"campo": "conteudo", "limite": 80, "recebido": 42}
  ]
}
```

---

## Apêndice B. De-para: nomes dos hand-offs → nomes do contrato

Os hand-offs (08/10 e 09/10) usam nomes da demo. O código e o Java usam os nomes da v1. **Vale o da coluna do meio.**

| Nome no hand-off / demo | Nome no contrato | Observação |
|---|---|---|
| `motor`: `llm1` / `llm2` / `local` / `regras` | `motorUtilizado`: `LLM_PRIMARIA` / `LLM_SECUNDARIA` / `MODELO_LOCAL` / `REGEX_FALLBACK` | Backend traduz para a demo |
| `score` | `scoreEngajamento` | |
| `sentimento`: `positivo`/`neutro`/`negativo` | `sentimentoGeral`: `POSITIVO`/`NEUTRO`/`NEGATIVO` | |
| `interesse[]` com `texto`, `turno`, `citacao` | `pontosInteresse[]` com `descricao`, `trecho`, `turno` | |
| `proximosPassos[]` | `proximosPassos[]` **e** `recomendacaoProximosPassos` (string) | A string mantém a v1 |
| `temas[].texto` | `temas[].texto` | Igual |
| — | `pontosDesinteresse[]`, `oportunidadesVenda[]` | Derivados dos `temas` (6.3) |
| `entradas.turnos[].n` | `turnos[].n` | Igual |
