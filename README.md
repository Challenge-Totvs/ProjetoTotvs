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
- **Motor de análise em Python**, exposto como serviço REST independente. Usa **LLM como motor principal** (com uma segunda LLM de outro provedor como fallback), gerando insights ancorados em evidência da própria transcrição, score de engajamento e uma recomendação de próximos passos; um motor de regex é mantido como último recurso caso as duas LLMs falhem;
- Tela com o resultado da análise (interesse, desinteresse, oportunidades, score, recomendação);
- Listagem de reuniões/transcrições por consultor.

**Fora do escopo (próximas versões):**
- Captura automática de áudio/transcrição em tempo real (assume-se que a transcrição já chega pronta, gerada por outra ferramenta);
- Modelo de Machine Learning supervisionado próprio (ver SDD, seção 8) — o dataset disponível não possui rótulo/avaliação, então essa via fica documentada como roadmap;
- Notificações por e-mail, dashboard analítico avançado, app mobile.

## 3. Stack técnica

O projeto é composto por **três aplicações independentes**:

| Aplicação | Camada | Tecnologia |
|---|---|---|
| `backend/` | API principal | Java 17+ / Spring Boot 3 |
| | Persistência | Spring Data JPA + Oracle (servidor da faculdade) |
| | Autenticação | Spring Security 6 + JWT |
| | Documentação de API | springdoc-openapi (Swagger UI) |
| | Testes | JUnit 5 + Mockito |
| `analise-service/` | Motor de análise | Python 3.11+ / FastAPI |
| | Validação | Pydantic |
| | Documentação de API | OpenAPI automático (nativo do FastAPI) |
| | Testes | pytest |
| `frontend/` | Interface | React (Vite) + Axios + React Router |

## 4. Arquitetura (resumo)

O sistema usa uma arquitetura de **dois serviços**: o backend Java orquestra tudo (autenticação, CRUDs, persistência) e delega **apenas o processamento de texto** para um serviço Python especializado.

```
                                    ┌──────────────────────────┐
                                    │  analise-service         │
                                    │  (Python / FastAPI)      │
                                    │  stateless, sem banco    │
                                    └──────────▲───────────────┘
                                               │ HTTP (JSON)
                                               │ texto → insights
React (SPA) ──► REST API (Spring Boot) ──► AnaliseService ──┘
                        ▲                        │
                 JWT Filter                      ▼
              (Spring Security)          Repository (Spring Data) ──► Oracle
```

**Divisão de responsabilidades:**
- **Java** é o dono do banco e da regra de negócio: autentica, valida permissões, busca a transcrição, chama o Python, e **persiste** o resultado na entidade `Analise`.
- **Python** é stateless: recebe um texto, devolve os insights em JSON. Não conhece o banco, não conhece usuários, não guarda estado.

Detalhes completos, contrato da API entre os serviços, modelo de dados e diagramas estão no **SDD.md**.

## 5. Como rodar o projeto

### Pré-requisitos
- JDK 17+
- Node.js 18+
- Maven
- **Python 3.11+** (para o serviço de análise)
- Acesso ao servidor Oracle da faculdade (host, porta, service name, usuário e senha fornecidos pela instituição — solicitar com antecedência)

> ⚠️ **Ordem de inicialização:** o `analise-service` (Python) precisa estar no ar **antes** de você disparar qualquer análise pelo backend. As demais funcionalidades (login, CRUDs, upload de transcrição) funcionam normalmente mesmo com o serviço Python desligado.

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

### 5.3 Serviço de análise (Python)

```bash
cd analise-service
python -m venv .venv

# Linux/macOS:
source .venv/bin/activate
# Windows (Git Bash):
source .venv/Scripts/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

O serviço sobe em `http://localhost:8000`. Documentação interativa (gerada automaticamente pelo FastAPI) em `http://localhost:8000/docs`.

> A pasta `.venv/` deve estar no `.gitignore` — nunca versione o ambiente virtual.

### 5.4 Frontend

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
| `ANALISE_SERVICE_URL` | URL base do serviço Python (ex: `http://localhost:8000`) |
| `ANALISE_SERVICE_TIMEOUT_MS` | Timeout da chamada ao serviço de análise. Generoso por causa do tamanho das transcrições (dataset chega a ~200 mil caracteres) — ex: 120000 (2 min) |
| `ANALISE_LLM_PRINCIPAL` / `ANALISE_LLM_SECUNDARIA` | Provedor e credencial de cada LLM na cadeia de fallback (definidos no `analise-service`, não no Java) |

## 7. Estrutura de pastas

```
ProjetoTotvs/
├── backend/
│   └── src/main/java/com/challengetotvs/api/
│       ├── config/               # SecurityConfig, CORS, OpenAPI, RestClient
│       ├── domain/
│       │   ├── consultor/        # Consultor, ConsultorRepository, AuthService,
│       │   │                     # RegisterRequest, LoginRequest, AuthResponse
│       │   ├── cliente/          # Cliente, ClienteRepository, DTOs, Service, Controller
│       │   ├── reuniao/          # Reuniao, StatusReuniao, Repository, DTOs, Service, Controller
│       │   ├── transcricao/      # Transcricao, Repository, DTOs, Service, Controller
│       │   └── analise/          # Analise, Repository, AnaliseService,
│       │                         # AnaliseStrategy + AnaliseServiceClientStrategy (HTTP)
│       ├── security/             # JwtProvider, JwtAuthFilter, ConsultorUserDetails, ConsultorDetailsService
│       └── exception/            # Handler global de erros (@ControllerAdvice)
├── analise-service/
│   ├── app/
│   │   ├── main.py               # instancia o FastAPI e registra as rotas
│   │   ├── schemas.py            # modelos Pydantic (contrato de entrada/saída)
│   │   ├── router.py             # endpoint POST /analisar
│   │   ├── orchestrator.py       # cadeia de fallback: LLM principal -> LLM secundária -> regex
│   │   └── engines/
│   │       ├── llm_engine.py     # motor via LLM (parametrizável por provedor - usado 2x)
│   │       └── regex_engine.py   # motor de regex, mantido como último recurso
│   │           # (keywords.py, extractor.py, scorer.py dentro deste módulo)
│   ├── tests/                    # pytest
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   └── src/
│       ├── pages/
│       ├── components/
│       ├── services/             # chamadas axios
│       └── context/              # AuthContext
├── docs/
│   ├── SDD.md
│   └── PLANEJAMENTO_SPRINTS.md
└── README.md
```

### Decisão arquitetural: package-by-feature em vez de package-by-layer

O backend organiza o código **por domínio** (`domain.consultor`, `domain.cliente`, `domain.reuniao`...), em vez de por camada técnica (`controller/`, `service/`, `dto/`, `repository/` genéricos na raiz).

**Motivo:** manter cada domínio coeso — entidade, repositório, DTOs, service e controller de um mesmo recurso ficam juntos, no mesmo pacote. Isso evita que pastas genéricas (como `dto/` ou `service/`) virem uma "gaveta" acumulando classes de features completamente diferentes conforme o projeto cresce, sem nenhuma relação entre elas além de estarem na mesma camada técnica.

Exceções propositais a essa regra: `security/` fica fora do `domain` porque é infraestrutura transversal (autenticação), não uma regra de negócio de um domínio específico; `config/` e `exception/` seguem a mesma lógica, por serem configuração/tratamento cross-cutting, não específicos de um recurso.

## 8. Equipe

| Integrante | Responsabilidade principal |
|---|---|
| Kelwin Silva Bastos | Backend Java (API, autenticação, CRUDs, persistência), integração com o serviço de análise e frontend React |
| João Paulo Basta | Serviço de análise em Python (FastAPI): motor de processamento de texto, extração de insights e score |

> ⚠️ **Preencher o nome do segundo integrante.** O contrato da API entre os dois serviços (seção 7 do SDD) é o ponto de acordo entre as duas frentes — deve ser definido em conjunto **antes** de cada um começar a desenvolver o seu lado, para permitir trabalho em paralelo sem bloqueio.

## 9. Roadmap futuro

- Treinar um modelo de Machine Learning supervisionado próprio, uma vez que exista um conjunto de dados rotulado (ver SDD, seção 8) — reduziria custo por análise em relação a depender de LLMs em nuvem;
- Modelo local (ex: Ollama) substituindo uma ou ambas as LLMs em nuvem, caso a confidencialidade dos dados do cliente se torne um requisito de produção;
- Dividir transcrições muito grandes em partes processadas em paralelo, se a medição de latência mostrar necessidade (ver SDD, seção 7.5);
- Containerizar os dois serviços (Docker Compose) para simplificar a subida do ambiente completo;
- Processamento assíncrono de análises longas (fila/eventos);
- Dashboard consolidado por gestor com métricas de todos os consultores;
- Exportação de relatório em PDF por reunião.