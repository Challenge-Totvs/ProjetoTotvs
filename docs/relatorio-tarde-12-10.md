# Relatório do lote da tarde — 12/10/2026

Lote sem supervisão (~2 h), autorizado a seguir sem aprovação de plano. O plano de cada item é escrito aqui antes de
implementar. Sem texto de transcrição neste arquivo (só contagens e métricas). Commits em nome de Joao, sem coautoria.
Sem push.

Baseline do pytest no início do lote (`analise-service/.venv`): `414 passed in 14.69s`.

## Item 1 — Reorganizar os CLAUDE.md
**Plano:** (a) `CLAUDE.md` da raiz fica só com o que vale para o grupo: mapa do repo, contrato, prazos, estado atual,
arquitetura em 5 linhas, regras de dados e de commit (regras 11 e 12 mantêm o número) e "ler sob demanda" do que é do
grupo. (b) `analise-service/CLAUDE.md` novo: regras invioláveis 1-10 (texto preservado), "não edite backend/ e
frontend/", comandos, tarefas por ID, ciclo fixo, fora do escopo, ler sob demanda. (c) `CLAUDE.local.md` na raiz com as
preferências do João; o `.gitignore` já tem a linha `CLAUDE.local.md` (conferido com `git check-ignore`), então nada a
acrescentar. (d) `.claude/skills/p8-retreino/SKILL.md`: só a linha da seção REGRAS DE DADOS sobre ler texto real.
**Antes → depois (nomes de seção):**
- `CLAUDE.md` (raiz) antes: Mapa · Estado atual · Comandos · Arquitetura · Regras invioláveis (1-12) · Como trabalhar ·
  Fora do escopo · Ler sob demanda. Depois: Mapa (sem "NÃO edite") · Contrato · Estado atual · Arquitetura · Regras de
  dados e de commit (11, 12 + decisão do corpus anonimizado) · Ler sob demanda.
- `analise-service/CLAUDE.md` (novo): Não edite · Comandos · Regras invioláveis (1-10) · Como trabalhar (tarefas por ID,
  ciclo fixo) · Fora do escopo · Ler sob demanda.
- `CLAUDE.local.md` (novo, ignorado pelo git): preferências de commit e de comunicação.
- `p8-retreino/SKILL.md`: só a primeira linha da seção REGRAS DE DADOS sobre ler texto real.
**Status:** concluído.

## Item 2 — `docs/evidencias/smoke-12-10.md`
**Plano:** criar o arquivo (a pasta `docs/evidencias/` ainda não existe) só com os fatos informados pelo João; não tocar
em `PROMPT_VALIDADO_COM_LLM_REAL`.
**Status:** concluído (`PROMPT_VALIDADO_COM_LLM_REAL` intocado). Sem mudança de código; suíte inalterada (414).
