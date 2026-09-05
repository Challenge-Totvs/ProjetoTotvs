# Planejamento Ágil — InsightCall

**Metodologia:** Scrum adaptado para desenvolvedor único ("Solo Scrum")
**Início:** 04/09/2026 | **Entrega/Apresentação:** 14/09/2026
**Capacidade estimada:** ~42h efetivas

## Calendário de disponibilidade

| Data | Dia | Janela | Horas estimadas |
|---|---|---|---|
| 04/09 (sex) | Setup noturno | Noite | 2h |
| 05/09 (sáb) | Fim de semana 1 | Dia inteiro | 8h |
| 06/09 (dom) | Fim de semana 1 | Dia inteiro | 8h |
| 07 a 11/09 (seg-sex) | Semana | 2h/dia | 10h |
| 12/09 (sáb) | Fim de semana 2 | Dia inteiro | 8h |
| 13/09 (dom) | Fim de semana 2 | Dia inteiro | 8h |
| 14/09 (seg) | Entrega | Sem código novo | Ensaio/buffer |
| **Total** | | | **~44h** |

Regra de ouro: **qualquer atraso corta primeiro os itens "Could" e "Should" do backlog**, nunca o núcleo "Must" (auth → CRUD → transcrição → análise → tela de resultado).

---

## Sprint 0 — Setup do ambiente
**Quando:** 04/09 (noite) — 2h
**Objetivo:** ambiente pronto para codar sem fricção no fim de semana.

> ⚠️ **Ação prévia (antes até do Sprint 0):** solicitar/confirmar com a faculdade o acesso ao servidor Oracle (host, porta, service name, usuário, senha, necessidade de VPN). Como é uma dependência externa, quanto antes for resolvida, menor o risco de travar o Sprint 1.

| Task | Estimativa | Prioridade |
|---|---|---|
| Criar repositório (backend + frontend) e estrutura de pastas | 20min | Must |
| Configurar conexão com o servidor Oracle da faculdade e validar acesso | 40min | Must |
| Gerar esqueleto Spring Boot (Web, Data JPA, Security, Validation, Lombok, driver Oracle) | 30min | Must |
| Gerar esqueleto React (Vite) com rotas básicas | 20min | Must |
| Configurar `application.yml` (datasource, JWT secret) | 10min | Must |

**Definition of Done:** projeto sobe local (`mvn spring-boot:run` e `npm run dev`) sem erro, conexão com Oracle validada com uma tabela de teste.

---

## Sprint 1 — Backend Core (Fim de semana 1)
**Quando:** 05–06/09 — 16h
**Objetivo:** autenticação + CRUDs essenciais + upload de transcrição funcionando via Swagger/Postman.

### Sábado 05/09 (8h) — Modelagem + Autenticação
| Task | Estimativa | Prioridade |
|---|---|---|
| Modelar entidades JPA (`Consultor`, `Cliente`, `Reuniao`, `Transcricao`, `Analise`) | 1h30 | Must |
| Configurar Spring Security 6 (SecurityFilterChain, PasswordEncoder) | 1h | Must |
| Implementar geração/validação de JWT (`JwtProvider`, `JwtAuthFilter`) | 2h | Must |
| Endpoints de registro e login (`/api/auth/**`) | 1h30 | Must |
| Teste manual do fluxo completo de login via Postman | 1h | Must |

### Domingo 06/09 (8h) — CRUDs + Upload
| Task | Estimativa | Prioridade |
|---|---|---|
| CRUD de `Cliente` (controller, service, repository, DTO) | 1h30 | Must |
| CRUD de `Reuniao` vinculado ao consultor logado | 2h | Must |
| Endpoint de upload/colagem de `Transcricao` | 2h | Must |
| Tratamento de erros global (`@ControllerAdvice`) | 1h | Should |
| Testes manuais de ponta a ponta via Postman/Swagger | 1h30 | Must |

**Definition of Done:** é possível, via Postman, registrar consultor, logar, criar cliente e reunião, e enviar uma transcrição — tudo persistido no Oracle.

---

## Sprint 2 — Motor de Análise + Refinamento (Semana, 2h/dia)
**Quando:** 07–11/09 — 10h
**Objetivo:** transcrição processada gera insights reais; API documentada e testada.

| Dia | Task | Estimativa | Prioridade |
|---|---|---|---|
| Seg 07/09 | Criar interface `AnaliseStrategy` + implementar `KeywordAnaliseStrategy` (listas de palavras-chave e regex) | 2h | Must |
| Ter 08/09 | Endpoint `POST /transcricoes/{id}/analisar` + `GET /transcricoes/{id}/analise`, persistência da `Analise` | 2h | Must |
| Qua 09/09 | Documentação da API com springdoc-openapi (Swagger UI) | 2h | Should |
| Qui 10/09 | Testes unitários (JUnit/Mockito) para `AuthService` e `KeywordAnaliseStrategy` | 2h | Should |
| Sex 11/09 | Buffer técnico + criação de dados de *seed* (2–3 transcrições de exemplo para a demo) | 2h | Must |

**Definition of Done:** ao enviar uma transcrição de teste, a API retorna pontos de interesse, desinteresse, oportunidades e score de forma consistente; Swagger UI acessível.

---

## Sprint 3 — Frontend + Integração + Polimento (Fim de semana 2)
**Quando:** 12–13/09 — 16h
**Objetivo:** aplicação utilizável de ponta a ponta pela interface, pronta para demo.

### Sábado 12/09 (8h) — Telas base
| Task | Estimativa | Prioridade |
|---|---|---|
| Setup React Router + Axios + `AuthContext` (login/logout, guarda de rotas) | 2h | Must |
| Tela de Login/Registro | 1h30 | Must |
| Tela de listagem de reuniões/transcrições do consultor | 2h | Must |
| Tela/formulário de upload de transcrição | 2h30 | Must |

### Domingo 13/09 (8h) — Resultado da análise + Polimento
| Task | Estimativa | Prioridade |
|---|---|---|
| Tela de resultado da análise (cards de interesse/desinteresse/oportunidades + score) | 3h | Must |
| Dashboard simples com contagem de reuniões/oportunidades | 1h30 | Could |
| Ajustes visuais e responsividade básica | 1h30 | Should |
| Teste end-to-end manual (fluxo completo: login → criar reunião → upload → análise) | 1h | Must |
| Preparar roteiro/slides da apresentação com os dados de seed | 1h | Must |

**Definition of Done:** fluxo completo funciona pela interface, sem depender do Postman, com dados de seed carregados para a demo.

---

## Dia da entrega — 14/09
- **Sem desenvolvimento novo.** Apenas:
  - Ensaio da apresentação;
  - Verificação de que o ambiente (Docker + backend + frontend) sobe do zero sem erro;
  - Buffer para qualquer bug de última hora.

---

## Backlog resumido (User Stories)

| ID | História | Story Points | Prioridade |
|---|---|---|---|
| US01 | Como consultor, quero me cadastrar e logar para acessar minhas reuniões | 5 | Must |
| US02 | Como consultor, quero cadastrar um cliente e uma reunião | 3 | Must |
| US03 | Como consultor, quero enviar a transcrição de uma reunião | 5 | Must |
| US04 | Como consultor, quero que a transcrição seja analisada automaticamente | 8 | Must |
| US05 | Como consultor, quero visualizar os pontos de interesse/desinteresse/oportunidades | 5 | Must |
| US06 | Como consultor, quero listar minhas reuniões e transcrições | 3 | Should |
| US07 | Como consultor, quero um resumo/dashboard das minhas oportunidades identificadas | 3 | Could |
| US08 | Como gestor (admin), quero ver as reuniões de todos os consultores | 5 | Won't (próxima entrega) |

**Total Must:** 26 pontos | **Should:** 6 pontos | **Could:** 3 pontos

---

## Riscos de cronograma (ver também SDD, seção 9)

Se algum sprint atrasar, a ordem de corte é: **US07 → US06 → parte visual do frontend (Should) → nunca o núcleo Must**. O objetivo é sempre ter, na pior das hipóteses, um fluxo Postman-only funcionando até o dia 11/09, garantindo uma demo (ainda que sem UI polida) para o dia 14.