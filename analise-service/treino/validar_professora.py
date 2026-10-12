"""P9: valida a "professora" (a LLM da destilação) contra os rótulos do João no conjunto ouro.

    cd analise-service
    python treino/validar_professora.py --teto-usd 0.5 --preco-entrada 0.15 --preco-saida 0.60

Roda a LLM da destilação (`rotulos_fracos.destilar`: cache em disco, retomada e teto de gasto) sobre os trechos de
`dados_locais/ouro_final.csv` e compara com os rótulos do João, por GRUPO (risco, oportunidade, interesse): revocação
nos positivos, alarme falso nos negativos, precisão, F1 e kappa de Cohen LLM × João. Trechos com `duvida`, sem rótulo
ou sem resposta da LLM ficam de fora (só contados).

Veredito por grupo: "usar" se kappa >= 0,6 e revocação >= 0,7; senão "NÃO usar para rótulos fracos nesse grupo".
O ouro_final.csv só tem o trecho alvo (o contexto não é guardado), então a LLM vê menos do que na destilação.

Escreve `docs/evidencias/professora-<data>.md` (só métricas). Nunca imprime texto de trecho, resposta da LLM,
mensagem de erro do provedor ou chave.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from treino.conciliar_ouro import LIMIAR_KAPPA, kappa_cohen  # noqa: E402
from treino.portao import metricas  # noqa: E402

GRUPOS = ("risco", "oportunidade", "interesse")
LIMIAR_REVOCACAO = 0.7
USAR = "usar"
NAO_USAR = "NÃO usar para rótulos fracos nesse grupo"


def comparar(ouro: list[dict], cache: dict[str, dict]) -> dict:
    """Métricas da LLM (`cache`, saída de `destilar`) contra o João (`ouro`, linhas de `ouro_final.csv`), por grupo."""
    fora = {"duvida": 0, "sem_resposta_da_llm": 0}
    validos = []
    for linha in ouro:
        if linha.get("duvida") == "1":
            fora["duvida"] += 1
        elif not cache.get(linha["id"], {}).get("ok"):
            fora["sem_resposta_da_llm"] += 1
        else:
            validos.append(linha)
    resultado: dict = {"_fora": fora}
    for g in GRUPOS:
        pares = [(linha[g] == "1", bool(cache[linha["id"]][g])) for linha in validos if linha.get(g) in ("0", "1")]
        joao, llm = [int(a) for a, _ in pares], [int(b) for _, b in pares]
        m = metricas(joao, llm)
        negativos = m["n"] - m["positivos"]
        m["tn"] = negativos - m["fp"]
        m["alarme_falso"] = round(m["fp"] / negativos, 4) if negativos else None
        m["kappa"] = kappa_cohen(joao, llm)
        resultado[g] = m
    return resultado


def veredito(m: dict) -> str:
    """`usar` só com kappa >= 0,6 E revocação >= 0,7 no grupo; sem positivos ou sem kappa não dá para confiar."""
    if m["positivos"] == 0 or m["kappa"] is None:
        return NAO_USAR
    return USAR if m["kappa"] >= LIMIAR_KAPPA and m["revocacao"] >= LIMIAR_REVOCACAO else NAO_USAR
