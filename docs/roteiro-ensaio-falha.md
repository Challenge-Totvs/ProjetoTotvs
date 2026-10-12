# Roteiro de 5 minutos: a cadeia de motores aguenta falha (demo da banca)

Mensagem: **o InsightCall sempre responde.** Se um motor cai, o próximo assume, a resposta diz quem respondeu e o
`/health` mostra o estado. Só some a análise quando os quatro motores falham (aí vem um 503 estruturado, não um erro cru).

Cadeia: `llm1` (Anthropic) → `llm2` (OpenAI) → `local` (classificador + regex) → `regras` (só regex) → 503.
A alavanca da demo é a variável `FORCAR_FALHA`: lista de motores que falham de propósito, sem chamar a API.

## Antes de entrar (2 min, fora do tempo)

1. Rode o ensaio offline uma vez: `python scripts/ensaio_falha.py` (sem rede, sem chave; mostra a tabela dos 5 cenários).
   Se a internet cair na banca, **essa tabela é o plano B**: a mesma sequência, em 5 s.
2. Confira que `analise-service/.env` tem as chaves das duas LLMs (não mostre o arquivo na tela).
   O smoke das duas LLMs passou em 12/10 (`docs/evidencias/smoke-12-10.md`). Se mesmo assim a `llm1` não responder na
   hora, o cenário 1 mostra `llm1:<erro> > llm2:ok`: não é defeito da demo, é a cadeia funcionando; avise e siga para o 2.
3. Terminal A (servidor) e terminal B (comandos), os dois em `analise-service/`. No terminal B, cole **uma vez**:

```powershell
function Analisar {
  $t = curl.exe -s -w "`n%{http_code}" -X POST http://localhost:8000/analisar -H "Content-Type: application/json" --data-binary "@../docs/contrato/pedido-v3.json"
  $j = $t[0] | ConvertFrom-Json
  "HTTP $($t[-1])  motor=$($j.motor)  avisos=$($j.avisos -join ',')  codigo=$($j.codigo)"
  $j.tentativas | Format-Table motor, ok, erro, duracaoMs
}
function Saude { $h = Invoke-RestMethod http://localhost:8000/health; "status=$($h.status)  " + (($h.motores | ForEach-Object { "$($_.motor)=$($_.ok)" }) -join "  ") }
```

O pedido é o curto do contrato (`docs/contrato/pedido-v3.json`): a LLM responde em poucos segundos. Para mostrar o pior
caso, troque por `tests/fixtures/transcricao-sintetica-p90.json` (399 turnos; a llm1 leva ~9 s e a llm2 ~17 s).

## Como trocar de cenário (leva ~3 s)

No terminal A: `Ctrl+C`, defina a variável e suba de novo. **Reiniciar é obrigatório**: o `.env` só é lido na subida e o
reinício zera a memória do `/health` (sem reiniciar, uma falha forçada fica registrada por 5 minutos).

```powershell
$env:FORCAR_FALHA = "llm1"        # o valor de cada cenário está na tabela abaixo; vazio = nada falha
python -m uvicorn app.main:app --port 8000
```

Depois, no terminal B: `Saude` e `Analisar`.

## Os 5 cenários (≈ 50 s cada)

| # | `FORCAR_FALHA` | `/health` (`Saude`) | Resposta (`Analisar`) | Uma frase para dizer |
|---|---|---|---|---|
| 1 | *(vazio)*: `$env:FORCAR_FALHA = ""` | `status=ok`, os 4 motores `True` | HTTP 200, `motor=llm1`, 1 tentativa (`llm1 ok`), sem avisos | "Caminho feliz: a LLM principal responde e a resposta traz de volta quem respondeu." |
| 2 | `llm1` | `status=ok`, `llm1=False`, o resto `True` | HTTP 200, `motor=llm2`, tentativas `llm1 erro_provedor` e `llm2 ok` | "Derrubei a principal: a cadeia passou para a segunda LLM sozinha, e a tentativa que falhou ficou registrada." |
| 3 | `llm1,llm2` | `status=degradado`, `llm1` e `llm2` `False` | HTTP 200, `motor=local`, aviso `contingencia_modelo_local` | "Sem nenhuma LLM, o modelo local responde, e o aviso de contingência deixa claro que é uma resposta mais simples." |
| 4 | `llm1,llm2,local` | `status=degradado`, só `regras=True` | HTTP 200, `motor=regras`, aviso `contingencia_regras` | "Só sobraram as regras: menos inteligente, mas ainda devolve temas com citação literal." |
| 5 | `llm1,llm2,local,regras` | `status=indisponivel`, os 4 `False` | HTTP **503**, `codigo=analise_indisponivel`, 4 tentativas com erro | "Quando tudo cai, o serviço não inventa resposta: devolve um 503 estruturado com as tentativas, e o Java trata como análise indisponível (503)." |

Fechamento (10 s): "Em nenhum cenário a análise foi inventada. Cada resposta diz o motor e o caminho que percorreu, e o `/health`
mostra o estado de cada peça sem gastar token."

## O que olhar na tela

- **`motor`**: quem respondeu (`llm1`, `llm2`, `local` ou `regras`). Vem do código, nunca da LLM.
- **`tentativas`**: um item por motor tentado, na ordem, com `ok`, `erro` (código do contrato) e `duracaoMs`. Forçado = `erro_provedor`.
- **`avisos`**: `contingencia_modelo_local` ou `contingencia_regras` quando a resposta não veio de uma LLM.
- **`/health`**: `status` (`ok` = alguma LLM ok · `degradado` = só local/regras · `indisponivel` = nenhum) e o `ok` de cada motor.
  O `/health` nunca chama a API de uma LLM.

## Ao terminar

`$env:FORCAR_FALHA = ""` e reinicie o servidor normalmente. Nenhuma chave aparece em nenhum comando deste roteiro.
