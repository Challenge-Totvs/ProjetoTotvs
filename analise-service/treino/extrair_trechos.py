"""Etapa 1 do P8: extrai trechos (turno alvo + 2 turnos de contexto) das reuniões FORA do holdout.

    cd analise-service
    python treino/extrair_trechos.py --verificar                      # só os nomes das colunas e as contagens
    python treino/extrair_trechos.py                                   # dados_locais/corpus.csv -> dados_locais/trechos.csv
    python treino/extrair_trechos.py --corpus dados_locais/X.csv --col-reuniao ID --col-cliente CODT --col-texto TRANSCRICAO

Exclui as reuniões do `holdout_reunioes.csv` E todas as reuniões dos clientes (CODT) que aparecem nele: nenhum cliente
do conjunto ouro entra no treino. Divide cada transcrição por turno com a regra do SDD §5.2 (`[LOCUTOR n]`). Imprime só
contagens; o texto fica em `dados_locais/` (ignorado pelo git).
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from treino.comum import (  # noqa: E402
    DADOS, cabecalho_corpus, cabecalho_csv, dividir_turnos, gravar_csv, imprimir, ler_corpus, ler_csv,
)

CONTEXTO = 2  # turnos anteriores ao alvo
COLUNAS_SAIDA = ["id", "reuniao", "cliente", "turno", "locutor", "texto", "contexto"]
SEPARADOR_CONTEXTO = " || "


def _conjunto_holdout(holdout: list[dict], col_reuniao: str, col_cliente: str) -> tuple[set[str], set[str]]:
    reunioes = {(linha.get(col_reuniao) or "").strip() for linha in holdout} - {""}
    clientes = {(linha.get(col_cliente) or "").strip() for linha in holdout} - {""}
    return reunioes, clientes


def extrair(corpus: list[dict], holdout: list[dict], col_reuniao: str, col_cliente: str, col_texto: str,
            col_holdout: str | None = None) -> tuple[list[dict], dict]:
    """Devolve (trechos, contagens). `col_holdout`: coluna da reunião no holdout (padrão: a mesma do corpus)."""
    for nome in (col_reuniao, col_cliente, col_texto):
        if corpus and nome not in corpus[0]:
            raise SystemExit(f"erro: coluna {nome!r} não existe no corpus (use --verificar para ver os nomes)")
    reunioes_holdout, clientes_holdout = _conjunto_holdout(holdout, col_holdout or col_reuniao, col_cliente)
    # Clientes do holdout também vêm do próprio corpus (o holdout pode ter só a coluna da reunião).
    for linha in corpus:
        if (linha.get(col_reuniao) or "").strip() in reunioes_holdout:
            clientes_holdout.add((linha.get(col_cliente) or "").strip())
    clientes_holdout.discard("")

    trechos: list[dict] = []
    contagem = {"reunioes_no_corpus": len(corpus), "reunioes_excluidas_holdout": 0, "reunioes_usadas": 0,
                "reunioes_sem_turnos": 0, "reunioes_duplicadas_ignoradas": 0, "clientes_no_holdout": len(clientes_holdout), "trechos": 0}
    vistos: dict[str, dict] = {}
    for linha in corpus:
        reuniao = (linha.get(col_reuniao) or "").strip()
        cliente = (linha.get(col_cliente) or "").strip()
        if reuniao in reunioes_holdout or cliente in clientes_holdout:
            contagem["reunioes_excluidas_holdout"] += 1
            continue
        if reuniao in vistos:
            if linha != vistos[reuniao]:  # repetição idêntica é só ignorada; conteúdo diferente não dá para escolher
                raise SystemExit(f"erro: reunião repetida no corpus com conteúdo diferente (linha de dados {len(vistos) + 1})")
            contagem["reunioes_duplicadas_ignoradas"] += 1
            continue
        vistos[reuniao] = linha
        turnos = dividir_turnos(linha.get(col_texto) or "")
        if not turnos:
            contagem["reunioes_sem_turnos"] += 1
            continue
        contagem["reunioes_usadas"] += 1
        for i, (locutor, texto) in enumerate(turnos):
            contexto = SEPARADOR_CONTEXTO.join(t for _, t in turnos[max(0, i - CONTEXTO):i])
            trechos.append({"id": f"{reuniao}:{i + 1}", "reuniao": reuniao, "cliente": cliente, "turno": i + 1,
                            "locutor": locutor, "texto": texto, "contexto": contexto})
    contagem["trechos"] = len(trechos)
    return trechos, contagem


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Etapa 1 do P8: trechos por turno, fora do holdout (só contagens).")
    p.add_argument("--corpus", type=Path, default=DADOS / "corpus.csv", help="CSV do corpus (padrão dados_locais/corpus.csv)")
    p.add_argument("--holdout", type=Path, default=DADOS / "holdout_reunioes.csv")
    p.add_argument("--saida", type=Path, default=DADOS / "trechos.csv")
    p.add_argument("--col-reuniao", default="reuniao", help="coluna com o id da reunião (corpus e holdout)")
    p.add_argument("--col-cliente", default="CODT", help="coluna do cliente/lead (CODT)")
    p.add_argument("--col-texto", default="transcricao", help="coluna com a transcrição")
    p.add_argument("--col-holdout", default=None, help="coluna da reunião no holdout, se o nome for outro")
    p.add_argument("--verificar", action="store_true", help="imprime só os nomes das colunas e as contagens")
    args = p.parse_args(argv)

    for caminho in (args.corpus, args.holdout):
        if not caminho.is_file():
            print(f"erro: arquivo não encontrado: {caminho.name}")
            return 1
    if args.verificar:
        resumo = {}
        for rotulo, caminho, ler in (("corpus", args.corpus, cabecalho_corpus), ("holdout", args.holdout, cabecalho_csv)):
            colunas, linhas = ler(caminho)
            resumo[rotulo] = {"colunas": colunas, "linhas": linhas}
        imprimir(resumo)
        return 0

    descarte: dict = {}
    trechos, contagem = extrair(ler_corpus(args.corpus, descarte), ler_csv(args.holdout), args.col_reuniao, args.col_cliente,
                                args.col_texto, args.col_holdout)
    gravar_csv(args.saida, trechos, COLUNAS_SAIDA)
    imprimir({"saida": args.saida.name, **contagem, **descarte})
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
