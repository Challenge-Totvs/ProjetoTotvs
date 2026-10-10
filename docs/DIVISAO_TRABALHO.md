# InsightCall — Divisão de trabalho até a banca e a entrega

**Data:** 09/10/2026
**Base:** `docs/SDD.md` v3.0 e `docs/HANDOFF_INTERFACE.md`
**Datas:** banca TOTVS na **quarta, 14/10** · entrega final FIAP na **quarta, 21/10**

## 1. Quem cuida de quê

| Frente | Dono | Apoio |
|---|---|---|
| **Java** (backend, banco, regras dos temas, carga inicial) | Kelwin | — |
| **Python** (analise-service: contrato v3, cadeia de motores, conferência das citações) | Parceiro do analise-service | Kelwin nos testes de integração |
| **Frontend** (portar a demo para o projeto React e ligar na API) | Kelwin | Quem escreveu a demo, para tirar dúvidas do código |

Ajustem os nomes se a divisão de vocês for outra. O que importa é que **cada tarefa tenha um dono só**.

## 2. Antes de qualquer código (sexta à noite, 09/10)

Estas quatro decisões destravam o resto. Sem elas, Java e Python vão codar contra contratos diferentes.

| # | Decisão | Proposta do SDD | Quem decide |
|---|---|---|---|
| D1 | Contrato v3 do `POST /analisar` | SDD, seção 6.2 | Kelwin e o parceiro do Python, juntos |
| D2 | Chaves de API das LLMs (quem paga e quanto) | Sem chave, a banca roda com a carga inicial e a resposta de exemplo gravada | Equipe |
| D3 | Pseudonimização no Java e conferência das citações no Python | SDD, seção 3.3 | Kelwin e o parceiro do Python |
| D4 | Transcrição sem `[LOCUTOR n]` | Recusar com 422 na banca | Kelwin |

**Entregável da sexta:** o parceiro do Python publica um **mock** do contrato v3: um `POST /analisar` que devolve sempre a resposta da transcrição de exemplo (Hospital Santa Luzia, seção 11.2 do handoff). Com isso, o Java e o frontend avançam sem esperar a LLM.

## 3. Tarefas da banca (14/10)

Tamanho: **P** até meio período · **M** um período inteiro · **G** mais de um período.

### Java (Kelwin)

| ID | Tarefa | Tam. | Depende de | Pronto quando |
|---|---|---|---|---|
| J1 | Perfil (`VENDEDOR`, `GESTOR`) no `Consultor` e no JWT; login devolve `{ token, expiraEm, usuario }`; `GET /api/me` | P | — | Login no Postman devolve o usuário com perfil |
| J2 | Erros no formato `{ codigo, mensagem }` no `GlobalExceptionHandler`; 404 para recurso de outro vendedor | P | — | 503, 404, 409 e 422 respondem nesse formato |
| J3 | `Cliente` (nome = empresa, tipo, segmento, vendedor dono) e `Contato`; `POST` e `GET` de clientes | M | J1 | Criar cliente com contato e listá-lo |
| J4 | `Reuniao` com status, duração, contato e `confirmada` | P | J3 | Criar reunião realizada e agendada |
| J5 | `LeitorTurnos` (regra 5.2), limites de tamanho e hash contra duplicata no envio da transcrição | M | J4 | Testes do `LeitorTurnos` passando; duplicata devolve 409 |
| J6 | Entidades `Padrao` (com os 14), `Tema`, `Citacao`, `EventoTema` e repositórios | M | J3 | Tabelas criadas e padrões carregados |
| J7 | `CalculadoraSituacao` com os **32 casos** do handoff em JUnit | M | J6 | Os 32 testes passando |
| J8 | `Pseudonimizador` (nomes do cadastro) e DTOs do contrato v3 | M | D1, D3 | Teste com "Helena Prado" e "Helena" |
| J9 | Novo `AnaliseService`: monta o pedido v3, chama o Python, traduz as citações de volta, grava a análise e chama o `IncorporadorTemas` | G | J5, J6, J8, mock do Python | `POST /analisar` com o mock cria os temas no cliente |
| J10 | `GET /api/clientes/{id}` e `GET /api/reunioes/{id}` (com turnos e versão "como a LLM recebeu") | M | J7, J9 | JSON igual ao exemplo do handoff (10.8) |
| J11 | `GET /api/inicio` (riscos, oportunidades, mudanças, agenda, desempenho) | M | J7 | Início devolve as listas já ordenadas |
| J12 | `POST` e `DELETE` de "tratei fora" e "não procede" | M | J7 | Situação muda e desfazer volta ao anterior |
| J13 | `GET /api/motores/status` (repassa o `/health`) | P | Python P5 | Banner sabe quando a LLM principal caiu |
| J14 | **Carga inicial** com os dados da demo (perfil `demo`, datas relativas) | G | J3 a J12 | Roteiro da banca roda com o banco recém-criado |

### Python (parceiro)

| ID | Tarefa | Tam. | Depende de | Pronto quando |
|---|---|---|---|---|
| P0 | Mock do contrato v3 (resposta fixa da transcrição de exemplo) | P | D1 | Java consegue chamar e receber o JSON |
| P1 | Schemas Pydantic do contrato v3 (pedido e resposta) | P | D1 | Pedido inválido devolve 422 |
| P2 | Prompt da LLM: padrão da lista, trecho literal, `tratado`, papéis, compromissos com regra, resumo, próximos passos e curva de sentimento | G | P1 | Transcrição de exemplo devolve os temas esperados |
| P3 | Conferência das citações (normalização, vizinhos ±2, trecho entre turnos, descartados) | M | P1 | Testes da seção 12 do SDD passando |
| P4 | Regras por padrão de volta na cadeia; modelo local contribuindo com score e interesse | M | P1 | Com as LLMs fora, a resposta sai com temas e `motor = regras` ou `local` |
| P5 | `/health` com o estado de cada motor; `motor` e `tentativas` na resposta | P | P1 | `/health` lista os quatro motores |
| P6 | Testes do orquestrador (cenários 2 a 4) e do contrato | M | P2 a P5 | Suíte do pytest passando |

### Frontend (Kelwin)

| ID | Tarefa | Tam. | Depende de | Pronto quando |
|---|---|---|---|---|
| F1 | Portar a demo: `allowJs` no `tsconfig`, `lucide-react`, CSS da demo em `styles/app.css`, componentes em `src/demo/` | M | — | A demo roda dentro do projeto, ainda com os dados fixos |
| F2 | Login e cadastro da demo ligados ao `AuthContext` e ao `/api/me`; cada perfil cai na sua tela inicial | P | J1, F1 | Entrar como vendedor leva ao Início |
| F3 | Camada `api/` (clientes, reuniões, transcrições, temas, início, motores) e tipos dos DTOs | M | J10, J11 | Chamadas tipadas funcionando |
| F4 | Início, Clientes e página do Cliente com dados da API | G | F3 | Passos 1 a 3 do roteiro funcionam |
| F5 | Página da Reunião e Nova transcrição (com a tela de andamento) | G | F3, J9 | Passos 4 e 5 do roteiro funcionam |
| F6 | Ações no tema (tratei fora, não procede) com desfazer | M | J12, F4 | Ação muda a situação na tela |

## 4. Calendário

A máquina com Java fica disponível só em parte do dia. Por isso, Python e frontend ocupam os outros horários.

| Dia | Java | Python | Frontend |
|---|---|---|---|
| **Sex 09/10, noite** | D1 a D4 | D1, P0 | — |
| **Sáb 10/10** | J1, J2, J3, J4, J6 | P1, P2 | F1 |
| **Dom 11/10** | J5, J7, J8, J9 | P2, P3, P4 | F2, F3 |
| **Seg 12/10** | J10, J11, J12, J13 | P5, P6; troca do mock pela cadeia real | F4, F5 |
| **Ter 13/10** | J14 (carga inicial); **congelar o código ao meio-dia** | Testes de integração | F6; **ensaio completo à tarde** na máquina da apresentação |
| **Qua 14/10** | **Banca** | | |

**Corte de emergência:** se na segunda à noite o fluxo ponta a ponta não estiver funcionando, a banca usa a carga inicial e a resposta gravada da transcrição de exemplo, e a análise ao vivo vira um passo opcional do roteiro.

## 5. Até a entrega (21/10)

| ID | Tarefa | Frente | Tam. |
|---|---|---|---|
| E1 | Compromissos: `PrazoPorRegra`, estados, marcar cumprido (com testes da tabela 8.10) | Java + Front | M |
| E2 | Telas do gestor: clientes com facetas, Padrões, Vendedores e visão do vendedor (só leitura) | Java + Front | G |
| E3 | "Avisar gestor" e sino de notificações | Java + Front | M |
| E4 | Janela configurável com prévia do impacto | Java + Front | M |
| E5 | Cadastro por domínio e convites | Java + Front | M |
| E6 | Contraexemplos ("não procede") no pedido à LLM | Java + Python | P |
| E7 | Régua da conversa, curva de sentimento e métricas por papel | Front | M |
| E8 | Reconhecimento automático de entidades (spaCy) na pseudonimização | Python ou Java | M |
| E9 | Atualizar README, SDD e Trello com o estado final | Kelwin | P |

Para depois da entrega: análise assíncrona, reprocessamento, semelhança com "não procede", integração com o RD Station e as demais ideias do handoff (seção 14).

## 6. Como cada tarefa vai ser feita

- Cada tarefa é pedida pelo ID (por exemplo, "vamos fazer a J7"). O código vem pronto, com a explicação de cada parte, para revisar, rodar e entender antes de commitar.
- Um commit por tarefa, com o ID na mensagem: `feat(J7): add CalculadoraSituacao with handoff test cases`.
- Toda tarefa fecha com o critério "pronto quando" da tabela atendido, testado no Postman ou no pytest.
- O Trello ganha um card por ID, com a fase (banca ou entrega).
