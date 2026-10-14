"""P8: confident learning (cleanlab) sobre os rótulos fracos, por grupo (risco/interesse).

    cd analise-service
    python treino/rotulos_suspeitos.py                              # dados_locais/rotulos_fracos.csv -> dados_locais/rotulos_suspeitos.csv
    python treino/rotulos_suspeitos.py --dobras 5 --saida dados_locais/rotulos_suspeitos.csv

Para cada grupo, clona o Pipeline base (D17, o mesmo de `treino/treinar.py`) e usa `sklearn.model_selection.
GroupKFold` AGRUPADO POR CLIENTE (nunca por trecho nem por reunião isolada: trechos do mesmo cliente não se separam
entre dobras, para a probabilidade prevista de um trecho nunca vir de um modelo que viu outro trecho do mesmo
cliente) para gerar probabilidades fora da dobra (`cross_val_predict(..., method="predict_proba")`). Passa essas
probabilidades e o rótulo de treino (LLM quando existe, senão regra) para `cleanlab.filter.find_label_issues`, que
aponta os trechos cujo rótulo provavelmente está errado (o modelo, sem nunca ter visto aquele cliente, discorda do
rótulo com confiança).

Dependência nova: `cleanlab` (só no pipeline de treino, listada em `requirements-treino.txt`; não entra no
`requirements.txt` do serviço).

Escreve `dados_locais/rotulos_suspeitos.csv` com `id, reuniao, cliente, grupo, rotulo, confianca, rank` — SEM texto
de trecho. Esse arquivo é o que `treino/treinar.py --excluir-suspeitos` lê para excluir os suspeitos do treino
daquele grupo (só daquele: um trecho suspeito em risco continua valendo para interesse). Imprime só contagens.
"""
import argparse
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from treino.comum import DADOS, gravar_csv, imprimir, ler_csv  # noqa: E402
from treino.treinar import CAMINHO_MODELO_ATUAL, MODELOS, carregar_base, novo_modelo  # noqa: E402

DOBRAS_PADRAO = 5
COLUNAS_SAIDA = ["id", "reuniao", "cliente", "grupo", "rotulo", "confianca", "rank"]


def _coluna_cliente(linha: dict) -> str:
    return (linha.get("cliente") or linha.get("reuniao") or "").strip()


def dobras_possiveis(grupos_cliente: list[str], maximo: int) -> int:
    """GroupKFold exige 2 <= n_splits <= nº de clientes distintos. 0 se não der para montar ao menos 2 dobras."""
    distintos = len(set(grupos_cliente))
    dobras = min(maximo, distintos)
    return dobras if dobras >= 2 else 0


def probabilidades_fora_da_dobra(textos: list[str], y: list[int], grupos_cliente: list[str], base: Any,
                                 dobras: int) -> Any:
    from sklearn.model_selection import GroupKFold, cross_val_predict

    modelo = novo_modelo(base, {})
    cv = GroupKFold(n_splits=dobras)
    return cross_val_predict(modelo, textos, y, cv=cv, groups=grupos_cliente, method="predict_proba")


def encontrar_suspeitos(y: list[int], pred_probs: Any) -> list[tuple[int, float]]:
    """[(indice, confianca_no_rotulo_dado)] na ordem de suspeita (mais suspeito primeiro)."""
    from cleanlab.filter import find_label_issues

    indices = find_label_issues(labels=y, pred_probs=pred_probs, return_indices_ranked_by="self_confidence")
    return [(int(i), round(float(pred_probs[i][y[i]]), 4)) for i in indices]


def suspeitos_do_grupo(linhas: list[dict], grupo: str, base: Any, dobras_pedidas: int) -> tuple[list[dict], dict]:
    textos = [x["texto"] for x in linhas]
    y = [1 if x[grupo] == "1" else 0 for x in linhas]
    grupos_cliente = [_coluna_cliente(x) for x in linhas]
    info: dict[str, Any] = {"trechos": len(linhas), "clientes": len(set(grupos_cliente)), "dobras_pedidas": dobras_pedidas}

    if len(set(y)) < 2:
        return [], {**info, "pulado": "uma classe só, não dá para rodar confident learning"}
    dobras = dobras_possiveis(grupos_cliente, dobras_pedidas)
    if dobras < 2:
        return [], {**info, "pulado": "menos de 2 clientes distintos"}
    info["dobras_usadas"] = dobras

    pred_probs = probabilidades_fora_da_dobra(textos, y, grupos_cliente, base, dobras)
    suspeitos_idx = encontrar_suspeitos(y, pred_probs)
    linhas_saida = [
        {"id": linhas[i]["id"], "reuniao": linhas[i].get("reuniao", ""), "cliente": _coluna_cliente(linhas[i]),
         "grupo": grupo, "rotulo": y[i], "confianca": conf, "rank": rank}
        for rank, (i, conf) in enumerate(suspeitos_idx)
    ]
    info["suspeitos"] = len(linhas_saida)
    return linhas_saida, info


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="P8: confident learning (cleanlab) sobre os rótulos fracos, por grupo.")
    p.add_argument("--rotulos", type=Path, default=DADOS / "rotulos_fracos.csv")
    p.add_argument("--base", type=Path, default=CAMINHO_MODELO_ATUAL, help="Pipeline atual (D17), só para clone")
    p.add_argument("--grupos", nargs="+", default=list(MODELOS))
    p.add_argument("--dobras", type=int, default=DOBRAS_PADRAO, help="nº de dobras do GroupKFold (por cliente)")
    p.add_argument("--saida", type=Path, default=DADOS / "rotulos_suspeitos.csv")
    args = p.parse_args(argv)

    if not args.rotulos.is_file():
        print(f"erro: arquivo não encontrado: {args.rotulos.name}")
        return 1
    linhas = ler_csv(args.rotulos)
    if not linhas:
        print("erro: rótulos vazios")
        return 1
    base = carregar_base(args.base)  # joblib é pickle: só artefato do próprio repo

    todas_saidas, resumo = [], {}
    for grupo in args.grupos:
        saida_grupo, info = suspeitos_do_grupo(linhas, grupo, base, args.dobras)
        todas_saidas += saida_grupo
        resumo[grupo] = info

    gravar_csv(args.saida, todas_saidas, COLUNAS_SAIDA)
    imprimir({"arquivo": args.saida.name, "grupos": resumo,
              "total_suspeitos": len(todas_saidas)})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
