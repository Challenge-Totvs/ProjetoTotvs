"""P8 — rotulos_suspeitos.py: confident learning (cleanlab) agrupado por cliente, com dados SINTÉTICOS."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

from sintetico_p8 import base_sintetica, rotulos_sinteticos
from treino import comum, rotulos_suspeitos, treinar

RAIZ = Path(__file__).resolve().parent.parent
pytest.importorskip("cleanlab")


@pytest.fixture
def cenario(tmp_path):
    return {"base": base_sintetica(tmp_path / "base.joblib"), "rotulos": rotulos_sinteticos(tmp_path, reunioes=60),
            "pasta": tmp_path}


def test_dobras_possiveis():
    assert rotulos_suspeitos.dobras_possiveis(["a", "a", "b", "c"], 5) == 3
    assert rotulos_suspeitos.dobras_possiveis(["a"], 5) == 0  # 1 cliente só: não dá para rodar
    assert rotulos_suspeitos.dobras_possiveis([f"c{i}" for i in range(10)], 5) == 5
    assert rotulos_suspeitos.dobras_possiveis([f"c{i}" for i in range(10)], 1) == 0  # --dobras < 2 também não dá


def test_suspeitos_do_grupo_roda_e_nao_vaza_texto(cenario):
    import joblib

    linhas = comum.ler_csv(cenario["rotulos"])
    base = joblib.load(cenario["base"])
    saida, info = rotulos_suspeitos.suspeitos_do_grupo(linhas, "risco", base, dobras_pedidas=3)
    assert info["trechos"] == len(linhas)
    assert "dobras_usadas" in info and info["dobras_usadas"] >= 2
    assert isinstance(info.get("suspeitos", 0), int)
    for linha in saida:
        assert set(linha) == {"id", "reuniao", "cliente", "grupo", "rotulo", "confianca", "rank"}
        assert linha["grupo"] == "risco"
        assert 0.0 <= linha["confianca"] <= 1.0
    ids_validos = {x["id"] for x in linhas}
    assert all(linha["id"] in ids_validos for linha in saida)


def test_suspeitos_do_grupo_pula_com_uma_classe_so():
    linhas = [{"id": f"T{i}", "reuniao": "R1", "cliente": "C1", "texto": "oi", "risco": "0"} for i in range(5)]
    saida, info = rotulos_suspeitos.suspeitos_do_grupo(linhas, "risco", object(), dobras_pedidas=5)
    assert saida == [] and "pulado" in info


def test_suspeitos_do_grupo_pula_com_poucos_clientes():
    linhas = [{"id": f"T{i}", "reuniao": "R1", "cliente": "C1", "texto": "oi", "risco": str(i % 2)} for i in range(4)]
    saida, info = rotulos_suspeitos.suspeitos_do_grupo(linhas, "risco", object(), dobras_pedidas=5)
    assert saida == [] and "pulado" in info


def test_main_escreve_csv_sem_texto_de_trecho(cenario, capsys):
    saida_csv = cenario["pasta"] / "rotulos_suspeitos.csv"
    assert rotulos_suspeitos.main(["--rotulos", str(cenario["rotulos"]), "--base", str(cenario["base"]),
                                   "--saida", str(saida_csv), "--dobras", "3"]) == 0
    resumo = json.loads(capsys.readouterr().out)
    assert set(resumo["grupos"]) == {"risco", "interesse"}
    assert saida_csv.is_file()
    conteudo = saida_csv.read_text(encoding="utf-8")
    assert "id,reuniao,cliente,grupo,rotulo,confianca,rank" in conteudo.splitlines()[0]
    linhas_rotulos = comum.ler_csv(cenario["rotulos"])
    assert all(x["texto"] not in conteudo for x in linhas_rotulos if x["texto"])


def test_sem_rotulos_devolve_1(tmp_path):
    assert rotulos_suspeitos.main(["--rotulos", str(tmp_path / "nao-existe.csv")]) == 1


def test_help_roda():
    r = subprocess.run([sys.executable, "treino/rotulos_suspeitos.py", "--help"], cwd=RAIZ, capture_output=True)
    assert r.returncode == 0 and b"--dobras" in r.stdout


# ------------------------------------------------------------------ integração com treinar.py --excluir-suspeitos

def test_treinar_exclui_suspeitos_do_grupo_marcado(cenario):
    linhas = comum.ler_csv(cenario["rotulos"])
    ids_risco_positivos = [x["id"] for x in linhas if x["risco"] == "1"]
    assert ids_risco_positivos, "cenário sintético precisa ter positivos de risco"
    excluido = ids_risco_positivos[0]
    suspeitos_csv = cenario["pasta"] / "rotulos_suspeitos.csv"
    comum.gravar_csv(suspeitos_csv, [{"id": excluido, "reuniao": "", "cliente": "", "grupo": "risco", "rotulo": 1,
                                      "confianca": 0.1, "rank": 0}], rotulos_suspeitos.COLUNAS_SAIDA)

    sem_exclusao = treinar.main(["--rotulos", str(cenario["rotulos"]), "--base", str(cenario["base"]),
                                 "--candidatos", str(cenario["pasta"] / "sem"),
                                 "--holdout", str(cenario["pasta"] / "nao-existe.csv"),
                                 "--ouro", str(cenario["pasta"] / "nao-existe-ouro.csv"),
                                 "--veredito", str(cenario["pasta"] / "nao-existe-veredito.json")])
    assert sem_exclusao == 0
    meta_sem = json.loads(next((cenario["pasta"] / "sem").iterdir()).joinpath("metadata.json").read_text(encoding="utf-8"))
    assert meta_sem["tamanhos"]["risco"]["excluidos_suspeitos"] == 0
    assert meta_sem["suspeitos"]["excluir_suspeitos"] is False

    com_exclusao = treinar.main(["--rotulos", str(cenario["rotulos"]), "--base", str(cenario["base"]),
                                 "--candidatos", str(cenario["pasta"] / "com"),
                                 "--holdout", str(cenario["pasta"] / "nao-existe.csv"),
                                 "--ouro", str(cenario["pasta"] / "nao-existe-ouro.csv"),
                                 "--veredito", str(cenario["pasta"] / "nao-existe-veredito.json"),
                                 "--excluir-suspeitos", "--suspeitos", str(suspeitos_csv)])
    assert com_exclusao == 0
    meta_com = json.loads(next((cenario["pasta"] / "com").iterdir()).joinpath("metadata.json").read_text(encoding="utf-8"))
    assert meta_com["tamanhos"]["risco"]["excluidos_suspeitos"] == 1
    assert meta_com["tamanhos"]["risco"]["positivos"] == meta_sem["tamanhos"]["risco"]["positivos"] - 1
    # interesse não foi marcado como suspeito: continua com o mesmo tamanho
    assert meta_com["tamanhos"]["interesse"] == meta_sem["tamanhos"]["interesse"]
    assert meta_com["suspeitos"]["excluir_suspeitos"] is True and meta_com["suspeitos"]["arquivo"] == suspeitos_csv.name


def test_treinar_excluir_suspeitos_sem_arquivo_avisa_e_continua(cenario, capsys):
    assert treinar.main(["--rotulos", str(cenario["rotulos"]), "--base", str(cenario["base"]),
                         "--candidatos", str(cenario["pasta"] / "candidatos"),
                         "--holdout", str(cenario["pasta"] / "nao-existe.csv"),
                         "--ouro", str(cenario["pasta"] / "nao-existe-ouro.csv"),
                         "--veredito", str(cenario["pasta"] / "nao-existe-veredito.json"),
                         "--excluir-suspeitos", "--suspeitos", str(cenario["pasta"] / "nao-existe-suspeitos.csv")]) == 0
    assert "aviso" in capsys.readouterr().out
