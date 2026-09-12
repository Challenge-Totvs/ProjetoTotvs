# Planejamento Ágil — InsightCall

**Metodologia:** Scrum adaptado para equipe de 2 pessoas, com checkpoints de aprendizado
**Equipe:** Kelwin (backend Java, integração e frontend) + João (serviço de análise em Python)
**Início real do projeto:** 04/09/2026 | **Nova entrega/apresentação:** 15/10/2026
**Capacidade estimada:** ~39 dias corridos, disponibilidade parecida com o início (fins de semana cheios + ~2h nos dias de semana)

## O que mudou em relação ao plano original

O prazo original (14/09) foi adiado para **15/10/2026** — quase 4x mais tempo. Isso muda o objetivo do plano: em vez de "sobreviver ao prazo apertado" (que era o foco do plano anterior, cortando tudo que não fosse essencial), agora o objetivo é **usar o tempo extra pra consolidar aprendizado de verdade**, com folga real pra imprevistos, revisão de código e reforço nos pontos onde você mais travou (Spring Security e JWT).

### Mudança de arquitetura: motor de análise em Python

A equipe decidiu implementar o motor de análise em **Python (FastAPI)**, como um serviço REST independente, em vez de dentro do backend Java. O backend continua sendo o dono do banco e da regra de negócio: ele chama o serviço Python, recebe os insights e **persiste** o resultado.

**Consequências para o planejamento:**
- A Fase 2 passa a ter **duas frentes paralelas** (Python e integração Java), com um passo de alinhamento obrigatório antes;
- O projeto deixa de ser individual: a divisão de responsabilidades está no README (seção 8);
- Surge um novo risco a gerenciar — a integração entre os serviços (ver SDD, seção 9).

Três mudanças estruturais em relação ao plano original:
1. **Checkpoints de aprendizado** ao final de cada fase — uma pausa pra revisar/testar o que foi realmente internalizado (via quiz e perguntas de "explique de volta"), antes de seguir pra próxima fase.
2. **Motor de análise em Python**, como serviço separado, com trabalho paralelizado entre os dois integrantes;
3. **Semana de buffer/polimento** inteira antes da reta final — não existia no plano original por falta de tempo; agora dá pra usar pra revisitar código, considerar melhorias que antes eram "Won't", e reforçar o que os checkpoints apontarem como fraco.

## Progresso já feito (Sprint 0 + parte do Sprint 1)

✅ Setup do ambiente (repositório, Oracle da faculdade, esqueleto Spring Boot/React)
✅ 5 entidades JPA (Consultor, Cliente, Reunião, Transcrição, Análise)
✅ Spring Security 6 configurado (SecurityFilterChain, PasswordEncoder, AuthenticationProvider)
✅ JWT completo (JwtProvider + JwtAuthFilter, plugado no SecurityConfig)

---

## FASE 1 — Concluir o Backend Core
**Período:** 06/09 (dom) a 13/09 (dom) — ~1 semana
**Objetivo:** fechar o que faltou do Sprint 1 original: autenticação exposta via endpoint, CRUDs, upload de transcrição.

| Task | Prioridade |
|---|---|
| Endpoints de registro e login (/api/auth/register, /api/auth/login) | Must |
| Teste manual do fluxo completo de login (Postman) | Must |
| CRUD de Cliente | Must |
| CRUD de Reunião vinculado ao consultor logado | Must |
| Endpoint de upload/colagem de Transcrição | Must |
| Tratamento de erros global (@ControllerAdvice) | Should |
| Testes manuais de ponta a ponta (Postman/Swagger) | Must |

**🎓 Checkpoint de aprendizado #1 (por volta de 13-14/09):** revisão de JPA (relacionamentos, fetch types), Spring Security (filter chain, UserDetails) e JWT (geração/validação, filtro). Formato: quiz rápido + 2-3 perguntas de "explique por que isso funciona assim" sobre decisões que você tomou nesta fase.

---

## FASE 2 — Motor de Análise (Python) + Integração
**Período:** 14/09 (seg) a 20/09 (dom)
**Objetivo:** ter o serviço Python analisando transcrições e o backend Java consumindo ele de ponta a ponta.

> 🔀 **Esta fase muda de natureza:** com a decisão de fazer o motor em Python, a Fase 2 passa a ter **duas frentes paralelas**. Isso é o que torna o trabalho em dupla vantajoso — mas exige um passo de alinhamento antes de qualquer código.

### Passo 0 — Alinhamento (fazer JUNTOS, antes de tudo)
| Task | Responsável |
|---|---|
| Fechar o contrato da API entre os serviços (SDD, seção 7.2): formato do request, do response e dos erros | **Ambos** |
| Definir portas, variáveis de ambiente e como cada um roda o serviço do outro localmente | **Ambos** |
| Criar a pasta `analise-service/` no repositório com a estrutura base e o `requirements.txt` | **Ambos** |

**Por que isso vem primeiro:** com o contrato fechado, cada frente consegue trabalhar com um *mock* do outro lado, sem ficar bloqueada esperando. Sem isso, uma frente trava a outra.

### Frente A — Serviço Python (João)
| Task | Prioridade |
|---|---|
| Setup do FastAPI: venv, `requirements.txt`, `main.py` subindo com `/docs` acessível | Must |
| Modelos Pydantic (`schemas.py`) conforme o contrato acordado | Must |
| Engine: listas de palavras-chave por categoria (`engine/keywords.py`) | Must |
| Engine: extração via regex de valores, prazos e entidades (`engine/extractor.py`) | Must |
| Engine: cálculo do score de engajamento (`engine/scorer.py`) | Must |
| Endpoint `POST /analisar` ligando tudo (`router.py`) | Must |
| Testes com pytest (engine + endpoint, casos de sucesso e texto vazio) | Should |

### Frente B — Integração no backend Java (Kelwin)
| Task | Prioridade |
|---|---|
| Configurar `RestClient` em `config/` com `ANALISE_SERVICE_URL` e timeout via variável de ambiente | Must |
| Implementar `AnaliseServiceClientStrategy` (implementa a `AnaliseStrategy` já existente) | Must |
| `AnaliseService`: buscar transcrição, checar ownership, chamar o Python, persistir a `Analise` | Must |
| Endpoints `POST /api/transcricoes/{id}/analisar` e `GET /api/transcricoes/{id}/analise` | Must |
| Tratar falhas de comunicação (timeout, 5xx, serviço fora do ar) conforme RNF06 | Must |
| Documentação da API com springdoc-openapi (Swagger) | Should |
| Testes unitários com o serviço Python mockado | Should |

### Fechamento da fase (JUNTOS)
| Task | Prioridade |
|---|---|
| Teste de integração real: os dois serviços no ar, fluxo completo até persistir no Oracle | Must |
| Dados de *seed*: 2–3 transcrições de exemplo que gerem análises coerentes para a demo | Must |

**🎓 Checkpoint de aprendizado #2 (por volta de 20-21/09):** revisão de Design Patterns (por que a Strategy permitiu trocar o motor sem tocar no resto do sistema), comunicação entre serviços via HTTP, e tratamento de falhas de integração. Bônus: FastAPI/Pydantic vs. Spring/Bean Validation — o que os dois têm em comum conceitualmente?

---

## FASE 3 — Frontend Base
**Período:** 21/09 (seg) a 27/09 (dom)
**Objetivo:** ter a aplicação React funcionando com autenticação e as telas de fluxo principal.

| Task | Prioridade |
|---|---|
| Setup React Router + Axios + AuthContext | Must |
| Tela de Login/Registro | Must |
| Tela de listagem de reuniões/transcrições do consultor | Must |
| Tela/formulário de upload de transcrição | Must |

**🎓 Checkpoint de aprendizado #3 (por volta de 27-28/09):** revisão de React Router, Context API e como o token JWT viaja do frontend pro backend (interceptors do Axios).

---

## FASE 4 — Frontend Completo
**Período:** 28/09 (seg) a 04/10 (dom)
**Objetivo:** fechar a experiência de ponta a ponta.

| Task | Prioridade |
|---|---|
| Tela de resultado da análise (interesse/desinteresse/oportunidades/score) | Must |
| Dashboard simples (contagem de reuniões/oportunidades) | Should (antes era Could — o tempo extra permite promover) |
| Ajustes visuais e responsividade básica | Should |
| Teste end-to-end manual (fluxo completo pela UI) | Must |

**🎓 Checkpoint de aprendizado #4 (por volta de 04-05/10):** revisão geral de ponta a ponta — consegue explicar o fluxo completo (request → filtro JWT → controller → service → repository → banco → resposta) sem olhar o código?

---

## FASE 5 — Buffer, Polimento e Stretch Goals
**Período:** 05/10 (seg) a 11/10 (dom)
**Objetivo:** essa fase não existia no plano original. Use pra reforçar o que os checkpoints apontarem como fraco, e opcionalmente avançar itens que antes eram "Won't".

**Stretch goals opcionais (só se sobrar tempo e energia, nessa ordem de prioridade):**

| Item | Por que vale considerar agora |
|---|---|
| Migrar de `ddl-auto=update` pra Flyway migrations | Você já tem experiência com Flyway de outros projetos — com mais tempo, é uma boa prática real pra mostrar na apresentação |
| **Docker Compose para subir os dois serviços juntos** | Com dois runtimes, subir tudo com um comando reduz bastante o risco na hora da apresentação |
| **Enriquecer o motor Python** (lematização, stopwords PT-BR, ou spaCy) | Frente natural de evolução agora que o motor está isolado — melhora a qualidade dos insights sem tocar no Java |
| RF09 — papel ADMIN vendo reuniões de todos os consultores | Estava marcado "Won't" só por causa do prazo; a base de Security já suporta isso (é adicionar uma authority + regra no SecurityFilterChain) |
| Testes automatizados mais abrangentes (Service layer completo) | Antes só cobria Auth e a Strategy; com tempo, dá pra cobrir os CRUDs também |
| Revisão de código geral | Reler o próprio código das Fases 1-4 com olhar crítico, sem pressa — costuma revelar entendimentos que ficaram rasos |

**Não é obrigatório fazer nada disso.** Se você preferir só descansar mais e manter o escopo do MVP original, está ótimo — o objetivo desta fase é dar folga, não empilhar trabalho novo.

---

## FASE 6 — Reta Final e Apresentação
**Período:** 12/10 (seg, feriado de N. Sra. Aparecida) a 15/10 (qui, entrega)
**Objetivo:** preparar a apresentação com calma, sem pressa de última hora.

| Task | Prioridade |
|---|---|
| Preparar roteiro/slides da apresentação | Must |
| Ensaiar a apresentação (roteiro + demo ao vivo) | Must |
| Verificar que o ambiente sobe do zero sem erro (Oracle da faculdade + backend Java + **serviço Python** + frontend) | Must |
| Ensaiar o plano B caso o serviço Python falhe na hora (prints/vídeo do fluxo de análise gravado) | Should |
| Confirmar que o servidor Oracle da faculdade está acessível no horário da apresentação | Must |
| Buffer para qualquer bug de última hora | Must |

---

## Backlog de User Stories (atualizado)

| ID | História | Prioridade atual |
|---|---|---|
| US01 | Como consultor, quero me cadastrar e logar para acessar minhas reuniões | Must |
| US02 | Como consultor, quero cadastrar um cliente e uma reunião | Must |
| US03 | Como consultor, quero enviar a transcrição de uma reunião | Must |
| US04 | Como consultor, quero que a transcrição seja analisada automaticamente | Must |
| US05 | Como consultor, quero visualizar os pontos de interesse/desinteresse/oportunidades | Must |
| US06 | Como consultor, quero listar minhas reuniões e transcrições | Should |
| US07 | Como consultor, quero um resumo/dashboard das minhas oportunidades identificadas | Should (promovido de Could) |
| US08 | Como gestor (admin), quero ver as reuniões de todos os consultores | Could (promovido de Won't — vira stretch goal da Fase 5) |

---

## Metodologia de aprendizado (novidade deste plano)

Com o prazo mais folgado, a forma de trabalhar também muda:

1. **Tentativa antes de solução**, inclusive em bibliotecas novas — antes, sob pressão, às vezes a resposta vinha pronta; agora o padrão é você tentar primeiro, sempre.
2. **Debug guiado, não resolvido de cara** — ao encontrar um erro, a conversa parte de "qual sua hipótese?" antes de apontar a causa.
3. **Previsão antes da explicação** — antes de explicar o que um trecho de código faz, a pergunta "o que você acha que acontece?" vem primeiro.
4. **Checkpoints de revisão entre fases** (marcados acima) — quiz rápido + perguntas de "explique de volta", pra identificar o que ficou raso vs. o que ficou sólido.
5. **Sem pressa artificial** — as explicações podem ser mais devagar, com mais perguntas no meio, já que o tempo não é mais o fator limitante.

## Regra de ouro (atualizada)

Com o prazo folgado, a regra de corte de escopo muda: **nada precisa ser cortado por padrão**. Se algum imprevisto real acontecer (problema de saúde, imprevisto na faculdade/estágio, servidor Oracle instável por dias), a ordem de corte continua sendo US08 → US07 → US06 → itens "Should" do frontend — mas a expectativa agora é entregar o escopo completo com folga, não just o mínimo viável.