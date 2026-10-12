"""Inspeção LOCAL do classificador: imprime a estrutura do Pipeline e os hiperparâmetros (baseline do portão da P8).

    cd analise-service
    python scripts/inspecionar_modelo.py                      # app/modelos/classificador_risco.joblib
    python scripts/inspecionar_modelo.py caminho/modelo.joblib

Imprime SÓ estrutura: nome e classe de cada step, parâmetros escalares do vetorizador e do classificador, `classes_`
e o TAMANHO do vocabulário. Nunca imprime o vocabulário aprendido, stop words, nem qualquer texto: listas, conjuntos e
dicionários saem como tipo e tamanho. `joblib` é pickle: use só artefatos do próprio repo.
"""
import sys
from pathlib import Path
from typing import Any

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from app import config  # noqa: E402

_ESCALARES = (str, int, float, bool, type(None))


def descrever(valor: Any) -> str:
    """Escalares e tuplas de escalares por valor; coleções só por tipo e tamanho; funções pelo nome."""
    if isinstance(valor, _ESCALARES):
        return repr(valor)
    if isinstance(valor, tuple) and all(isinstance(v, _ESCALARES) for v in valor):
        return repr(valor)
    if isinstance(valor, (list, tuple, set, frozenset, dict)):
        return f"<{type(valor).__name__} len={len(valor)}>"
    return f"<{type(valor).__name__}>"


def parametros(estimador: Any) -> dict[str, str]:
    return {nome: descrever(v) for nome, v in sorted(estimador.get_params(deep=False).items())}


def inspecionar(pipeline: Any) -> list[str]:
    linhas = [f"classe: {type(pipeline).__name__}"]
    steps = getattr(pipeline, "steps", None)
    if steps is None:
        steps = [("modelo", pipeline)]
    linhas.append("steps: " + " -> ".join(f"{nome}={type(est).__name__}" for nome, est in steps))
    for nome, est in steps:
        linhas.append(f"[{nome}] {type(est).__name__}")
        for chave, valor in parametros(est).items():
            linhas.append(f"  {chave}: {valor}")
        if hasattr(est, "vocabulary_"):
            linhas.append(f"  tamanho_vocabulario: {len(est.vocabulary_)}")
        if hasattr(est, "classes_"):
            linhas.append(f"  classes_: {est.classes_.tolist()}")
        if hasattr(est, "coef_"):
            linhas.append(f"  coef_.shape: {tuple(est.coef_.shape)}")
    return linhas


def main(argv: list[str]) -> int:
    caminho = Path(argv[0]) if argv else config.CAMINHO_MODELO_LOCAL
    if not caminho.is_file():
        print("erro: artefato_nao_encontrado")
        return 1
    import joblib

    try:
        pipeline = joblib.load(caminho)  # artefato do próprio repo (joblib é pickle)
    except Exception as e:  # só o tipo, nunca a mensagem
        print(f"erro: {type(e).__name__}")
        return 1
    import sklearn

    print(f"artefato: {caminho.name} | scikit-learn instalado: {sklearn.__version__}")
    print("\n".join(inspecionar(pipeline)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
