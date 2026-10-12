# Handoff para o Kelwin — 12/10/2026

O que mudou no Python e o que o Java precisa saber/fazer. O formato do `POST /analisar` (contrato v3) **não mudou**.

## 1. Semântica do `GET /health` (já no contrato v3 §8.3)
- Formato igual: `{status, pipelineVersao, motores: [{motor, ok}]}`.
- `ok` de cada motor = configurado **e** a última tentativa REAL dele não falhou nos últimos 5 minutos (memória do
  processo; reiniciar o Python zera). Uma tentativa bem-sucedida recupera na hora.
- `regras` **não é mais "sempre true"**: nasce `true` e cai para `false` por 5 min se falhar de verdade.
- `status`: `ok` (alguma LLM ok), `degradado` (só `local`/`regras`), `indisponivel` (nenhum).
- O `/health` nunca chama a API de LLM. Para a demo, `FORCAR_FALHA=llm1` no `.env` do Python derruba a LLM principal
  (o `/health` mostra `ok: false` na hora e a análise cai para `llm2`).

## 2. `POST /similares` — contrato PROPOSTO (validar comigo antes de codar)
Detalhes em `docs/contrato/similares.md`; fixtures `docs/contrato/pedido-similares.json` e `resposta-similares.json`.
- Pedido: `{"texto": "...", "referencias": [{"id": "...", "texto": "..."}], "topK": 3, "limiar": 0.2}`
  (`referencias` 0..200, `topK` 1..50, `limiar` opcional 0..1).
- Resposta 200: `{"similares": [{"id": "np-101", "score": 0.259}], "versaoContrato": "v3"}`, por score decrescente;
  lista vazia é válida. 422 no formato do §8.1 para pedido inválido.
- **O que o Java precisa implementar:**
  1. cliente HTTP do `/similares` (mesma base URL do `/analisar`, timeout curto, sugestão 3 s);
  2. para cada tema novo, enviar o `texto` do tema e os trechos "não procede" do MESMO cliente como `referencias`
     (`id` = id do registro no Java);
  3. campo `semelhanteNaoProcede` no tema devolvido ao frontend (id da referência mais parecida ou booleano: você
     escolhe, me avise);
  4. **ignorar falha em silêncio** (timeout, 4xx, 5xx => o tema segue sem `semelhanteNaoProcede`; só log no Java).
- O limiar (0,2) ainda não foi calibrado com dados reais; pode mudar sem mudar o formato.

## 3. `descartados[].motivo`
O Java lê o motivo como texto livre (`String`), mas o frontend sempre prefixa "Evidência não localizada." antes dele.
Hoje o Python já pode devolver `evidencia_nao_localizada`, `padrao_fora_da_lista`, `evento_fora_da_lista`,
`trecho_curto` e `trecho_longo` (contrato §6.7): só o primeiro combina com o prefixo. Sugestão: o frontend mapear
motivo -> rótulo. Nenhum motivo novo foi criado hoje; antes de criar um, combino com você.

## 4. Pendências do teu lado
- **AC9**: teste Java lendo as fixtures `docs/contrato/resposta-v3-*.json` em `ContratoV3.Resposta`.
- **A10**: atualizar o SDD §6.2 para apontar para `docs/contrato/contrato-v3.md`.
- **Timeout do Java**: continua 120 s; vou confirmar com o smoke das LLMs reais (incluindo a transcrição sintética de
  ~72 mil caracteres, o P90) e te aviso se precisar mudar.

## 5. Chave da Anthropic
A chave usada pelo Python precisa ser **de um workspace** ou vir acompanhada do ID do workspace. O Python agora aceita
a variável opcional `LLM_PRINCIPAL_WORKSPACE_ID` (envia o cabeçalho `anthropic-workspace-id`); sem ela nada muda. Ao
me passar a chave, diga de qual workspace ela é.

## 6. Para saber (sem ação)
- O motor `local` pode, no futuro, usar um classificador de interesse próprio; está DESLIGADO e só liga depois do
  portão de qualidade aprovar um modelo treinado com os dados reais. O formato da resposta não muda.
