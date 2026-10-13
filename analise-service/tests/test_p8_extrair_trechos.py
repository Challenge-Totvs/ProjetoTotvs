"""P8 etapa 1 — extrair_trechos.py com corpus SINTÉTICO."""
import json
import subprocess
import sys
from pathlib import Path

from sintetico_p8 import corpus, gravar
from treino import comum, extrair_trechos

RAIZ = Path(__file__).resolve().parent.parent


def test_dividir_turnos_segue_o_sdd():
    texto = "cabeçalho descartado\n[LOCUTOR 3]: Bom dia.\ncontinua aqui\r\n[locutor 12] Tudo bem?\n[LOCUTOR 5]:   \n"
    assert comum.dividir_turnos(texto) == [(3, "Bom dia. continua aqui"), (12, "Tudo bem?")]


def test_exclui_reunioes_e_clientes_do_holdout():
    linhas = corpus(30)
    holdout = [{"reuniao": "R000"}, {"reuniao": "R010"}]  # clientes C000 e C003 (3 reuniões cada)
    trechos, contagem = extrair_trechos.extrair(linhas, holdout, "reuniao", "CODT", "transcricao")
    reunioes = {t["reuniao"] for t in trechos}
    assert contagem["reunioes_excluidas_holdout"] == 6 and contagem["clientes_no_holdout"] == 2
    assert not reunioes & {"R000", "R001", "R002", "R009", "R010", "R011"}
    assert {t["cliente"] for t in trechos}.isdisjoint({"C000", "C003"})
    assert contagem["reunioes_usadas"] == 24


def test_holdout_com_coluna_de_cliente_tambem_exclui():
    linhas = corpus(9)
    trechos, _ = extrair_trechos.extrair(linhas, [{"reuniao": "X", "CODT": "C001"}], "reuniao", "CODT", "transcricao")
    assert {t["cliente"] for t in trechos} == {"C000", "C002"}


def test_trecho_tem_alvo_e_dois_turnos_de_contexto():
    linhas = [{"reuniao": "R1", "CODT": "C1", "transcricao": "[LOCUTOR 1]: um\n[LOCUTOR 2]: dois\n[LOCUTOR 1]: tres\n[LOCUTOR 2]: quatro"}]
    trechos, _ = extrair_trechos.extrair(linhas, [], "reuniao", "CODT", "transcricao")
    assert [t["id"] for t in trechos] == ["R1:1", "R1:2", "R1:3", "R1:4"]
    assert trechos[0]["contexto"] == "" and trechos[3]["contexto"] == "dois || tres"
    assert trechos[3]["texto"] == "quatro" and trechos[3]["locutor"] == 2


def test_main_grava_e_imprime_so_contagens(tmp_path, capsys):
    linhas = corpus(12)
    c = gravar(tmp_path / "corpus.csv", linhas)
    h = gravar(tmp_path / "holdout.csv", [{"reuniao": "R000"}])
    saida = tmp_path / "trechos.csv"
    assert extrair_trechos.main(["--corpus", str(c), "--holdout", str(h), "--saida", str(saida)]) == 0
    impresso = capsys.readouterr().out
    gravados = comum.ler_csv(saida)
    assert gravados and list(gravados[0]) == extrair_trechos.COLUNAS_SAIDA
    assert all(t["texto"] not in impresso for t in gravados)
    assert json.loads(impresso)["trechos"] == len(gravados)


def test_verificar_mostra_so_nomes_de_colunas(tmp_path, capsys):
    c = gravar(tmp_path / "corpus.csv", corpus(5))
    h = gravar(tmp_path / "holdout.csv", [{"reuniao": "R000"}])
    assert extrair_trechos.main(["--corpus", str(c), "--holdout", str(h), "--verificar"]) == 0
    resumo = json.loads(capsys.readouterr().out)
    assert resumo["corpus"] == {"colunas": ["reuniao", "CODT", "transcricao"], "linhas": 5}
    assert not (tmp_path / "trechos.csv").exists()


def test_coluna_errada_para_com_mensagem(tmp_path):
    import pytest

    with pytest.raises(SystemExit, match="coluna 'texto'"):
        extrair_trechos.extrair(corpus(3), [], "reuniao", "CODT", "texto")


def test_arquivo_ausente_devolve_1(tmp_path, capsys):
    assert extrair_trechos.main(["--corpus", str(tmp_path / "nao.csv"), "--holdout", str(tmp_path / "h.csv")]) == 1


def test_help_roda():
    r = subprocess.run([sys.executable, "treino/extrair_trechos.py", "--help"], cwd=RAIZ, capture_output=True)
    assert r.returncode == 0 and b"holdout" in r.stdout
