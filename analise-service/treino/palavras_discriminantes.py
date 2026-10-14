"""P8: palavras de maior peso por classe, por grupo (risco/interesse).

    cd analise-service
    python treino/palavras_discriminantes.py                                   # último candidato em dados_locais/candidatos/
    python treino/palavras_discriminantes.py --candidato dados_locais/candidatos/2026-10-14 --top 15

Lê o Pipeline (`tfidf` + `clf`, `sklearn.linear_model.LogisticRegression`) de cada grupo e lista, por classe, as
N palavras/n-gramas do vocabulário do TF-IDF com maior coeficiente em valor absoluto: coeficiente positivo empurra
para a classe 1 (ex.: risco), negativo empurra para a classe 0. Isto é vocabulário do TF-IDF (tokens/n-gramas, não
texto de transcrição), e é exatamente o que este script existe para mostrar — não é a exceção de "nunca imprime
texto de trecho" (que vale para citações e recortes de reunião, não para a lista de palavras do modelo).

Escreve `docs/evidencias/palavras-<data>.md`.
"""
import argparse
import datetime as dt
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from treino.comum import DADOS, EVIDENCIAS, imprimir  # noqa: E402

GRUPOS_PADRAO = ("risco", "interesse")
TOP_PADRAO = 20


def palavras_de_maior_peso(pipeline: Any, top: int = TOP_PADRAO) -> dict[str, list[tuple[str, float]]]:
    """{"positivas": [(palavra, peso), ...], "negativas": [...]} ordenadas por |peso| decrescente.

    `positivas` empurra a previsão para a classe 1 (coeficiente > 0); `negativas`, para a classe 0 (coeficiente < 0).
    """
    tfidf = pipeline.named_steps["tfidf"]
    clf = pipeline.named_steps["clf"]
    vocabulario = tfidf.get_feature_names_out()
    coeficientes = clf.coef_[0]
    pares = list(zip(vocabulario, coeficientes))
    positivas = sorted((p for p in pares if p[1] > 0), key=lambda p: p[1], reverse=True)[:top]
    negativas = sorted((p for p in pares if p[1] < 0), key=lambda p: p[1])[:top]
    return {"positivas": [(p, round(float(c), 4)) for p, c in positivas],
            "negativas": [(p, round(float(c), 4)) for p, c in negativas]}


def ultimo_candidato(raiz: Path) -> Path | None:
    pastas = sorted((p for p in raiz.iterdir() if (p / "metadata.json").is_file()), key=lambda p: p.stat().st_mtime) \
        if raiz.is_dir() else []
    return pastas[-1] if pastas else None


def _linha(palavra: str, peso: float) -> str:
    return f"| {palavra} | {peso} |"


def escrever_relatorio(caminho: Path, resultado: dict[str, dict], candidato: str, top: int) -> None:
    linhas = [
        f"# Palavras de maior peso por classe — {dt.date.today().isoformat()}", "",
        f"Candidato: `{candidato}`. Top {top} palavras/n-gramas do vocabulário do TF-IDF por coeficiente da "
        "regressão logística (|coeficiente| decrescente). Vocabulário do modelo, não texto de transcrição.", "",
    ]
    for grupo, grupos in resultado.items():
        linhas += [f"## {grupo}", "",
                   f"### Empurram para {grupo} = 1 (coeficiente positivo)", "",
                   "| palavra/n-grama | coeficiente |", "|---|---|"]
        linhas += [_linha(p, c) for p, c in grupos["positivas"]]
        linhas += ["", f"### Empurram para {grupo} = 0 (coeficiente negativo)", "",
                   "| palavra/n-grama | coeficiente |", "|---|---|"]
        linhas += [_linha(p, c) for p, c in grupos["negativas"]]
        linhas.append("")
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="P8: palavras de maior peso por classe, por grupo.")
    p.add_argument("--candidato", type=Path, default=None, help="pasta do candidato (padrão: o mais recente)")
    p.add_argument("--candidatos", type=Path, default=DADOS / "candidatos")
    p.add_argument("--grupos", nargs="+", default=list(GRUPOS_PADRAO))
    p.add_argument("--top", type=int, default=TOP_PADRAO)
    p.add_argument("--saida", type=Path, default=None, help="padrão docs/evidencias/palavras-<data>.md")
    args = p.parse_args(argv)

    pasta = args.candidato or ultimo_candidato(args.candidatos)
    if pasta is None:
        print("erro: candidato não encontrado (rode treino/treinar.py)")
        return 1
    faltando = [g for g in args.grupos if not (pasta / f"{g}.joblib").is_file()]
    if faltando:
        print(f"erro: modelo(s) não encontrado(s) em {pasta}: {', '.join(faltando)}")
        return 1

    import joblib

    resultado = {}
    for grupo in args.grupos:
        # joblib é pickle: só artefato do próprio repo/candidatos gerados por treino/treinar.py
        pipeline = joblib.load(pasta / f"{grupo}.joblib")
        resultado[grupo] = palavras_de_maior_peso(pipeline, args.top)

    saida = args.saida or EVIDENCIAS / f"palavras-{dt.date.today().isoformat()}.md"
    escrever_relatorio(saida, resultado, pasta.name, args.top)
    imprimir({"candidato": pasta.name, "relatorio": saida.name, "top": args.top,
              "grupos": {g: {"positivas": len(v["positivas"]), "negativas": len(v["negativas"])}
                        for g, v in resultado.items()}})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
