"""P8 etapa 3 — conciliar_ouro.py com planilhas SINTÉTICAS (modos único e pares, kappa teste-reteste)."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

openpyxl = pytest.importorskip("openpyxl")

from treino import comum, conciliar_ouro as co  # noqa: E402

RAIZ = Path(__file__).resolve().parent.parent
CABECALHO = ["id", "contexto", "texto", "padrao_1", "padrao_2", "interesse", "duvida"]
TEXTO = "Frase sintética número {} da reunião inventada."


def planilha(caminho: Path, linhas: list[list], titulo: bool = True) -> Path:
    livro = openpyxl.Workbook()
    aba = livro.active
    aba.title = "Rotular"  # o conciliar_ouro lê SEMPRE a aba Rotular
    if titulo:
        aba.append(["Planilha de rotulagem (sintética)"])  # o cabeçalho não precisa estar na 1ª linha
    aba.append(CABECALHO)
    for linha in linhas:
        aba.append(linha)
    livro.save(caminho)
    return caminho


def metade(prefixo: str, n: int, padroes=("preco_objecao", "renovacao", ""), interesse=("sim", "nao")) -> list[list]:
    return [[f"{prefixo}{i:03d}", "ctx", TEXTO.format(i), padroes[i % len(padroes)], "",
             interesse[i % len(interesse)], ""] for i in range(n)]


def _rodar(pasta: Path, *extra) -> tuple[int, dict]:
    relatorio = pasta / "relatorio.md"
    codigo = co.main(["--pasta", str(pasta), "--relatorio", str(relatorio), *extra])
    return codigo, json.loads((pasta / "ouro_final.json").read_text(encoding="utf-8")) if codigo == 0 else {}


def test_kappa_de_cohen():
    assert co.kappa_cohen(["a", "b", "a", "b"], ["a", "b", "a", "b"]) == 1.0
    assert co.kappa_cohen(["a", "a", "b", "b"], ["a", "b", "a", "b"]) == 0.0
    assert co.kappa_cohen(["x", "x"], ["x", "x"]) == 1.0
    assert co.kappa_cohen([], []) is None
    assert co.kappa_cohen([True, True, False, False, True], [True, False, False, False, True]) == pytest.approx(0.6154, abs=1e-4)


def test_unico_so_metade_a_e_parcial(tmp_path, capsys):
    planilha(tmp_path / co.ARQUIVOS[1], metade("GA", 30))
    codigo, meta = _rodar(tmp_path)
    assert codigo == 0 and meta["modo"] == "unico" and meta["completo"] is False and meta["metades"] == ["A"]
    assert any("reteste ainda não medido" in a for a in meta["avisos"])
    ouro = comum.ler_csv(tmp_path / "ouro_final.csv")
    assert len(ouro) == 30 and list(ouro[0]) == co.COLUNAS_OURO
    preco = next(x for x in ouro if x["padrao_1"] == "preco_objecao")
    assert (preco["risco"], preco["oportunidade"]) == ("1", "0")
    impresso = capsys.readouterr().out
    assert "Frase sintética" not in impresso
    relatorio = (tmp_path / "relatorio.md").read_text(encoding="utf-8")
    assert "PARCIAL" in relatorio and "Rotulador único" in relatorio and "Frase sintética" not in relatorio


def test_unico_completo_com_reteste(tmp_path):
    planilha(tmp_path / co.ARQUIVOS[1], metade("GA", 20))
    planilha(tmp_path / co.ARQUIVOS[3], metade("GB", 20))
    # Reteste: 10 trechos da metade A, com 2 respostas de padrão diferentes da 1ª vez.
    reteste = [[f"R{i:02d}", "ctx", TEXTO.format(i), ("preco_objecao", "renovacao", "")[i % 3] if i not in (1, 4) else
                "fiscal_problema", "", ("sim", "nao")[i % 2], ""] for i in range(10)]
    planilha(tmp_path / co.RETESTE, reteste)
    comum.gravar_csv(tmp_path / co.MAPA_RETESTE, [{"reteste": f"R{i:02d}", "ouro": f"GA{i:03d}"} for i in range(10)],
                     ["reteste", "ouro"])
    codigo, meta = _rodar(tmp_path)
    assert codigo == 0 and meta["completo"] is True and meta["metades"] == ["A", "B"]
    k = meta["kappas"]["teste-reteste"]
    assert k["interesse"] == 1.0 and 0 < k["padrao"] < 1 and meta["pares_kappa"]["teste-reteste"] == 10
    assert len(comum.ler_csv(tmp_path / "ouro_final.csv")) == 40


def test_kappa_baixo_gera_aviso(tmp_path):
    planilha(tmp_path / co.ARQUIVOS[1], metade("GA", 10))
    reteste = [[f"R{i:02d}", "", "", "", "", ("nao", "sim")[i % 2], ""] for i in range(10)]  # interesse invertido
    planilha(tmp_path / co.RETESTE, reteste)
    comum.gravar_csv(tmp_path / co.MAPA_RETESTE, [{"reteste": f"R{i:02d}", "ouro": f"GA{i:03d}"} for i in range(10)],
                     ["reteste", "ouro"])
    _, meta = _rodar(tmp_path)
    assert any("teste-reteste/interesse" in a and "revisar as definições" in a for a in meta["avisos"])


def test_valores_invalidos_sao_contados_sem_imprimir(tmp_path, capsys):
    linhas = metade("GA", 5)
    linhas[0][3] = "padrao_que_nao_existe"
    linhas[1][5] = "talvez"
    planilha(tmp_path / co.ARQUIVOS[1], linhas)
    _, meta = _rodar(tmp_path)
    assert meta["invalidos"] == {"padrao": 1, "interesse": 1, "ids_repetidos": 0, "fora_da_lista": 0}
    assert "padrao_que_nao_existe" not in capsys.readouterr().out


def test_unico_sem_metade_a_para(tmp_path):
    with pytest.raises(SystemExit, match="metade A"):
        co.main(["--pasta", str(tmp_path)])


def test_pares_com_divergencias_pede_arbitragem_e_depois_grava(tmp_path):
    a1 = metade("GA", 12)
    a2 = [linha[:] for linha in a1]
    a2[0][3] = "renovacao"  # divergência de padrão
    a2[5][5] = "sim" if a1[5][5] == "nao" else "nao"  # divergência de interesse
    planilha(tmp_path / co.ARQUIVOS[1], a1)
    planilha(tmp_path / co.ARQUIVOS[2], a2)
    codigo = co.main(["--pasta", str(tmp_path), "--modo", "pares", "--relatorio", str(tmp_path / "r.md")])
    assert codigo == 3 and (tmp_path / co.DIVERGENCIAS).is_file() and not (tmp_path / "ouro_final.csv").exists()

    livro = openpyxl.load_workbook(tmp_path / co.DIVERGENCIAS)
    aba = livro.active
    for linha in aba.iter_rows(min_row=2):
        linha[5].value = "renovacao" if linha[2].value == "padrao_1" else "sim"
    livro.save(tmp_path / co.DIVERGENCIAS_PRONTO)
    codigo, meta = _rodar(tmp_path, "--modo", "pares")
    assert codigo == 0 and meta["modo"] == "pares" and meta["completo"] is False and meta["divergencias"] == 2
    assert "rotuladores 1x2" in meta["kappas"] and meta["kappas"]["rotuladores 1x2"]["padrao"] < 1
    ouro = {x["id"]: x for x in comum.ler_csv(tmp_path / "ouro_final.csv")}
    assert ouro["GA000"]["padrao_1"] == "renovacao" and ouro["GA005"]["interesse"] == "1"


def test_pares_sem_decisao_para(tmp_path):
    a1 = metade("GA", 6)
    a2 = [linha[:] for linha in a1]
    a2[0][3] = "renovacao"
    planilha(tmp_path / co.ARQUIVOS[1], a1)
    planilha(tmp_path / co.ARQUIVOS[2], a2)
    co.main(["--pasta", str(tmp_path), "--modo", "pares", "--relatorio", str(tmp_path / "r.md")])
    (tmp_path / co.DIVERGENCIAS).rename(tmp_path / co.DIVERGENCIAS_PRONTO)  # sem preencher a decisão
    with pytest.raises(SystemExit, match="sem decisão"):
        co.main(["--pasta", str(tmp_path), "--modo", "pares", "--relatorio", str(tmp_path / "r.md")])


def test_pares_quatro_rotuladores_completo_sem_divergencia(tmp_path):
    for k, prefixo in ((1, "GA"), (2, "GA"), (3, "GB"), (4, "GB")):
        planilha(tmp_path / co.ARQUIVOS[k], metade(prefixo, 8))
    codigo, meta = _rodar(tmp_path, "--modo", "pares")
    assert codigo == 0 and meta["completo"] is True and set(meta["kappas"]) == {"rotuladores 1x2", "rotuladores 3x4"}
    assert meta["avisos"] == []


def test_verificar_mostra_so_colunas(tmp_path, capsys):
    planilha(tmp_path / co.ARQUIVOS[1], metade("GA", 4))
    assert co.main(["--pasta", str(tmp_path), "--verificar"]) == 0
    resumo = json.loads(capsys.readouterr().out)
    assert resumo[co.ARQUIVOS[1]]["linhas"] == 4 and "padrao_1" in resumo[co.ARQUIVOS[1]]["colunas"]
    assert not (tmp_path / "ouro_final.csv").exists()


def test_colunas_com_outros_nomes(tmp_path):
    livro = openpyxl.Workbook()
    aba = livro.active
    aba.title = "Rotular"
    aba.append(["ID", "Fala alvo", "Padrão 1", "Padrão 2", "Interesse?", "Dúvida"])
    aba.append(["G1", TEXTO.format(1), "Renovação", "", "Sim", "x"])
    livro.save(tmp_path / co.ARQUIVOS[1])
    codigo = co.main(["--pasta", str(tmp_path), "--relatorio", str(tmp_path / "r.md"), "--col-id", "ID",
                      "--col-texto", "Fala alvo", "--col-padrao1", "Padrão 1", "--col-padrao2", "Padrão 2",
                      "--col-interesse", "Interesse?", "--col-duvida", "Dúvida"])
    ouro = comum.ler_csv(tmp_path / "ouro_final.csv")
    assert codigo == 0 and ouro[0]["padrao_1"] == "renovacao" and ouro[0]["interesse"] == "1" and ouro[0]["duvida"] == "1"
    assert ouro[0]["texto"] == TEXTO.format(1)


def test_help_roda():
    r = subprocess.run([sys.executable, "treino/conciliar_ouro.py", "--help"], cwd=RAIZ, capture_output=True)
    assert r.returncode == 0 and b"--modo" in r.stdout


def test_pares_duvida_e_motivo_de_qualquer_um_dos_dois(tmp_path):
    a, b = metade("GA", 8), metade("GA", 8)
    b[0][6] = "não sei se é renovação"  # texto livre na célula duvida: é dúvida, e o texto é o motivo
    planilha(tmp_path / co.ARQUIVOS[1], a)
    planilha(tmp_path / co.ARQUIVOS[2], b)
    codigo, meta = _rodar(tmp_path, "--modo", "pares")
    ouro = {x["id"]: x for x in comum.ler_csv(tmp_path / "ouro_final.csv")}
    assert codigo == 0 and ouro["GA000"]["duvida"] == "1" and ouro["GA000"]["motivo_duvida"] == "não sei se é renovação"
    assert meta["resumo"]["duvida_com_motivo"] == 1
