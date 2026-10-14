# Integração backend ↔ analise-service — 13-14/10

Ensaio de 13/10, das 22h40 às 23h, no Wi-Fi, na branch `integracao-backend` (criada de `origin/main`). Este arquivo
traz só status, contagens, tempos e nomes de arquivo: nenhum texto de transcrição e nenhum valor de chave.
As transcrições usadas são sintéticas: a curta está embutida em `scripts/fluxo_integracao.py` e a grande sai de
`analise-service/scripts/gerar_transcricao_sintetica.py`.

## Resumo

| Etapa | Status | Tempo | Comando exato (Git Bash, na raiz) |
|---|---|---|---|
| 0 Inventário | ok, com ressalvas | — | `git fetch`; `java -version`; `node -v`; `analise-service/.venv/Scripts/python.exe --version` |
| 1a Backend `mvn test` | **140/141**: `contextLoads` falha sem as variáveis do Oracle | 16 s | `cd backend && JAVA_HOME=~/.jdks/temurin-25.0.4.1 ~/.m2/wrapper/dists/apache-maven-3.9.16-bin/5grr65jo27hi51sujmtcldfovl/apache-maven-3.9.16/bin/mvn -B test` |
| 1b Frontend | `npm ci` ok, `build` ok, `lint` com 0 erros e 5 avisos | 17 s + 5 s | `cd frontend && npm ci && npm run build && npm run lint` |
| 1c analise-service | **522 passed** | 23 s | `cd analise-service && .venv/Scripts/python.exe -m pytest -q` |
| 2 Rede (Wi-Fi) | Oracle OK 74 ms · Anthropic OK 232 ms · OpenAI OK 111 ms | 1 s | `python scripts/teste_rede.py` (com DB_URL/DB_PORT no ambiente; ver nota 2) |
| 3a Fluxo real, transcrição curta (687 car., 7 turnos) | 200, `llm1`, 4 temas, 4 com citação, 2 compromissos, score 72 | **7,5 s** | `python scripts/fluxo_integracao.py` |
| 3b Fluxo real, transcrição grande (77.248 car., 399 turnos, 6 temas plantados) | 200, `llm1`, 6 temas, 6 com citação, 2 compromissos, score 55 | **9,1 s** | `python scripts/fluxo_integracao.py --pedido <scratch>/grande.json` |
| 4a `FORCAR_FALHA=llm1` | 200, tentativas `llm1:false → llm2:true`, 2 temas com citação; `/health` e `/api/motores/status` com llm1 `ok:false` | 7,5 s | `FORCAR_FALHA=llm1 uvicorn …`; `python scripts/fluxo_integracao.py --reuniao 90 --transcricao 66` |
| 4b Python parado | 503 `analise_indisponivel`; reunião 90 continua `aguardando` com transcrição; nova tentativa com o Python de volta deu 200 | 0,2 s | Python parado; `python scripts/fluxo_integracao.py` |
| 4c `PIPELINE_VERSAO=mock` | 200, `llm1` (resposta gravada), 3 temas, 1 compromisso; `/health` `pipelineVersao:"mock"` | 0,8 s | `PIPELINE_VERSAO=mock uvicorn …`; `python scripts/fluxo_integracao.py` |
| 5 Health | sem divergência com o contrato §8.3 (ver abaixo); handoff de 13/10 ausente | — | leitura de `MotorStatusService`/`StatusMotores` |
| 6 `/similares` e contraexemplos | **não feito**: bloqueado (ver Pendências) | — | — |

`python` = `analise-service/.venv/Scripts/python.exe`. Os serviços foram subidos assim:

```bash
# analise-service (real); para 4a acrescente FORCAR_FALHA=llm1, para 4c troque para PIPELINE_VERSAO=mock
cd analise-service && unset ANTHROPIC_API_KEY OPENAI_API_KEY && PIPELINE_VERSAO=real .venv/Scripts/python.exe -m uvicorn app.main:app --port 8000

# backend (subiu em 34 s); as DB_*/JWT_SECRET vieram do run config do IntelliJ, injetadas só no processo
cd backend && export JAVA_HOME=$(cygpath -w ~/.jdks/temurin-25.0.4.1) ANALISE_SERVICE_URL=http://localhost:8000 JWT_EXPIRATION_MS=43200000
mvn -B -q spring-boot:run
```

## Notas por etapa

0. **Inventário.** Java no PATH: 21.0.7, mas o `pom.xml` pede 25. O JDK 25 está em `~/.jdks/temurin-25.0.4.1`. Não há
   `mvn` no PATH nem `mvnw` no `backend/`; usei o Maven 3.9.16 do cache do wrapper (`~/.m2/wrapper/dists`). Node v22.18.0.
   Python do `.venv`: 3.12.1. `origin/pre-demo-script` não existe; os commits da `pre-demo-script` local já estão
   no `origin/main`, então não houve merge.
   - `backend/.env.example` pede: DB_URL, DB_PORT, DB_SID, DB_USERNAME, DB_PASSWORD. Não existe `backend/.env`.
     Essas variáveis, mais JWT_SECRET, estão no run config `ApiApplication` do IntelliJ (`.idea/workspace.xml`).
   - `analise-service/.env.example` pede: LLM_PRINCIPAL_{PROVIDER,MODEL,API_KEY} e LLM_SECUNDARIA_{PROVIDER,MODEL,API_KEY}.
     O `.env` real tem as seis.
1. **Base.** `contextLoads` é falha de ambiente (ORA-17866 com a porta vazia), não de código; com as variáveis do
   IntelliJ o contexto sobe (etapa 3). Não mexi. Os avisos do lint (`only-export-components`, `exhaustive-deps`) não
   travam o build.
2. **Rede.** `scripts/teste_rede.py` (só biblioteca padrão) lê DB_URL/DB_PORT de `backend/.env` ou, se ele não existir,
   do ambiente. Como hoje só o IntelliJ tem as variáveis, ou se cria o `backend/.env` (já ignorado pelo git), ou se
   exportam DB_URL e DB_PORT antes de rodar. Falta a rodada no 4G (João).
3. **Fluxo real.** Usuário criado por `POST /api/auth/register` (`integracao@insightcall.test`), sem o perfil `demo`.
   Cada execução cria cliente, reunião, transcrição, análise e leitura. Reuniões 88 e 89 no Oracle.
   Tempo do `/analisar` medido no cliente HTTP do backend: 7,5 s (curta) e 9,1 s (grande), bem abaixo dos 120 s.
4. **Falhas.** (a) A llm2 achou menos temas que a llm1 na mesma transcrição curta (2 contra 4): esperado para
   contingência, mas vale saber na demo. (b) Comportamento certo, mas **não há teste Java** cobrindo
   `analise_indisponivel` (nenhum arquivo em `backend/src/test` cita esse código). (c) No mock, as citações gravadas são
   as da fixture `resposta-v3-llm.json`, não as da transcrição enviada: serve como rollback, não para mostrar citação.
5. **Health.** O contrato §8.3 diz que o Java lê `motores[].motor/ok` (motor ausente conta como fora do ar) e que
   `status`/`pipelineVersao` são extras. O backend faz exatamente isso (`MotorStatusService`, cache de 10 s; Python
   fora do ar vira os quatro `ok:false`). Na 4a, `/api/motores/status` mostrou llm1 `false` e os outros `true`.
   Não há divergência real com o contrato. `docs/handoff-kelwin-13-10.md` não está no repo: se ele pedir que o Java
   exponha `status` (`ok|degradado|indisponivel`), isso é mudança nova, não correção.

## Bug encontrado: fuso na criação de reunião (backend)

`ReuniaoService.criar` faz `request.dataHora().toLocalDateTime()`, mas o Jackson já normalizou o `OffsetDateTime`
para UTC. Efeito confirmado por HTTP: `"2026-10-13T20:00:00-03:00"` é gravado como `2026-10-13T23:00:00`.
Consequências: (1) toda reunião criada pelo frontend fica 3 h adiantada; (2) depois das 21h de Brasília, uma
reunião "aguardando" de hoje vira amanhã em UTC e é recusada com 422 `data_invalida`. O script de fluxo contorna com
09:00 do dia. Correção proposta (não aplicada, ver Pendências), no mesmo padrão do `InicioService`:

```java
private static final ZoneId FUSO = ZoneId.of("America/Sao_Paulo");

static LocalDateTime horaLocal(OffsetDateTime dataHora) {        // em criar(): var dataHora = horaLocal(request.dataHora());
    return dataHora.atZoneSameInstant(FUSO).toLocalDateTime();
}
// validarStatusEData: LocalDateTime.now(FUSO) e LocalDate.now(FUSO)
```

Teste: `horaLocal(OffsetDateTime.parse("2026-10-14T01:30:00Z"))` deve dar `2026-10-13T22:30`.
Reuniões já gravadas pelo frontend continuariam com +3 h; corrigir os dados antigos é decisão do Kelwin.

## Pendências e por quê

- **Edição em `backend/` bloqueada**: `.claude/settings.json` do projeto tem `Edit(/backend/**)` e `Edit(/frontend/**)`
  em `deny`. Respeitei a regra. Por isso ficaram de fora: a correção de fuso acima, o teste Java da 4b e a etapa 6
  (cliente `POST /similares` e contraexemplos `naoProcede` no pedido). Para fazer: liberar a regra nesta sessão ou o
  Kelwin aplicar.
- Etapa 6 também exigiria as etapas 1 a 5 verdes; a 1a tem o `contextLoads` dependente do Oracle.
- Rodada do `teste_rede.py` no 4G: com o João.
- `docs/handoff-kelwin-13-10.md`: pedir ao João para conferir a etapa 5 contra ele.
- Sugestão: um `backend/.env` local (ignorado pelo git) ou um perfil de teste com H2 deixaria o `mvn test` verde fora
  do IntelliJ.

## Arquivos desta rodada

`scripts/teste_rede.py`, `scripts/test_teste_rede.py`, `scripts/fluxo_integracao.py`, `scripts/test_fluxo_integracao.py`
(9 testes: `python -m pytest -q scripts/`) e este relatório.
