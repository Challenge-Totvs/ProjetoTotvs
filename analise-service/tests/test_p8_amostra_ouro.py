"""P8 — amostra_ouro.py: amostra nova para o ouro, só do holdout e fora das reuniões dos 300. Tudo SINTÉTICO."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from sintetico_p8 import corpus, gravar
from treino import amostra_ouro, comum, extrair_trechos

RAIZ = Path(__file__).resolve().parent.parent
DOS_300 = {"R000", "R001", "R002"}  # no_ouro = 1
POOL = {"R003", "R004", "R005", "R006", "R007", "R008"}  # no holdout, no_ouro = 0


@pytest.fixture
def cenario(tmp_path):
    linhas = corpus(30)
    gravar(tmp_path / "corpus.csv", linhas)
    holdout = [{"reuniao": f"R{i:03d}", "CODT": f"C{i // 3:03d}", "no_ouro": "1" if f"R{i:03d}" in DOS_300 else "0"}
               for i in range(9)]
    comum.gravar_csv(tmp_path / "holdout.csv", holdout, ["reuniao", "CODT", "no_ouro"])
    trechos, _ = extrair_trechos.extrair(linhas, holdout, "reuniao", "CODT", "transcricao")
    comum.gravar_csv(tmp_path / "trechos.csv", trechos, extrair_trechos.COLUNAS_SAIDA)
    return tmp_path


def _rodar(pasta: Path, *extra) -> int:
    return amostra_ouro.main(["--corpus", str(pasta / "corpus.csv"), "--holdout", str(pasta / "holdout.csv"),
                              "--trechos", str(pasta / "trechos.csv"), "--saida", str(pasta / "amostra.csv"),
                              "--por-padrao", "2", "--interesse", "5", "--negativos", "6", "--min-caracteres", "5",
                              *extra])


def test_so_reunioes_do_holdout_fora_dos_300(cenario, capsys):
    assert _rodar(cenario) == 0
    mapa = comum.ler_csv(cenario / "amostra_mapa.csv")
    assert mapa and {x["reuniao"] for x in mapa} <= POOL
    assert not {x["reuniao"] for x in mapa} & DOS_300
    treino = {x["reuniao"] for x in comum.ler_csv(cenario / "trechos.csv")}
    assert not {x["reuniao"] for x in mapa} & treino  # nenhuma reunião do ouro entra no treino
    resumo = json.loads(capsys.readouterr().out)
    assert resumo["reunioes_dos_300"] == 3 and resumo["reunioes_no_pool"] == 6
    assert resumo["reunioes_do_holdout_no_treino"] == 0 and resumo["amostra"] == len(mapa)


def test_planilha_no_layout_rotular_sem_estrato_e_sem_rotulos(cenario):
    _rodar(cenario)
    planilha = comum.ler_csv(cenario / "amostra.csv")
    assert list(planilha[0]) == amostra_ouro.COLUNAS_ROTULAR and "estrato" not in planilha[0]
    assert all(x["padrao_1"] == x["interesse"] == x["duvida"] == x["motivo_duvida"] == "" for x in planilha)
    assert [x["ID"] for x in sorted(planilha, key=lambda x: x["ID"])][:2] == ["N001", "N002"]
    mapa = {x["ID"]: x for x in comum.ler_csv(cenario / "amostra_mapa.csv")}
    assert set(mapa) == {x["ID"] for x in planilha}


def test_estratos_respeitam_metas_e_uma_reuniao_por_padrao(cenario):
    _rodar(cenario)
    mapa = comum.ler_csv(cenario / "amostra_mapa.csv")
    por_estrato: dict[str, list[str]] = {}
    for x in mapa:
        por_estrato.setdefault(x["estrato"], []).append(x["reuniao"])
    for estrato, reunioes in por_estrato.items():
        if estrato.startswith("padrao:"):
            assert len(reunioes) <= 2 and len(set(reunioes)) == len(reunioes)
    assert len(por_estrato.get("interesse", [])) <= 5 and len(por_estrato.get("negativo", [])) <= 6
    assert len({x["trecho"] for x in mapa}) == len(mapa)  # nenhum trecho repetido


def test_deterministico_e_nunca_sobrescreve(cenario, capsys):
    _rodar(cenario)
    primeiro = (cenario / "amostra_mapa.csv").read_text(encoding="utf-8")
    assert _rodar(cenario) == 1 and "já existe" in capsys.readouterr().out
    (cenario / "amostra.csv").unlink()
    (cenario / "amostra_mapa.csv").unlink()
    _rodar(cenario)
    assert (cenario / "amostra_mapa.csv").read_text(encoding="utf-8") == primeiro


def test_saida_so_com_contagens(cenario, capsys):
    _rodar(cenario)
    saida = capsys.readouterr().out
    assert all(x["TRECHO ALVO"][:25] not in saida for x in comum.ler_csv(cenario / "amostra.csv"))


def test_holdout_sem_no_ouro_para(cenario):
    comum.gravar_csv(cenario / "holdout.csv", [{"reuniao": "R000", "CODT": "C000"}], ["reuniao", "CODT"])
    with pytest.raises(SystemExit, match="no_ouro"):
        _rodar(cenario)


def test_reuniao_do_holdout_no_treino_para(cenario):
    trechos = comum.ler_csv(cenario / "trechos.csv")
    trechos[0]["reuniao"] = "R004"
    comum.gravar_csv(cenario / "trechos.csv", trechos, extrair_trechos.COLUNAS_SAIDA)
    with pytest.raises(SystemExit, match="holdout"):
        _rodar(cenario)
    assert not (cenario / "amostra.csv").exists()


def test_nao_grava_com_nome_de_planilha_do_ouro(cenario):
    with pytest.raises(SystemExit):
        amostra_ouro.main(["--corpus", str(cenario / "corpus.csv"), "--holdout", str(cenario / "holdout.csv"),
                           "--saida", str(cenario / "ouro_rotulador_1.csv")])


def test_help_roda():
    r = subprocess.run([sys.executable, "treino/amostra_ouro.py", "--help"], cwd=RAIZ, capture_output=True)
    assert r.returncode == 0 and b"--por-padrao" in r.stdout
