# InsightCall — Plataforma de Transcrições e Análise de Reuniões

> Projeto acadêmico — FIAP — Challenge TOTVS 2026
> Entrega/apresentação: **14/09/2026**

## 1. Sobre o projeto

O **InsightCall** é uma aplicação web que centraliza as transcrições das reuniões dos consultores com clientes, organiza esse conteúdo por consultor e aplica uma análise automática sobre o texto para extrair:

- **Pontos de interesse** do cliente durante a conversa;
- **Pontos de desinteresse** ou objeções;
- **Oportunidades de venda** (upsell, cross-sell, renovação, novos módulos);
- Um **score de engajamento** geral da reunião.

O objetivo é dar ao consultor (e ao gestor comercial) uma visão rápida do que realmente importou na conversa, sem precisar reler a transcrição inteira.

## 2. Escopo desta entrega (MVP)

Dado o prazo (10 dias) e o time reduzido, esta primeira entrega cobre:

**Incluso:**
- Cadastro/login de consultores com autenticação JWT;
- Upload de transcrição (texto colado ou arquivo `.txt`) vinculada a um consultor e a uma reunião/cliente;
- Motor de análise baseado em regras (palavras-chave + regex), com arquitetura pronta para trocar por um modelo de NLP/LLM no futuro;
- Tela com o resultado da análise (interesse, desinteresse, oportunidades, score);
- Listagem de reuniões/transcrições por consultor.

**Fora do escopo (próximas versões):**
- Captura automática de áudio/transcrição em tempo real (assume-se que a transcrição já chega pronta, gerada por outra ferramenta);
- Análise via modelo de linguagem (LLM) — hoje é rule-based;
- Notificações por e-mail, dashboard analítico avançado, app mobile.

## 3. Stack técnica

| Camada | Tecnologia |
|---|---|
| Backend | Java 17+ / Spring Boot 3 |
| Persistência | Spring Data JPA + Oracle Database (XE via Docker) |
| Autenticação | Spring Security 6 + JWT |
| Frontend | React (Vite) + Axios + React Router |
| Documentação de API | springdoc-openapi (Swagger UI) |
| Testes | JUnit 5 + Mockito |

## 4. Arquitetura (resumo)

Arquitetura em camadas clássica, monolito modular:

```
React (SPA)  →  REST API (Spring Boot)  →  Service Layer  →  Repository (Spring Data)  →  Oracle
                        ↑
                 JWT Filter (Spring Security)
```

Detalhes completos, modelo de dados e diagramas estão no **SDD.md**.

## 5. Como rodar o projeto

### Pré-requisitos
- JDK 17+
- Node.js 18+
- Maven
- Acesso ao servidor Oracle da faculdade (host, porta, service name, usuário e senha fornecidos pela instituição — solicitar com antecedência)

### 5.1 Banco de dados (servidor Oracle da faculdade)

O projeto **não sobe um Oracle local**: ele se conecta diretamente ao servidor Oracle disponibilizado pela faculdade. Antes de rodar o backend:

1. Confirmar com a faculdade/TI o host, porta, *service name* (ou SID) e as credenciais de acesso;
2. Verificar se é necessário estar na rede da faculdade ou conectado via VPN para acessar o servidor remotamente;
3. Preencher essas informações nas variáveis de ambiente (seção 6) antes de subir o backend.

> ⚠️ Como esse servidor está fora do seu controle, valide o acesso (conexão via SQL Developer/DBeaver) o quanto antes — idealmente antes do Sprint 0 — para não perder tempo de desenvolvimento caso haja bloqueio de rede, credencial pendente ou instabilidade do servidor.

### 5.2 Backend

```bash
cd backend
# configure src/main/resources/application.yml com usuário/senha/URL do Oracle e o segredo JWT
mvn clean install
mvn spring-boot:run
```

A API sobe em `http://localhost:8080`. Documentação Swagger em `http://localhost:8080/swagger-ui.html`.

### 5.3 Frontend

```bash
cd frontend
npm install
npm run dev
```

Aplicação disponível em `http://localhost:5173`.

## 6. Variáveis de ambiente (backend)

| Variável | Descrição |
|---|---|
| `SPRING_DATASOURCE_URL` | URL JDBC do servidor Oracle da faculdade (ex: `jdbc:oracle:thin:@host:porta:serviceName`) |
| `SPRING_DATASOURCE_USERNAME` / `PASSWORD` | Credenciais fornecidas pela faculdade |
| `JWT_SECRET` | Chave usada para assinar os tokens |
| `JWT_EXPIRATION_MS` | Tempo de expiração do token (ex: 3600000) |

## 7. Estrutura de pastas (sugerida)

```
insightcall/
├── backend/
│   └── src/main/java/com/insightcall/
│       ├── config/          # Security, CORS, OpenAPI
│       ├── controller/
│       ├── dto/
│       ├── entity/
│       ├── repository/
│       ├── service/
│       │   └── analise/     # Strategy do motor de análise
│       ├── security/        # JWT provider/filter
│       └── exception/       # Handler global de erros
├── frontend/
│   └── src/
│       ├── pages/
│       ├── components/
│       ├── services/        # chamadas axios
│       └── context/         # AuthContext
├── docs/
│   ├── SDD.md
│   └── PLANEJAMENTO_SPRINTS.md
└── README.md
```

## 8. Equipe

- Kelwin Silva Bastos — responsável por este módulo (backend, motor de análise e frontend)
- *(demais integrantes do grupo — preencher conforme divisão de tarefas do Challenge TOTVS)*

## 9. Roadmap futuro

- Trocar o motor de análise rule-based por um modelo de NLP/LLM real;
- Processamento assíncrono de análises longas (fila/eventos);
- Dashboard consolidado por gestor com métricas de todos os consultores;
- Exportação de relatório em PDF por reunião.