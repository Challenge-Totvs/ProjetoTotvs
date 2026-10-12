"""Etapa 4 do P8: treina os candidatos de RISCO (retreino) e de INTERESSE (novo) com os rótulos fracos.

    cd analise-service
    python treino/treinar.py                                     # dados_locais/rotulos_fracos.csv -> dados_locais/candidatos/<data>/
    python treino/treinar.py --param clf__C=0.5 --justificativa "..."   # mudar hiperparâmetro exige justificativa

Os dois partem de `sklearn.base.clone` do Pipeline de `app/modelos/classificador_risco.joblib` (D17): herdam TODOS os
hiperparâmetros, inclusive a lista de 315 stop words, que são o baseline do portão. Treina só com rótulos fracos e só
com reuniões fora do holdout; o conjunto ouro nunca entra (só mede). Grava `risco.joblib`, `interesse.joblib` e
`metadata.json` (data, sha256 dos dados, versão do scikit-learn, tamanhos, hiperparâmetros, mudanças). `joblib` é
pickle: só artefatos do próprio repo. A promoção para `app/` é MANUAL (o `portao.py` imprime o comando).
"""
import argparse
import ast
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from treino.comum import CAMINHO_MODELO_ATUAL, DADOS, imprimir, ler_csv, sha256_arquivo  # noqa: E402

MODELOS = ("risco", "interesse")
TAMANHO_MINIMO_TEXTO_IGUAL = 40  # texto idêntico ao do ouro a partir deste tamanho conta como possível vazamento
_ESCALARES = (str, int, float, bool, type(None))


def descrever(valor: Any) -> Any:
    """Hiperparâmetro para o metadata: escalares por valor, coleções só por tipo e tamanho (nunca as stop words)."""
    if isinstance(valor, _ESCALARES):
        return valor
    if isinstance(valor, tuple) and all(isinstance(v, _ESCALARES) for v in valor):
        return list(valor)
    if isinstance(valor, (list, tuple, set, frozenset, dict)):
        return f"<{type(valor).__name__} len={len(valor)}>"
    return f"<{type(valor).__name__}>"


def hiperparametros(pipeline: Any) -> dict[str, Any]:
    return {nome: descrever(v) for nome, v in sorted(pipeline.get_params(deep=True).items())
            if "__" in nome}  # só os parâmetros dos steps (tfidf__..., clf__...)


def carregar_base(caminho: Path) -> Any:
    import joblib

    if not caminho.is_file():
        raise SystemExit(f"erro: modelo base não encontrado: {caminho.name}")
    return joblib.load(caminho)  # artefato do próprio repo (joblib é pickle)


def ler_params(itens: list[str]) -> dict[str, Any]:
    params = {}
    for item in itens:
        if "=" not in item:
            raise SystemExit(f"erro: --param espera chave=valor, recebeu {item!r}")
        chave, bruto = item.split("=", 1)
        try:
            valor = ast.literal_eval(bruto)
        except (ValueError, SyntaxError):
            valor = bruto
        params[chave.strip()] = valor
    return params


def novo_modelo(base: Any, params: dict[str, Any]) -> Any:
    from sklearn.base import clone

    modelo = clone(base)  # mesmos steps e hiperparâmetros, sem nada aprendido
    if params:
        modelo.set_params(**params)
    return modelo


def conferir_separacao(linhas: list[dict], holdout: set[str], ouro: list[dict]) -> dict:
    """Aborta se alguma reunião do holdout ou id do ouro estiver no treino; conta textos idênticos aos do ouro."""
    vazadas = sum(1 for x in linhas if x.get("reuniao") in holdout)
    if vazadas:
        raise SystemExit(f"erro: {vazadas} trecho(s) de reuniões do holdout nos rótulos de treino")
    ids_ouro = {x["id"] for x in ouro}
    if any(x["id"] in ids_ouro for x in linhas):
        raise SystemExit("erro: trecho do conjunto ouro nos rótulos de treino (o ouro só mede)")
    textos_ouro = {x["texto"].strip() for x in ouro if len(x.get("texto", "").strip()) >= TAMANHO_MINIMO_TEXTO_IGUAL}
    iguais = sum(1 for x in linhas if x["texto"].strip() in textos_ouro)
    return {"reunioes_do_holdout_no_treino": 0, "ids_do_ouro_no_treino": 0, "textos_iguais_ao_ouro": iguais}


def treinar(linhas: list[dict], base: Any, params: dict[str, Any]) -> tuple[dict[str, Any], dict]:
    textos = [x["texto"] for x in linhas]
    modelos, tamanhos = {}, {}
    for nome in MODELOS:
        y = [1 if x[nome] == "1" else 0 for x in linhas]
        if len(set(y)) < 2:
            raise SystemExit(f"erro: rótulo '{nome}' tem uma classe só ({sum(y)} positivos em {len(y)}); não dá para treinar")
        modelo = novo_modelo(base, params)
        modelo.fit(textos, y)
        modelos[nome] = modelo
        tamanhos[nome] = {"positivos": sum(y), "negativos": len(y) - sum(y)}
    return modelos, tamanhos


def pasta_livre(raiz: Path, data: str) -> Path:
    pasta, i = raiz / data, 2
    while pasta.exists():
        pasta, i = raiz / f"{data}_{i}", i + 1
    return pasta


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Etapa 4 do P8: treina candidatos de risco e interesse (só contagens).")
    p.add_argument("--rotulos", type=Path, default=DADOS / "rotulos_fracos.csv")
    p.add_argument("--base", type=Path, default=CAMINHO_MODELO_ATUAL, help="Pipeline atual (D17), só para clone")
    p.add_argument("--holdout", type=Path, default=DADOS / "holdout_reunioes.csv")
    p.add_argument("--col-holdout", default="reuniao", help="coluna da reunião no holdout")
    p.add_argument("--ouro", type=Path, default=DADOS / "ouro_final.csv")
    p.add_argument("--candidatos", type=Path, default=DADOS / "candidatos")
    p.add_argument("--param", action="append", default=[], help="hiperparâmetro alterado (chave=valor); exige justificativa")
    p.add_argument("--justificativa", default="")
    args = p.parse_args(argv)

    params = ler_params(args.param)
    if params and not args.justificativa.strip():
        p.error("--param exige --justificativa (registrada no metadata.json)")
    if not args.rotulos.is_file():
        print(f"erro: arquivo não encontrado: {args.rotulos.name}")
        return 1
    linhas = ler_csv(args.rotulos)
    holdout = set()
    if args.holdout.is_file():
        holdout = {(x.get(args.col_holdout) or "").strip() for x in ler_csv(args.holdout)} - {""}
    ouro = ler_csv(args.ouro) if args.ouro.is_file() else []
    separacao = conferir_separacao(linhas, holdout, ouro)
    separacao["holdout_conferido"] = bool(holdout)

    import sklearn

    base = carregar_base(args.base)
    modelos, tamanhos = treinar(linhas, base, params)
    data = dt.date.today().isoformat()
    pasta = pasta_livre(args.candidatos, data)
    pasta.mkdir(parents=True)
    import joblib

    for nome, modelo in modelos.items():
        joblib.dump(modelo, pasta / f"{nome}.joblib")
    meta = {
        "data": data, "pasta": pasta.name, "scikit_learn": sklearn.__version__,
        "dados": {"arquivo": args.rotulos.name, "sha256": sha256_arquivo(args.rotulos), "trechos": len(linhas),
                  "reunioes": len({x.get("reuniao") for x in linhas}),
                  "fonte_llm": sum(1 for x in linhas if x.get("fonte") == "llm")},
        "base": {"arquivo": args.base.name, "sha256": sha256_arquivo(args.base)},
        "tamanhos": tamanhos,
        "hiperparametros": hiperparametros(modelos["risco"]),
        "mudancas": [{"parametro": k, "valor": descrever(v), "valor_base": descrever(base.get_params(deep=True).get(k)),
                      "justificativa": args.justificativa} for k, v in params.items()],
        "separacao": separacao,
    }
    (pasta / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    imprimir({"candidato": pasta.name, "tamanhos": tamanhos, "mudancas": len(params), "separacao": separacao})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
