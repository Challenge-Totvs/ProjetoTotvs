"""Amostra NOVA para o conjunto ouro, sem tocar nos 300 trechos já separados.

    cd analise-service
    python treino/amostra_ouro.py --corpus dados_locais/ANON_nome_transcricao.csv --col-reuniao ID_MEETING --col-texto ANON_TRANSCRICAO

Sorteia trechos SÓ das reuniões do holdout (`holdout_reunioes.csv`) que NÃO deram origem aos 300 (`no_ouro` = 0/vazio).
As planilhas do ouro não são abertas nem alteradas. Desenho do escopo §3: até 8 trechos por padrão (no máximo 1 por
reunião em cada padrão), 80 candidatos a interesse e 110 negativos sem acerto de regra; semente fixa. Turno alvo com
menos de `--min-caracteres` fica de fora. Grava em `dados_locais/`:
- `amostra_ouro_2.csv`: layout da aba Rotular (sem o estrato, em ordem embaralhada) para rotular;
- `amostra_ouro_2_mapa.csv`: ID -> trecho, reunião, cliente, turno e estrato (fora da vista do rotulador).
Não sobrescreve arquivo existente. Imprime só contagens. As reuniões do holdout nunca entram no treino
(`extrair_trechos.py` as exclui); se o `trechos.csv` existir, o script confere isso e para se houver mistura.
"""
import argparse
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.engines.regras_engine import EXPRESSAO_INTERESSE, EXPRESSOES, dobrar  # noqa: E402
from treino.comum import DADOS, dividir_turnos, gravar_csv, imprimir, ler_corpus, ler_csv, normalizar_sim_nao  # noqa: E402

POR_PADRAO, INTERESSE, NEGATIVOS = 8, 80, 110  # escopo §3 (o primeiro lote teve 110 + 80 + 110 = 300)
MIN_CARACTERES = 20  # [proposta] turno curto demais ("Ok.") não ajuda a medir
PREFIXO_ID = "N"  # os 300 usam G (e o reteste, R): não há colisão
COLUNAS_ROTULAR = ["ID", "contexto (2 turnos antes)", "contexto (turno anterior)", "TRECHO ALVO", "padrao_1", "padrao_2",
                   "interesse", "duvida", "motivo_duvida", "observacao"]
COLUNAS_MAPA = ["ID", "trecho", "reuniao", "cliente", "turno", "estrato"]


def reunioes_do_pool(holdout: list[dict], col_reuniao: str, col_cliente: str) -> tuple[set[str], set[str], dict]:
    """(reuniões do pool, reuniões dos 300, contagens): pool = holdout sem as reuniões marcadas em `no_ouro`."""
    if holdout and "no_ouro" not in holdout[0]:
        raise SystemExit("erro: holdout sem a coluna 'no_ouro': não dá para saber de onde saíram os 300")
    do_ouro = {(x.get(col_reuniao) or "").strip() for x in holdout if normalizar_sim_nao(x.get("no_ouro")) is not False}
    todas = {(x.get(col_reuniao) or "").strip() for x in holdout} - {""}
    clientes = {(x.get(col_cliente) or "").strip() for x in holdout} - {""}
    return todas - do_ouro, do_ouro, {"reunioes_no_holdout": len(todas), "reunioes_dos_300": len(do_ouro & todas),
                                      "clientes_no_holdout": len(clientes)}


def trechos_do_pool(corpus: list[dict], pool: set[str], col_reuniao: str, col_cliente: str, col_texto: str,
                    min_caracteres: int) -> list[dict]:
    trechos, vistas = [], set()
    for linha in corpus:
        reuniao = (linha.get(col_reuniao) or "").strip()
        if reuniao not in pool or reuniao in vistas:
            continue
        vistas.add(reuniao)
        turnos = dividir_turnos(linha.get(col_texto) or "")
        for i, (_, texto) in enumerate(turnos):
            if len(texto.strip()) < min_caracteres:
                continue
            dobrado = dobrar(texto)
            trechos.append({
                "trecho": f"{reuniao}:{i + 1}", "reuniao": reuniao, "cliente": (linha.get(col_cliente) or "").strip(),
                "turno": i + 1, "texto": texto, "ctx2": turnos[i - 2][1] if i >= 2 else "",
                "ctx1": turnos[i - 1][1] if i >= 1 else "",
                "padroes": {p for p, e in EXPRESSOES.items() if e.search(dobrado)},
                "interesse": bool(EXPRESSAO_INTERESSE.search(dobrado)),
            })
    return trechos


def sortear(trechos: list[dict], por_padrao: int, n_interesse: int, n_negativos: int, semente: int) -> list[dict]:
    """Estratos na ordem do escopo: padrões (no máximo 1 por reunião em cada padrão), interesse, negativos."""
    ordem = list(trechos)
    random.Random(semente).shuffle(ordem)
    escolhidos: dict[str, dict] = {}

    def pegar(filtro, n: int, estrato: str, uma_por_reuniao: bool = False) -> None:
        reunioes: set[str] = set()
        pegos = 0
        for t in ordem:
            if pegos >= n:
                return
            if t["trecho"] in escolhidos or (uma_por_reuniao and t["reuniao"] in reunioes) or not filtro(t):
                continue
            escolhidos[t["trecho"]] = {**t, "estrato": estrato}
            reunioes.add(t["reuniao"])
            pegos += 1

    for padrao in sorted(EXPRESSOES):
        pegar(lambda t, p=padrao: p in t["padroes"], por_padrao, f"padrao:{padrao}", uma_por_reuniao=True)
    pegar(lambda t: t["interesse"], n_interesse, "interesse")
    pegar(lambda t: not t["padroes"] and not t["interesse"], n_negativos, "negativo")
    saida = list(escolhidos.values())
    random.Random(semente + 1).shuffle(saida)  # a ordem da planilha não revela o estrato
    for i, t in enumerate(saida):
        t["ID"] = f"{PREFIXO_ID}{i + 1:03d}"
    return saida


def contagens(amostra: list[dict], por_padrao: int) -> dict:
    por_estrato: dict[str, int] = {}
    for t in amostra:
        por_estrato[t["estrato"]] = por_estrato.get(t["estrato"], 0) + 1
    faltam = {p: por_padrao - por_estrato.get(f"padrao:{p}", 0) for p in sorted(EXPRESSOES)
              if por_estrato.get(f"padrao:{p}", 0) < por_padrao}
    return {"amostra": len(amostra), "reunioes_na_amostra": len({t["reuniao"] for t in amostra}),
            "por_estrato": dict(sorted(por_estrato.items())), "padroes_abaixo_da_meta": faltam}


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Amostra nova para o ouro, só do holdout e fora dos 300 (só contagens).")
    p.add_argument("--corpus", type=Path, default=DADOS / "corpus.csv")
    p.add_argument("--holdout", type=Path, default=DADOS / "holdout_reunioes.csv")
    p.add_argument("--trechos", type=Path, default=DADOS / "trechos.csv", help="conferência: nada do holdout no treino")
    p.add_argument("--saida", type=Path, default=DADOS / "amostra_ouro_2.csv")
    p.add_argument("--col-reuniao", default="reuniao", help="coluna da reunião (corpus e holdout)")
    p.add_argument("--col-cliente", default="CODT")
    p.add_argument("--col-texto", default="transcricao")
    p.add_argument("--por-padrao", type=int, default=POR_PADRAO)
    p.add_argument("--interesse", type=int, default=INTERESSE)
    p.add_argument("--negativos", type=int, default=NEGATIVOS)
    p.add_argument("--min-caracteres", type=int, default=MIN_CARACTERES)
    p.add_argument("--semente", type=int, default=42)
    args = p.parse_args(argv)

    mapa = args.saida.with_name(args.saida.stem + "_mapa.csv")
    for caminho in (args.corpus, args.holdout):
        if not caminho.is_file():
            print(f"erro: arquivo não encontrado: {caminho.name}")
            return 1
    if args.saida.name.startswith("ouro_rotulador") or args.saida.name.startswith("ouro_reteste"):
        p.error("--saida não pode ter o nome de uma planilha do ouro")
    for caminho in (args.saida, mapa):
        if caminho.exists():
            print(f"erro: {caminho.name} já existe; não sobrescrevo (apague ou use --saida)")
            return 1

    pool, do_ouro, resumo = reunioes_do_pool(ler_csv(args.holdout), args.col_reuniao, args.col_cliente)
    if args.trechos.is_file():
        no_treino = {x.get("reuniao", "") for x in ler_csv(args.trechos)} & (pool | do_ouro)
        if no_treino:
            raise SystemExit(f"erro: {len(no_treino)} reunião(ões) do holdout no trechos.csv do treino")
        resumo["reunioes_do_holdout_no_treino"] = 0
    trechos = trechos_do_pool(ler_corpus(args.corpus), pool, args.col_reuniao, args.col_cliente, args.col_texto,
                              args.min_caracteres)
    amostra = sortear(trechos, args.por_padrao, args.interesse, args.negativos, args.semente)
    gravar_csv(args.saida, [{"ID": t["ID"], "contexto (2 turnos antes)": t["ctx2"], "contexto (turno anterior)": t["ctx1"],
                             "TRECHO ALVO": t["texto"]} for t in amostra], COLUNAS_ROTULAR)
    gravar_csv(mapa, sorted(amostra, key=lambda t: t["ID"]), COLUNAS_MAPA)
    imprimir({"saida": args.saida.name, "mapa": mapa.name, **resumo, "reunioes_no_pool": len(pool),
              "trechos_no_pool": len(trechos), **contagens(amostra, args.por_padrao)})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
