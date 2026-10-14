"""Etapa 5 do P8: portão de qualidade. Candidato × modelo/filtro atual no conjunto ouro, por GRUPO.

    cd analise-service
    python treino/portao.py                                  # último candidato em dados_locais/candidatos/
    python treino/portao.py --candidato dados_locais/candidatos/2026-10-14

Grupos (trechos com `duvida` ficam de fora):
- risco: classificador atual × candidato de risco, os dois com `LIMIAR_RISCO` do motor local;
- interesse: filtro atual (palavra-chave v2 E risco do atual < `LIMIAR_INTERESSE`) × candidato de interesse com
  `LIMIAR_P_INTERESSE`;
- oportunidade: expressões nos dois lados (não há candidato): só informativo.
Por grupo: precisão, revocação (com IC95% de Wilson), F1, matriz de confusão, baseline Dummy (sem sinal) e IC95% por
bootstrap PAREADO da DIFERENÇA de F1 e da diferença de precisão (candidato − atual), além da contagem de trechos em
que atual e candidato discordam. Aprova um candidato se F1 >= atual E o IC95% da diferença de precisão não fica
inteiramente abaixo de -0,02 E o IC95% da diferença de F1 não fica inteiramente abaixo de zero. Ouro parcial (ou sem
`ouro_final.json`) => nunca recomenda promoção. Por padrão os números são só indicativos (~8 trechos cada).

Escreve `docs/evidencias/portao-<data>.md` (só métricas) e imprime o comando de promoção MANUAL de cada candidato
aprovado, ou "REPROVADO: mantém o atual". Nunca imprime texto de trecho.
"""
import argparse
import datetime as dt
import json
import sys
import unicodedata
from pathlib import Path
from typing import Any, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.engines.modelo_local_engine import LIMIAR_INTERESSE, LIMIAR_P_INTERESSE, LIMIAR_RISCO  # noqa: E402
from app.engines.regras_engine import EXPRESSAO_INTERESSE, EXPRESSOES, TIPO_DO_PADRAO, dobrar  # noqa: E402
from treino.comum import CAMINHO_MODELO_ATUAL, DADOS, EVIDENCIAS, PADROES, imprimir, ler_csv  # noqa: E402

QUEDA_MAXIMA_PRECISAO = 0.02
REPETICOES_BOOTSTRAP = 2000
DESTINO_PROMOCAO = {"risco": "app/modelos/classificador_risco.joblib",
                    "interesse": "app/modelos/classificador_interesse.joblib"}


# ------------------------------------------------------------------ métricas

def intervalo_wilson(positivos: int, n: int, z: float = 1.96) -> tuple[float, float]:
    """IC95% de Wilson para uma proporção (positivos/n). (0.0, 0.0) se n == 0."""
    if n == 0:
        return 0.0, 0.0
    p = positivos / n
    denom = 1 + z * z / n
    centro = p + z * z / (2 * n)
    margem = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    lo = (centro - margem) / denom
    hi = (centro + margem) / denom
    return round(max(0.0, lo), 4), round(min(1.0, hi), 4)


def metricas(y: Sequence[int], pred: Sequence[int]) -> dict:
    tp = sum(1 for a, b in zip(y, pred) if a and b)
    fp = sum(1 for a, b in zip(y, pred) if not a and b)
    fn = sum(1 for a, b in zip(y, pred) if a and not b)
    tn = sum(1 for a, b in zip(y, pred) if not a and not b)
    precisao = tp / (tp + fp) if tp + fp else 0.0
    revocacao = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precisao * revocacao / (precisao + revocacao) if precisao + revocacao else 0.0
    return {"n": len(y), "positivos": sum(y), "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precisao": round(precisao, 4), "revocacao": round(revocacao, 4), "f1": round(f1, 4),
            "wilson_precisao": intervalo_wilson(tp, tp + fp), "wilson_revocacao": intervalo_wilson(tp, tp + fn)}


def _f1(y, p) -> float:
    tp = int((y & p).sum())
    fp = int((~y & p).sum())
    fn = int((y & ~p).sum())
    return 2 * tp / (2 * tp + fp + fn) if tp else 0.0


def _precisao(y, p) -> float:
    tp = int((y & p).sum())
    fp = int((~y & p).sum())
    return tp / (tp + fp) if tp + fp else 0.0


def _bootstrap_diferenca(estatistica, y: Sequence[int], atual: Sequence[int], candidato: Sequence[int],
                         repeticoes: int = REPETICOES_BOOTSTRAP, semente: int = 42) -> tuple[float, float]:
    """Bootstrap pareado (mesma reamostragem para os dois lados) da diferença estatistica(candidato) − estatistica(atual)."""
    import numpy as np

    y_, a_, c_ = (np.asarray(v, dtype=bool) for v in (y, atual, candidato))
    if len(y_) == 0:
        return 0.0, 0.0
    rng = np.random.default_rng(semente)
    difs = np.empty(repeticoes)
    for i in range(repeticoes):
        idx = rng.integers(0, len(y_), len(y_))
        difs[i] = estatistica(y_[idx], c_[idx]) - estatistica(y_[idx], a_[idx])
    return round(float(np.percentile(difs, 2.5)), 4), round(float(np.percentile(difs, 97.5)), 4)


def ic95_diferenca_f1(y: Sequence[int], atual: Sequence[int], candidato: Sequence[int],
                      repeticoes: int = REPETICOES_BOOTSTRAP, semente: int = 42) -> tuple[float, float]:
    """Bootstrap pareado da diferença F1(candidato) − F1(atual)."""
    return _bootstrap_diferenca(_f1, y, atual, candidato, repeticoes, semente)


def ic95_diferenca_precisao(y: Sequence[int], atual: Sequence[int], candidato: Sequence[int],
                            repeticoes: int = REPETICOES_BOOTSTRAP, semente: int = 42) -> tuple[float, float]:
    """Bootstrap pareado da diferença precisão(candidato) − precisão(atual)."""
    return _bootstrap_diferenca(_precisao, y, atual, candidato, repeticoes, semente)


def discordancia(atual: Sequence[int], candidato: Sequence[int]) -> int:
    """Quantos trechos atual e candidato classificam de forma diferente."""
    return sum(1 for a, c in zip(atual, candidato) if bool(a) != bool(c))


def linha_de_base_dummy(y: Sequence[int], semente: int = 42) -> dict:
    """Baseline sem sinal (DummyClassifier estratificado pela distribuição de classes do próprio y)."""
    from sklearn.dummy import DummyClassifier

    y_lista = list(y)
    clf = DummyClassifier(strategy="stratified", random_state=semente)
    x_vazio = [[0]] * len(y_lista)
    clf.fit(x_vazio, y_lista)
    pred = clf.predict(x_vazio)
    return metricas(y_lista, [int(v) for v in pred])


def suficiencia(candidato: dict | None, minimo: int | None, positivos_minimos: int) -> bool:
    """Ouro parcial vale como suficiente só com --ouro-minimo (decisão humana) e tamanho/positivos mínimos no grupo."""
    if minimo is None or not candidato:
        return False
    return candidato.get("n", 0) >= minimo and candidato.get("positivos", 0) >= positivos_minimos


def decidir(atual: dict, candidato: dict, ic_f1: tuple[float, float],
           ic_precisao: tuple[float, float]) -> tuple[bool, list[str]]:
    motivos = []
    if candidato["positivos"] == 0:
        return False, ["sem positivos no ouro: não dá para decidir"]
    if candidato["f1"] < atual["f1"]:
        motivos.append(f"F1 {candidato['f1']} < atual {atual['f1']}")
    if ic_precisao[1] < -QUEDA_MAXIMA_PRECISAO:
        motivos.append(f"IC95% da diferença de precisão inteiramente abaixo de -{QUEDA_MAXIMA_PRECISAO} {list(ic_precisao)}")
    if ic_f1[1] < 0:
        motivos.append(f"IC95% da diferença de F1 inteiramente abaixo de zero {list(ic_f1)}")
    return not motivos, motivos


# ------------------------------------------------------------------ previsões

def _nfc(texto: str) -> str:
    return unicodedata.normalize("NFC", texto).strip()


def regex_do_tipo(texto: str, tipo: str) -> bool:
    dobrado = dobrar(texto)
    return any(EXPRESSOES[p].search(dobrado) for p in EXPRESSOES if TIPO_DO_PADRAO[p] == tipo)


def avaliar(ouro: list[dict], atual: Any, cand_risco: Any, cand_interesse: Any, repeticoes: int = REPETICOES_BOOTSTRAP) -> dict:
    linhas = [x for x in ouro if x.get("duvida") != "1"]
    textos = [_nfc(x["texto"]) for x in linhas]
    p_atual = atual.predict_proba(textos)[:, 1]
    p_risco = cand_risco.predict_proba(textos)[:, 1]
    p_interesse = cand_interesse.predict_proba(textos)[:, 1]
    grupos: dict[str, dict] = {}

    y = [int(x["risco"] == "1") for x in linhas]
    a = [int(p >= LIMIAR_RISCO) for p in p_atual]
    c = [int(p >= LIMIAR_RISCO) for p in p_risco]
    grupos["risco"] = {"atual": metricas(y, a), "candidato": metricas(y, c),
                       "ic95": ic95_diferenca_f1(y, a, c, repeticoes),
                       "ic95_precisao": ic95_diferenca_precisao(y, a, c, repeticoes),
                       "discordancia": discordancia(a, c), "dummy": linha_de_base_dummy(y),
                       "referencia_regex": metricas(y, [int(regex_do_tipo(t, "risco")) for t in textos])}

    com = [i for i, x in enumerate(linhas) if x.get("interesse") in ("0", "1")]
    y = [int(linhas[i]["interesse"] == "1") for i in com]
    a = [int(bool(EXPRESSAO_INTERESSE.search(dobrar(textos[i]))) and p_atual[i] < LIMIAR_INTERESSE) for i in com]
    c = [int(p_interesse[i] >= LIMIAR_P_INTERESSE) for i in com]
    grupos["interesse"] = {"atual": metricas(y, a), "candidato": metricas(y, c),
                           "ic95": ic95_diferenca_f1(y, a, c, repeticoes),
                           "ic95_precisao": ic95_diferenca_precisao(y, a, c, repeticoes),
                           "discordancia": discordancia(a, c), "dummy": linha_de_base_dummy(y)}

    y = [int(x["oportunidade"] == "1") for x in linhas]
    r = [int(regex_do_tipo(t, "oportunidade")) for t in textos]
    grupos["oportunidade"] = {"atual": metricas(y, r), "candidato": None, "ic95": None}

    for nome in ("risco", "interesse"):
        g = grupos[nome]
        g["aprovado"], g["motivos"] = decidir(g["atual"], g["candidato"], g["ic95"], g["ic95_precisao"])

    por_padrao = {}
    for padrao in PADROES:
        dentro = [i for i, x in enumerate(linhas) if padrao in (x.get("padrao_1"), x.get("padrao_2"))]
        acertos = [i for i, t in enumerate(textos) if EXPRESSOES[padrao].search(dobrar(t))]
        por_padrao[padrao] = {"trechos": len(dentro), "regex_acerta": len(set(dentro) & set(acertos)),
                              "regex_alarme_falso": len(set(acertos) - set(dentro))}
    return {"trechos_avaliados": len(linhas), "trechos_com_duvida": len(ouro) - len(linhas), "grupos": grupos,
            "por_padrao": por_padrao}


# ------------------------------------------------------------------ relatório

def comando_promocao(nome: str, pasta: Path) -> str:
    origem = f"dados_locais/candidatos/{pasta.name}/{nome}.joblib"
    return f'Copy-Item "{origem}" "{DESTINO_PROMOCAO[nome]}"'


def _linha(rotulo: str, m: dict | None) -> str:
    if m is None:
        return f"| {rotulo} | — | — | — | — | — |"
    wp = m.get("wilson_precisao")
    wr = m.get("wilson_revocacao")
    matriz = f"tp={m.get('tp', '—')} fp={m.get('fp', '—')} fn={m.get('fn', '—')} tn={m.get('tn', '—')}"
    return (f"| {rotulo} | {m['precisao']} ({list(wp) if wp else '—'}) | {m['revocacao']} ({list(wr) if wr else '—'}) "
            f"| {m['f1']} | {m['positivos']}/{m['n']} | {matriz} |")


def escrever_relatorio(caminho: Path, resultado: dict, meta_ouro: dict, meta_candidato: dict, decisoes: dict) -> None:
    g = resultado["grupos"]
    linhas = [
        f"# Portão do modelo local — {resultado['data']}", "",
        "Só métricas; nenhum texto de trecho. Gerado por `treino/portao.py`.", "",
        f"- Candidato: `{meta_candidato.get('pasta', '?')}` (scikit-learn {meta_candidato.get('scikit_learn', '?')}, "
        f"dados sha256 `{str(meta_candidato.get('dados', {}).get('sha256', '?'))[:12]}`, "
        f"mudanças de hiperparâmetro: {len(meta_candidato.get('mudancas', []))})",
        f"- Ouro: modo **{meta_ouro.get('modo', 'desconhecido')}**, "
        f"**{'completo' if meta_ouro.get('completo') else 'PARCIAL'}**; kappas: "
        f"{json.dumps(meta_ouro.get('kappas', {}), ensure_ascii=False)}",
        f"- Trechos avaliados: {resultado['trechos_avaliados']} (fora por dúvida: {resultado['trechos_com_duvida']})",
        f"- Limiares: risco >= {LIMIAR_RISCO}; filtro atual de interesse = palavra-chave E risco < {LIMIAR_INTERESSE}; "
        f"candidato de interesse >= {LIMIAR_P_INTERESSE}",
    ]
    if meta_ouro.get("limitacao"):
        linhas.append(f"- Limitação: {meta_ouro['limitacao']}")
    linhas += ["", "## Por grupo", "",
               "| Grupo / lado | precisão (Wilson 95%) | revocação (Wilson 95%) | F1 | positivos/n | matriz de confusão |",
               "|---|---|---|---|---|---|"]
    for nome in ("risco", "interesse", "oportunidade"):
        linhas.append(_linha(f"{nome} — atual", g[nome]["atual"]))
        linhas.append(_linha(f"{nome} — candidato", g[nome]["candidato"]))
        if "dummy" in g[nome]:
            linhas.append(_linha(f"{nome} — baseline Dummy (sem sinal)", g[nome]["dummy"]))
    linhas.append(_linha("risco — referência: só regex", g["risco"]["referencia_regex"]))
    linhas += ["", "## Decisão", ""]
    for nome in ("risco", "interesse"):
        linhas.append(f"- **{nome}**: IC95% da diferença de F1 = {list(g[nome]['ic95'])}; "
                      f"IC95% da diferença de precisão = {list(g[nome]['ic95_precisao'])}; "
                      f"discordância atual×candidato = {g[nome]['discordancia']} trecho(s); {decisoes[nome]}")
        if g[nome]["motivos"]:
            linhas.append(f"  - motivos: {'; '.join(g[nome]['motivos'])}")
    linhas.append("- **oportunidade**: sem candidato (expressões nos dois lados); só informativo.")
    linhas += ["", "## Por padrão (APENAS INDICATIVO: ~8 trechos por padrão)", "",
               "| Padrão | trechos no ouro | regex acerta | regex alarme falso |", "|---|---|---|---|"]
    linhas += [f"| {p} | {v['trechos']} | {v['regex_acerta']} | {v['regex_alarme_falso']} |"
               for p, v in resultado["por_padrao"].items()]
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8")


def ultimo_candidato(raiz: Path) -> Path | None:
    pastas = sorted((p for p in raiz.iterdir() if (p / "metadata.json").is_file()), key=lambda p: p.stat().st_mtime) \
        if raiz.is_dir() else []
    return pastas[-1] if pastas else None


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Etapa 5 do P8: portão de qualidade (só métricas).")
    p.add_argument("--ouro", type=Path, default=DADOS / "ouro_final.csv")
    p.add_argument("--candidato", type=Path, default=None, help="pasta do candidato (padrão: o mais recente)")
    p.add_argument("--candidatos", type=Path, default=DADOS / "candidatos")
    p.add_argument("--atual", type=Path, default=CAMINHO_MODELO_ATUAL, help="classificador de risco em uso")
    p.add_argument("--relatorio", type=Path, default=None, help="padrão docs/evidencias/portao-<data>.md")
    p.add_argument("--repeticoes", type=int, default=REPETICOES_BOOTSTRAP)
    p.add_argument("--ouro-minimo", type=int, default=None,
                   help="aceita ouro PARCIAL como suficiente se o grupo tiver >= N trechos avaliados (decisão humana)")
    p.add_argument("--positivos-minimos", type=int, default=10,
                   help="com --ouro-minimo: positivos mínimos do grupo no ouro (padrão 10)")
    args = p.parse_args(argv)

    if not args.ouro.is_file():
        print(f"erro: arquivo não encontrado: {args.ouro.name}")
        return 1
    pasta = args.candidato or ultimo_candidato(args.candidatos)
    if pasta is None or not (pasta / "risco.joblib").is_file() or not (pasta / "interesse.joblib").is_file():
        print("erro: candidato não encontrado (rode treino/treinar.py)")
        return 1
    import joblib

    # joblib é pickle: só o artefato do repo e candidatos gerados por treino/treinar.py
    atual, cand_risco, cand_interesse = (joblib.load(c) for c in (args.atual, pasta / "risco.joblib",
                                                                  pasta / "interesse.joblib"))
    meta_ouro_arquivo = args.ouro.with_suffix(".json")
    meta_ouro = json.loads(meta_ouro_arquivo.read_text(encoding="utf-8")) if meta_ouro_arquivo.is_file() else {}
    meta_candidato = json.loads((pasta / "metadata.json").read_text(encoding="utf-8")) \
        if (pasta / "metadata.json").is_file() else {}

    resultado = avaliar(ler_csv(args.ouro), atual, cand_risco, cand_interesse, args.repeticoes)
    resultado["data"] = dt.date.today().isoformat()
    completo = bool(meta_ouro.get("completo"))
    decisoes, comandos = {}, []
    for nome in ("risco", "interesse"):
        grupo = resultado["grupos"][nome]
        suficiente = suficiencia(grupo["candidato"], args.ouro_minimo, args.positivos_minimos)
        if not grupo["aprovado"]:
            decisoes[nome] = "REPROVADO: mantém o atual"
        elif not completo and not suficiente:
            decisoes[nome] = "passou no ouro PARCIAL: NÃO promover até o ouro completo (mantém o atual)"
        elif not completo:
            decisoes[nome] = (f"APROVADO no ouro PARCIAL suficiente (>= {args.ouro_minimo} trechos e "
                              f">= {args.positivos_minimos} positivos): promoção manual liberada")
            comandos.append(comando_promocao(nome, pasta))
        else:
            decisoes[nome] = "APROVADO: promoção manual liberada"
            comandos.append(comando_promocao(nome, pasta))
    relatorio = args.relatorio or EVIDENCIAS / f"portao-{resultado['data']}.md"
    escrever_relatorio(relatorio, resultado, meta_ouro, meta_candidato, decisoes)
    imprimir({"candidato": pasta.name, "relatorio": relatorio.name, "ouro_completo": completo,
              "decisoes": decisoes, "grupos": {n: {k: v for k, v in g.items() if k != "motivos"}
                                               for n, g in resultado["grupos"].items()}})
    for nome, decisao in decisoes.items():
        print(f"{nome}: {decisao}")
    for comando in comandos:
        print(f"  promover (manual, a partir de analise-service/): {comando}")
    if any("interesse" in c for c in comandos):
        print("  depois de promover o interesse: acrescentar INTERESSE_MODELO=1 ao .env (só então ele liga)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
