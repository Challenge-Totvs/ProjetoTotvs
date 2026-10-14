# Runbook da demo — banca TOTVS, 15/10/2026

Passo a passo para subir, conferir, ensaiar e apresentar o InsightCall. O roteiro de 5 minutos da cadeia de motores
(só o serviço Python, por terminal) está em [roteiro-ensaio-falha.md](roteiro-ensaio-falha.md); este runbook cobre o
sistema inteiro, pela tela.

Nenhum comando abaixo imprime chave, senha do banco ou texto de transcrição. Não abra os arquivos `.env` com a tela
compartilhada.

---

## 1. Pré-requisitos da máquina da apresentação

| Item | Versão / valor | Onde conferir |
|---|---|---|
| Java | 25 | `backend/pom.xml` (`java.version`) · `java -version` |
| Maven | qualquer 3.9.x (o repositório não tem `mvnw`) | `mvn -v` |
| Node | v24.16.0: rodar `node -v` onde o front sobe | `node -v` (versão que funcionou no ensaio de 14/10) |
| Python | 3.11+ | `README.md` · `python --version` |
| Rede | acesso ao Oracle da FIAP, a `api.anthropic.com` e a `api.openai.com` | seção 3, `scripts/teste_rede.py` |

**Backend (Java).** O `application.properties` lê estas variáveis de ambiente; o modelo está em `backend/.env.example`
(formato `CHAVE=valor;CHAVE=valor`, o mesmo do campo *Environment variables* do IntelliJ):

| Variável | Para quê |
|---|---|
| `DB_URL`, `DB_PORT`, `DB_SID` | host, porta e SID do Oracle (a URL JDBC é montada no `application.properties`) |
| `DB_USERNAME`, `DB_PASSWORD` | credenciais do Oracle |
| `JWT_SECRET` | segredo que assina os tokens |
| `ANALISE_SERVICE_URL` | URL do Python; o padrão já é `http://localhost:8000` |

Opcionais, com padrão: `JWT_EXPIRATION_MS` (3600000) e `ANALISE_SERVICE_TIMEOUT_MS` (120000). O
`scripts/teste_rede.py` lê `DB_URL` e `DB_PORT` de `backend/.env`; o Spring **não** lê esse arquivo sozinho: defina as
variáveis no terminal ou na configuração de execução do IntelliJ.

**Serviço de análise (Python).** `analise-service/.env` (modelo em `analise-service/.env.example`), lido na subida do
uvicorn:

| Variável | Para quê |
|---|---|
| `LLM_PRINCIPAL_PROVIDER`, `LLM_PRINCIPAL_API_KEY`, `LLM_PRINCIPAL_MODEL` | llm1 (Anthropic) |
| `LLM_SECUNDARIA_PROVIDER`, `LLM_SECUNDARIA_API_KEY`, `LLM_SECUNDARIA_MODEL` | llm2 (OpenAI) |
| `LLM_PRINCIPAL_WORKSPACE_ID` | opcional (cabeçalho `anthropic-workspace-id`) |

Variáveis só de ensaio, definidas no terminal (nunca no `.env` do dia): `FORCAR_FALHA` e `PIPELINE_VERSAO`
(seção 4).

**Contas do seed** (`backend/src/main/resources/demo/seed.json`), todas com a senha `demo1234`:

- vendedor: `kelwin.bastos@insightcall.com` (também é a conta que marca que o seed já foi carregado)
- gestor: `mariana.lopes@insightcall.com`
- outros vendedores: `bruno.melo@`, `caio.torres@` e `ana.ribeiro@insightcall.com`

---

## 2. Ordem de subida

Três terminais, nesta ordem. O Python sobe primeiro porque o backend consulta o `/health` dele para o banner de motores.

**Terminal 1 — Python (porta 8000)**

```powershell
cd analise-service
.venv\Scripts\activate                       # primeira vez: python -m venv .venv ; pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000   # sem --reload no dia da demo
```

Confira em `http://localhost:8000/docs`. Para trocar de cenário (seção 4): `Ctrl+C`, defina a variável e suba de novo.
O reinício é obrigatório: o `.env` e as variáveis só são lidos na subida, e o reinício zera a memória do `/health`.

**Terminal 2 — Backend (porta 8080, perfil `demo`)**

```powershell
cd backend
# variáveis da seção 1 já definidas neste terminal
mvn spring-boot:run "-Dspring-boot.run.profiles=demo"
```

Pelo IntelliJ, basta marcar *Active profiles: demo* na configuração de execução; o comando `mvn` acima é a
alternativa. O perfil `demo` liga o `CargaDemo` (`@Profile("demo")`): na primeira subida num banco vazio ele grava o seed
(5 usuários, 16 clientes, 33 reuniões, 47 temas, 8 compromissos); nas seguintes, vê que a conta
`kelwin.bastos@insightcall.com` existe e não faz nada. Sem o perfil `demo`, o seed não é carregado. Pelo IntelliJ, o
equivalente é *Active profiles: demo* na configuração de execução. O Hibernate está com `ddl-auto=update`: a primeira
subida também cria as colunas novas (ex.: `TEMA.SEMELHANTE_NAO_PROCEDE_ID`).

**Terminal 3 — Front (porta 5173)**

```powershell
cd frontend
npm install        # só na primeira vez (ou npm ci)
npm run dev
```

Abra **`http://localhost:5173`**. O CORS do backend (`SecurityConfig`) só aceita essa origem: não use `127.0.0.1:5173`,
outra porta nem o `npm run preview` (porta 4173). O front chama o backend em `http://localhost:8080` (padrão de
`VITE_API_URL`).

---

## 3. Verificações antes da banca

Rode na manhã da banca, na máquina e na rede da apresentação, com o Python no ar (exceto o teste de rede).

| # | Comando (pasta) | O que confere | Passou se |
|---|---|---|---|
| 1 | `python scripts/teste_rede.py` (raiz do repositório) | TCP até o Oracle e HTTPS até as duas APIs de LLM. Imprime OK/FALHOU e latência, nunca host ou chave | tudo OK |
| 2 | `python scripts/smoke_llm.py llm1 llm2` (`analise-service/`) | uma chamada real a cada LLM com o pedido sintético do contrato; imprime motor, tempo e contagens | as duas OK (custa centavos) |
| 3 | `python scripts/pre_demo.py --exigir-real` (`analise-service/`) | `/health`, `/analisar` curta (12 turnos) e grande (399, sintética), `/similares`; com `--exigir-real` falha se o pipeline não for `real` | termina em `PRONTO PARA A DEMO` (saída 0) |

Leitura do `pre_demo.py`: saída 1 = Python fora do ar (ele mostra o comando de subida); saída 2 = `NAO PRONTO`, com a
lista do que falhou. Referência de um resultado bom: [evidencias/pre-demo-13-10.md](evidencias/pre-demo-13-10.md).

Depois dos três: faça login no front com `kelwin.bastos@insightcall.com` / `demo1234` e confira que o Início carrega e
que **não** há banner amarelo de motores.

---

## 4. Testes de ensaio (A a G)

Ensaie todos **antes** da limpeza do banco (seção 5). Cada análise de teste grava uma transcrição; o mesmo texto para o
mesmo cliente não pode ser enviado duas vezes (409 `transcricao_duplicada`).

Notas que valem para todos:

- O banner de motores no topo vem do `/health` do Python, via backend (cache de 10 s) e o front pergunta a cada 60 s.
  Depois de trocar de cenário, **recarregue a página (F5)** para ver o banner na hora.
- Para mandar uma análise: *Nova transcrição* (`/transcricoes/nova`) → *Usar transcrição de exemplo* (preenche o texto e
  o cliente Hospital Santa Luzia) → *Enviar e analisar*. Em ensaio, para não gastar a amostra, cole outra transcrição
  **sintética** (por exemplo, gerada com `analise-service/scripts/gerar_transcricao_sintetica.py`).
- Ao fim de cada cenário: `Ctrl+C` no terminal 1, `$env:FORCAR_FALHA = ""`, `$env:PIPELINE_VERSAO = ""` e suba de novo.

| Teste | Como provocar | O que se espera na tela |
|---|---|---|
| **A. Fluxo normal** | Python sem variáveis de ensaio. Envie e analise uma transcrição | Tela de andamento com as etapas; ao fim, abre a página da reunião e o aviso "Análise concluída por LLM principal: N temas novos…". Sem banner. Temas com citação literal, score, sentimento e próximos passos |
| **B. llm1 fora** | Terminal 1: `$env:FORCAR_FALHA = "llm1"` e suba de novo. F5 no front. Envie uma transcrição | Banner amarelo: "A LLM principal não está respondendo. As próximas análises seguem pela LLM secundária…". A análise conclui com "Análise concluída por LLM secundária…". A cadeia mostra a tentativa da llm1 com erro e a llm2 ok. Pode vir com menos temas (seção 7) |
| **C. llm1 e llm2 fora** | `$env:FORCAR_FALHA = "llm1,llm2"`, suba de novo, F5. Envie uma transcrição | Banner: "As duas LLMs não estão respondendo… modelo local, marcadas como contingência… Reenvie a transcrição quando uma LLM voltar." A reunião abre com o aviso "Análise em contingência pelo modelo local: sem resumo, sem compromissos e sem leitura de quem falou…" |
| **D. Python parado** | `Ctrl+C` no terminal 1 e **não** suba de novo. F5. Envie uma transcrição | Banner de LLMs fora (o backend vê o Python fora do ar). Ao analisar: "O serviço de análise está fora do ar. A transcrição ficou gravada; tente analisar de novo em instantes." (o backend devolve 503 `analise_indisponivel`). **Não saia da tela**: suba o Python e clique de novo em *Enviar e analisar*; a tela reaproveita a transcrição já gravada e não dá 409 |
| **E. Mock** | `$env:PIPELINE_VERSAO = "mock"`, suba de novo. Envie uma transcrição | A análise volta na hora com a resposta gravada de `docs/contrato/resposta-v3-llm.json` (motor llm1), qualquer que seja o texto. Serve para provar o fluxo sem LLM. **Não use no dia** e lembre de limpar a variável: o `pre_demo.py --exigir-real` reprova esse modo |
| **F. Contraexemplo** | Num cliente com temas, abra um tema e use *Marcar como não procede* (informe o motivo). Depois envie uma reunião **nova do mesmo cliente** que fale do mesmo assunto | O tema novo aparece no mapa de temas com "· parecido com não procede", e no inspetor do tema: "Parecido com um trecho marcado como não procede antes: …". O aviso só aparece em tema **novo** e depende do `/similares` do Python |
| **G. Busca no histórico** | Na página de um cliente com reuniões (`/clientes/:id`), seção *Buscar no histórico*. Digite um assunto (ex.: "suporte", "preço") e clique *Buscar* | Lista dos trechos de reuniões anteriores mais parecidos. Sem resultado: "Nada encontrado — Nenhum trecho parecido com …". Também depende do Python no ar |

Plano B só do motor, sem rede e sem chave: `python scripts/ensaio_falha.py` (em `analise-service/`) imprime a tabela dos
cenários de falha em segundos. Tempos medidos ao vivo: [evidencias/ensaio-falha-13-10.md](evidencias/ensaio-falha-13-10.md).

---

## 5. Limpeza do banco antes da banca

Script: [`scripts/limpar_demo.sql`](../scripts/limpar_demo.sql). Ele apaga só o que os testes criaram (reuniões,
transcrições, análises, temas, citações, eventos, compromissos e notificações) e mantém usuários, clientes, contatos,
padrões e os dados do seed.

Antes de rodar:

1. **Suba o backend pelo menos uma vez antes**, com o código atual: é essa subida que cria a coluna
   `TEMA.SEMELHANTE_NAO_PROCEDE_ID`, que o script usa. Sem ela, o script falha. Confirmado em 14/10/2026: no Oracle
   da demo a coluna já existe (NUMBER(19,0), anulável). Se a banca usar outro banco, a primeira subida do backend a cria.
2. **Pare o backend** (terminal 2) durante a limpeza.
3. **Faça backup** do schema.
4. Rode só **depois do último ensaio** (seção 4).

Como rodar:

1. Desligue o autocommit do cliente SQL.
2. Rode a seção 1 (CONFERÊNCIA) e anote os números.
3. Antes do `ROLLBACK`, cole a consulta 1.1 do script (totais por tabela) logo depois do passo 2.9 e rode a seção 2
   inteira. Sem essa consulta, o `ROLLBACK` desfaz tudo e não dá para ver o resultado da limpeza.
4. Só troque, de propósito, o `ROLLBACK;` pelo `COMMIT;` comentado se o resultado for: REUNIAO 33, TRANSCRICAO 27,
   ANALISE 27, TEMA 47, CITACAO 60, EVENTO_TEMA 1, COMPROMISSO 8, NOTIFICACAO 0.

Depois da limpeza, confira os cadastros de teste:

```sql
SELECT id, nome FROM CLIENTE ORDER BY id;
SELECT id, nome, email FROM CONSULTOR ORDER BY id;
```

O seed tem 16 clientes e 5 usuários. O que passar disso é de teste (por exemplo, a conta `integracao@insightcall.test`
e os clientes criados pelo `scripts/fluxo_integracao.py`) e aparece na visão da gestora. O script **não** apaga
cadastros, de propósito: a decisão de apagá-los à mão é do Kelwin.

**Depois da limpeza, não reenvie a transcrição de exemplo** (nem para "testar"). O próximo envio dela tem de ser o da
banca: um segundo envio do mesmo texto para o mesmo cliente é bloqueado pelo hash duplicado (409
`transcricao_duplicada`, "Esta transcrição já foi enviada.").

---

## 6. Se algo falhar durante a demo

```
A análise está lenta?
├─ Até ~30 s com a tela de andamento contando: normal (llm2 chega a ~20 s na transcrição grande). Fale enquanto espera.
└─ Passou de 120 s: o backend desiste e devolve 503 → siga o ramo "503".

Apareceu "O serviço de análise está fora do ar" (503)?
├─ Olhe o terminal 1. Python caiu? Suba de novo (python -m uvicorn app.main:app --port 8000).
├─ NÃO recarregue nem saia da tela: clique de novo em "Enviar e analisar" (reaproveita a transcrição gravada).
└─ Voltou a falhar? Diga "é o 503 estruturado: o sistema não inventa análise" e mostre uma reunião já analisada do seed.

Apareceu o banner amarelo sem você ter forçado nada?
└─ É a cadeia funcionando (llm2 ou modelo local assumiu). Siga a demo e use isso como prova de resiliência.

A rede caiu (ou o Oracle não responde: login falha, telas não carregam)?
├─ Rode python scripts/teste_rede.py para saber o que caiu (Oracle ou APIs de LLM).
├─ Só as LLMs caíram: o sistema segue no modelo local (banner de contingência). Continue.
├─ Caiu o Oracle: o front não funciona. Mostre o motor sozinho: analise-service/scripts/ensaio_falha.py (offline)
│  e o roteiro de terminal de docs/roteiro-ensaio-falha.md, se ainda houver internet para as LLMs.
└─ Nada disso resolve em ~1 min → plano C.

Nada funciona?
└─ Plano C: passe o vídeo gravado da demo e narre por cima. Não tente consertar ao vivo.
   Vídeo: PREENCHER: onde está o vídeo (caminho no computador da apresentação e cópia de reserva em pendrive ou nuvem).
```

---

## 7. Ressalvas para a fala

Diga com estas palavras, para não prometer o que não existe:

- **Pseudonimização:** o backend troca por pseudônimos, antes de mandar para qualquer LLM externa, **só os nomes que
  estão no cadastro** daquela reunião (o cliente, os contatos dele e o consultor). Um nome que aparece na conversa e não está cadastrado vai como está.
  Reconhecer esses nomes automaticamente (**E8**) é **roadmap**.
- **Reprocessamento automático (RF17) é roadmap.** Quando a análise sai em contingência e uma LLM volta, a reunião não é
  reanalisada sozinha; a interface pede para reenviar a transcrição.
- **A llm2 acha menos temas que a llm1.** Na checagem de 13/10, a transcrição curta saiu com 5 temas pela llm1 e 3 pela
  llm2 (a grande, 6 e 6). A resposta continua válida e com citações conferidas, mas é menos completa: é por isso que a
  llm1 é a principal.
