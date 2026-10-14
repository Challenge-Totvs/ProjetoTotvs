"""Experimento (sem deploy): embeddings de frase + regressão logística vs. TF-IDF + LR atual.

    python treino/experimentos/embeddings_vs_tfidf.py --rotulos <...>/dados_locais/rotulos_fracos.csv

Treino: trechos com `fonte` = regra. Avaliação: trechos com `fonte` = llm. Quase todo cliente tem trechos das duas
fontes, então a separação por cliente é por GroupKFold: a cada dobra, os clientes avaliados (trechos da LLM) ficam
FORA do treino (trechos da regra). Cada trecho da LLM é avaliado uma vez, por um modelo que não viu o cliente dele.
O baseline é `clone` do Pipeline de app/modelos/ (mesmos hiperparâmetros); o embedding usa LR com os mesmos
`class_weight`, `max_iter` e `random_state`. Só lê app/ e o CSV; não grava nada fora de --saida. Imprime só
contagens e métricas (nunca texto de trecho).
"""
import argparse
import csv
import json
import sys
import tempfile
import time
import warnings
from pathlib import Path

import joblib
import numpy as np
from sklearn.base import clone
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_fscore_support
from sklearn.model_selection import GroupKFold



RAIZ = Path(__file__).resolve().parent.parent.parent
CAMINHO_MODELO_ATUAL = RAIZ / "app" / "modelos" / "classificador_risco.joblib"
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))  # textos do corpus passam de 128 KB


def ler_csv(caminho: Path) -> list[dict[str, str]]:  # não importa treino.comum: ele puxa o app (fastapi)
    with open(caminho, encoding="utf-8-sig", errors="replace", newline="") as f:
        return list(csv.DictReader(f))

GRUPOS = ("risco", "oportunidade", "interesse")
MODELO_EMB = "paraphrase-multilingual-MiniLM-L12-v2"
DOBRAS = 5


def codificar(modelo, textos: list[str], lote: int = 128) -> np.ndarray:
    únicos = list(dict.fromkeys(textos))  # muitos trechos curtos se repetem ("tudo bem?")
    vetores = modelo.encode(únicos, batch_size=lote, convert_to_numpy=True, normalize_embeddings=True,
                            show_progress_bar=False)
    posicao = {t: i for i, t in enumerate(únicos)}
    return vetores[[posicao[t] for t in textos]].astype(np.float32)


def metricas(y, pred, score) -> dict:
    p, r, f, _ = precision_recall_fscore_support(y, pred, average="binary", zero_division=0)
    ap = average_precision_score(y, score) if sum(y) else float("nan")
    return {"precisao": p, "revocacao": r, "f1": f, "pr_auc": ap, "positivos": int(sum(y))}


def lr_emb(base) -> LogisticRegression:
    clf = base.steps[-1][1]
    return LogisticRegression(class_weight=clf.class_weight, max_iter=clf.max_iter, random_state=clf.random_state)


def tamanho_mb(obj) -> float:
    with tempfile.TemporaryDirectory() as t:
        joblib.dump(obj, Path(t) / "m.joblib")
        return (Path(t) / "m.joblib").stat().st_size / 1e6


def pasta_mb(caminho: Path) -> float:
    return sum(f.stat().st_size for f in caminho.rglob("*") if f.is_file()) / 1e6


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--rotulos", type=Path, required=True)
    p.add_argument("--saida", type=Path, required=True, help="JSON com as métricas (fora do repo)")
    p.add_argument("--cache", type=Path, help="npz com embeddings já calculados (fora do repo)")
    args = p.parse_args(argv)
    warnings.filterwarnings("ignore")

    linhas = ler_csv(args.rotulos)
    tr = [x for x in linhas if x["fonte"] == "regra"]
    av = [x for x in linhas if x["fonte"] == "llm"]
    base = joblib.load(CAMINHO_MODELO_ATUAL)  # artefato do próprio repo
    clientes = np.array([x["cliente"] for x in tr + av])
    print(f"treino(regra)={len(tr)} avaliacao(llm)={len(av)} clientes_av={len(set(x['cliente'] for x in av))} "
          f"clientes_em_comum={len(set(x['cliente'] for x in av) & set(x['cliente'] for x in tr))}", flush=True)

    from sentence_transformers import SentenceTransformer

    modelo = SentenceTransformer(MODELO_EMB, device="cpu")
    t_tr, t_av = [x["texto"] for x in tr], [x["texto"] for x in av]
    if args.cache and args.cache.is_file():
        z = np.load(args.cache)
        e_tr, e_av, seg_enc_tr = z["tr"], z["av"], float(z["seg_tr"])
    else:
        t0 = time.perf_counter()
        e_tr = codificar(modelo, t_tr)
        seg_enc_tr = time.perf_counter() - t0
        e_av = codificar(modelo, t_av)
        if args.cache:
            np.savez(args.cache, tr=e_tr, av=e_av, seg_tr=seg_enc_tr)
    print(f"embeddings: dim={e_tr.shape[1]} codificar_treino={seg_enc_tr:.0f}s", flush=True)

    g_tr = np.array([x["cliente"] for x in tr])
    g_av = np.array([x["cliente"] for x in av])
    clientes_av = np.array(sorted(set(g_av)))
    dobra_do_cliente = {}
    # GroupKFold sobre os clientes avaliados, ponderando pelo nº de trechos da LLM (balanceia as dobras).
    for i, (_, idx) in enumerate(GroupKFold(DOBRAS).split(g_av, groups=g_av)):
        for c in set(g_av[idx]):
            dobra_do_cliente[c] = i
    f_av = np.array([dobra_do_cliente[c] for c in g_av])

    res = {g: {"tfidf": {}, "emb": {}} for g in GRUPOS}
    tempos = {"tfidf_treino_s": 0.0, "emb_treino_s": 0.0, "n_fits": 0}
    pred = {(g, m): np.zeros(len(av), dtype=int) for g in GRUPOS for m in ("tfidf", "emb")}
    score = {(g, m): np.zeros(len(av)) for g in GRUPOS for m in ("tfidf", "emb")}
    n_treino_dobra = []
    for d in range(DOBRAS):
        fora = np.array([dobra_do_cliente.get(c) == d for c in g_tr])  # treino de clientes que serão avaliados na dobra d
        # clientes de fora dos 245 avaliados ficam sempre no treino
        usa = ~fora
        sel_av = f_av == d
        n_treino_dobra.append(int(usa.sum()))
        for g in GRUPOS:
            y_tr = np.array([1 if x[g] == "1" else 0 for x in tr])[usa]
            if len(set(y_tr)) < 2:
                raise SystemExit(f"erro: {g} sem as duas classes na dobra {d}")
            tx = [t for t, u in zip(t_tr, usa) if u]
            t0 = time.perf_counter()
            m1 = clone(base).fit(tx, y_tr)
            tempos["tfidf_treino_s"] += time.perf_counter() - t0
            t0 = time.perf_counter()
            m2 = lr_emb(base).fit(e_tr[usa], y_tr)
            tempos["emb_treino_s"] += time.perf_counter() - t0
            tempos["n_fits"] += 1
            ta = [t for t, s in zip(t_av, sel_av) if s]
            pred[(g, "tfidf")][sel_av] = m1.predict(ta)
            score[(g, "tfidf")][sel_av] = m1.predict_proba(ta)[:, 1]
            pred[(g, "emb")][sel_av] = m2.predict(e_av[sel_av])
            score[(g, "emb")][sel_av] = m2.predict_proba(e_av[sel_av])[:, 1]
        print(f"dobra {d}: treino={int(usa.sum())} avaliacao={int(sel_av.sum())}", flush=True)

    for g in GRUPOS:
        y = np.array([1 if x[g] == "1" else 0 for x in av])
        for m in ("tfidf", "emb"):
            res[g][m] = metricas(y, pred[(g, m)], score[(g, m)])

    # Modelos finais com todo o treino (tamanho e latência de inferência).
    y_full = {g: np.array([1 if x[g] == "1" else 0 for x in tr]) for g in GRUPOS}
    t0 = time.perf_counter()
    final_tfidf = clone(base).fit(t_tr, y_full["risco"])
    seg_final_tfidf = time.perf_counter() - t0
    final_emb = lr_emb(base).fit(e_tr, y_full["risco"])
    amostra = t_av[:200]
    inf = {}
    for rot, fn in (
        ("tfidf", lambda ts: final_tfidf.predict_proba(ts)),
        ("emb", lambda ts: final_emb.predict_proba(modelo.encode(ts, batch_size=32, normalize_embeddings=True,
                                                                  show_progress_bar=False))),
    ):
        fn(amostra[:8])  # aquecimento
        t0 = time.perf_counter()
        for t in amostra:
            fn([t])
        um = (time.perf_counter() - t0) / len(amostra) * 1000
        t0 = time.perf_counter()
        fn(amostra)
        lote = (time.perf_counter() - t0) / len(amostra) * 1000
        inf[rot] = {"ms_por_trecho_1_a_1": um, "ms_por_trecho_lote_200": lote}
    with tempfile.TemporaryDirectory() as t:
        modelo.save(str(Path(t) / "st"))
        mb_modelo_emb = pasta_mb(Path(t) / "st")
    tam = {"tfidf_pipeline_mb": tamanho_mb(final_tfidf), "emb_lr_mb": tamanho_mb(final_emb),
           "emb_encoder_mb": mb_modelo_emb, "tfidf_vocab": len(final_tfidf.steps[0][1].vocabulary_)}

    out = {"dados": {"treino": len(tr), "avaliacao": len(av), "dobras": DOBRAS, "treino_por_dobra": n_treino_dobra,
                     "encoder": MODELO_EMB, "max_seq_length": modelo.max_seq_length},
           "metricas": res,
           "tempo": {**tempos, "tfidf_treino_s_por_fit": tempos["tfidf_treino_s"] / tempos["n_fits"],
                     "emb_lr_treino_s_por_fit": tempos["emb_treino_s"] / tempos["n_fits"],
                     "emb_codificar_treino_s": seg_enc_tr, "tfidf_fit_completo_s": seg_final_tfidf},
           "inferencia": inf, "tamanho": tam}
    args.saida.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
