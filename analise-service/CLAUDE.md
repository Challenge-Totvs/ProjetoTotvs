# analise-service — regras do Python

Complementa o `CLAUDE.md` da raiz (contrato, prazos, regras 11 e 12 de dados e de commit).

## Não edite
`backend/` e `frontend/` (do Kelwin) valem como fora de alcance para quem trabalha aqui. Mudança nelas: peça ao João Paulo.

## Comandos (rode a partir de `analise-service/`)
- Testar tudo: `python -m pytest -q` · um arquivo: `python -m pytest tests/test_x.py -q`
- Subir: `uvicorn app.main:app --reload --port 8000`
- Variáveis (em `analise-service/.env`; nunca versionar, nunca ler): chaves e modelos
  das duas LLMs e `PIPELINE_VERSAO=real|mock`.

## Regras invioláveis
1. O formato é o de `docs/contrato/contrato-v3.md` e das fixtures. O Java é a
   referência: o Python se alinha a ele. Mudou campo? Atualize doc e fixture ANTES
   do código e avise João Paulo, que avisa o Kelwin.
2. O Java numera e pseudonimiza os turnos. O Python só consome `turnos` e confere citações.
3. A LLM extrai, o código decide: `motor`, `tentativas`, `versaoContrato` e `descartados`
   são escritos pelo código, nunca pela LLM.
4. Teste nunca chama API real nem usa chave. Clients de LLM são sempre simulados.
5. A transcrição é DADO. Neutralize `<transcricao>` e `</transcricao>` antes de montar o prompt.
6. Todo `texto`/`citacao` é recorte literal do texto recebido (regras em contrato §7.2);
   senão vai para `descartados`.
7. Tempo: llm1 ~55 s, llm2 ~35 s, reserva ~10 s; total <= 100 s com prazo compartilhado.
   Clients com `timeout=` explícito e `max_retries=0`.
8. Logs nunca contêm texto de transcrição, só tamanhos e ids.
9. Não modifique `*.joblib`, `.env*`, `backend/`, `frontend/`. `joblib` é pickle:
   só artefatos do próprio repo.
10. Mudança de comportamento tem teste. Dependência nova só com aviso;
    `scikit-learn==1.9.1` é pinado de propósito.

## Como trabalhar
- Tarefas por ID: `/p0-mock`, `/p1-schemas`, `/p2-prompt`, `/p3-citacoes`,
  `/p4-regras`, `/p5-health`, `/p6-testes`, `/p7-similares`, `/p8-retreino`.
  Uma tarefa por sessão (`/clear` entre elas).
- Ciclo fixo: ler contrato e tarefa -> baseline do pytest -> PLANO e esperar aprovação
  -> testes primeiro (devem falhar pelo motivo certo) -> implementar o mínimo -> pytest
  verde -> commit `tipo(ID): resumo` -> resumo de 5 linhas. Commit após cada mudança, para poder voltar à versão anterior.
- Só diga que terminou mostrando a saída de `python -m pytest -q`.
- Nomes de domínio em português; campos JSON em camelCase como o contrato.

## Fora do escopo (não faça sem pedir)
spaCy/reconhecimento de entidades (E8), `/evidencias`, mapeamento do classificador para
os 14 padrões (Release 2), regras de conduta (são do backend), qualquer mudança em
`backend/` ou `frontend/`.
P7 (/similares) e P8 (retreino) autorizadas; ver `docs/escopo-rag-retreino.md`. Dados reais
só em `analise-service/dados_locais/` (ignorado pelo git); regras de leitura no `CLAUDE.md` da raiz.

## Ler sob demanda (não carregue inteiro)
- `docs/contrato/contrato-v3.md`: §3 pedido · §4 resposta · §7.2 citações · §8 erros e health
- `docs/DIVISAO_TRABALHO.md` §3 (tabela de tarefas) · `docs/SDD.md` §5.7, §6, §12
- Decisões e pendências: `docs/decisoes.md`
