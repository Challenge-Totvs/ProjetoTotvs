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
import argparse
import datetime as dt
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from treino.comum import DADOS, EVIDENCIAS, imprimir, ler_csv  # noqa: E402
from treino.conciliar_ouro import LIMIAR_KAPPA, kappa_cohen  # noqa: E402
from treino.portao import metricas  # noqa: E402
from treino.rotulos_fracos import Chamar, criar_chamada, destilar, ler_cache  # noqa: E402

GRUPOS = ("risco", "oportunidade", "interesse")
LIMIAR_REVOCACAO = 0.7
USAR = "usar"
NAO_USAR = "NÃO usar para rótulos fracos nesse grupo"
TETO_MAXIMO_USD = 0.5  # validar a professora é barato: o ouro tem poucas centenas de trechos
POSITIVOS_MINIMOS = 30  # abaixo disso o grupo é só indicativo
MODOS = {"unico": "rotulador único (João Paulo), sem validação cruzada entre pessoas",
         "pares": "pares de rotuladores (com arbitragem das divergências)"}


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


def escrever_relatorio(caminho: Path, meta: dict, r: dict, destilacao: dict) -> None:
    modo = MODOS.get(meta.get("modo"), "desconhecido (sem ouro_final.json)")
    completo = meta.get("completo") is True
    fora = r["_fora"]
    linhas = [f"# Validação da professora — {meta['data']}", "",
              "Só métricas e contagens; nenhum texto de trecho. Gerado por `treino/validar_professora.py`.", ""]
    if meta["preliminar"]:
        linhas += [f"> **PRELIMINAR:** {fora['sem_resposta_da_llm']} trecho(s) sem resposta da LLM (teto de gasto, "
                   "erro do provedor ou item sem resposta). Rode de novo para retomar do cache.", ""]
    linhas += [
        f"- Modo: **{modo}**",
        f"- Ouro: **{'COMPLETO' if completo else 'PARCIAL'}**"
        + ("" if meta.get("modo") else " (sem `ouro_final.json`; tratado como parcial)"),
        f"- Motor da professora: {meta['motor']} (modelo do `.env`)",
        f"- Trechos no ouro: {meta['trechos']}; fora da comparação: {fora['duvida']} com dúvida, "
        f"{fora['sem_resposta_da_llm']} sem resposta da LLM",
        f"- Gasto: US$ {destilacao.get('gasto_acumulado_usd', 0)} de teto US$ {destilacao.get('teto_usd')} "
        f"({destilacao.get('chamadas_acumuladas', 0)} chamada(s) acumuladas)",
        f"- Limiares do veredito: kappa >= {LIMIAR_KAPPA} e revocação >= {LIMIAR_REVOCACAO} em cada grupo",
        "- Limitação: o `ouro_final.csv` guarda só o trecho alvo; a professora viu menos contexto do que na destilação.",
        f"- **Aviso:** n pequeno é só indicativo (grupos com menos de {POSITIVOS_MINIMOS} positivos oscilam muito; "
        "um erro muda a revocação em vários pontos).", "",
        "## Métricas por grupo (LLM × João)", "",
        "| Grupo | n | positivos | revocação | alarme falso | precisão | F1 | kappa |", "|---|---|---|---|---|---|---|---|",
    ]
    for g in GRUPOS:
        m = r[g]
        pequeno = " (n pequeno)" if m["positivos"] < POSITIVOS_MINIMOS else ""
        linhas.append(f"| {g}{pequeno} | {m['n']} | {m['positivos']} | {m['revocacao']} | {m['alarme_falso']} | "
                      f"{m['precisao']} | {m['f1']} | {m['kappa']} |")
    linhas += ["", "Revocação = acertos entre os positivos do João; alarme falso = positivos da LLM entre os "
               "negativos do João.", "", "## Veredito", ""]
    linhas += [f"- {g}: **{veredito(r[g])}**" for g in GRUPOS]
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main(argv: list[str], chamar: Chamar | None = None) -> int:
    p = argparse.ArgumentParser(description="P9: valida a professora (LLM da destilação) contra o ouro do João.")
    p.add_argument("--ouro", type=Path, default=DADOS / "ouro_final.csv")
    p.add_argument("--pasta", type=Path, default=DADOS / "professora", help="cache e estado (retomada)")
    p.add_argument("--relatorio", type=Path, default=None, help="padrão: docs/evidencias/professora-<data>.md")
    p.add_argument("--motor", choices=["llm1", "llm2"], default="llm2")
    p.add_argument("--modelo", default=None, help="modelo barato (padrão: o do .env para o motor)")
    p.add_argument("--teto-usd", type=float, required=True, help=f"obrigatório; máximo {TETO_MAXIMO_USD}")
    p.add_argument("--preco-entrada", type=float, required=True, help="US$ por milhão de tokens de entrada")
    p.add_argument("--preco-saida", type=float, required=True, help="US$ por milhão de tokens de saída")
    args = p.parse_args(argv)
    if not 0 < args.teto_usd <= TETO_MAXIMO_USD:
        p.error(f"--teto-usd deve estar entre 0 e {TETO_MAXIMO_USD}")
    if not args.ouro.is_file():
        print(f"erro: arquivo não encontrado: {args.ouro.name}")
        return 1

    ouro = ler_csv(args.ouro)
    meta_ouro = {}
    if (args.ouro.parent / "ouro_final.json").is_file():
        meta_ouro = json.loads((args.ouro.parent / "ouro_final.json").read_text(encoding="utf-8"))
    candidatos = [{"id": linha["id"], "texto": linha["texto"]} for linha in ouro if linha.get("duvida") != "1"]
    if chamar is None:
        from app import config

        config.carregar_dotenv()
        chamar = criar_chamada(args.motor, args.modelo)
    destilacao = destilar(candidatos, chamar, args.teto_usd, args.preco_entrada, args.preco_saida, args.pasta)

    r = comparar(ouro, ler_cache(args.pasta / "cache.jsonl"))
    data = dt.date.today().isoformat()
    meta = {**meta_ouro, "data": data, "motor": args.motor, "trechos": len(ouro),
            "preliminar": r["_fora"]["sem_resposta_da_llm"] > 0}
    relatorio = args.relatorio or EVIDENCIAS / f"professora-{data}.md"
    escrever_relatorio(relatorio, meta, r, destilacao)
    imprimir({"relatorio": relatorio.name, "preliminar": meta["preliminar"], "destilacao": destilacao,
              "fora": r["_fora"], "metricas": {g: r[g] for g in GRUPOS},
              "veredito": {g: veredito(r[g]) for g in GRUPOS}})
    return 2 if destilacao.get("erro") else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
