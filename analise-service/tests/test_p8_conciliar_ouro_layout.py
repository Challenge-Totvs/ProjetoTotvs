"""P8 etapa 3 — conciliar_ouro.py no layout REAL da planilha (abas Leia-me, Rotular, Padrões, Listas), SINTÉTICO."""
import json
from pathlib import Path

import pytest

openpyxl = pytest.importorskip("openpyxl")

from treino import comum, conciliar_ouro as co  # noqa: E402

CABECALHO_REAL = ["ID", "contexto (2 turnos antes)", "contexto (turno anterior)", "TRECHO ALVO", "padrao_1",
                  "padrao_2", "interesse", "duvida", "observacao"]
TEXTO = "Frase sintética número {} da reunião inventada."
LISTA_PADROES = ["preco_objecao", "renovacao", "fiscal_problema", "treinamento", "nenhum"]


def planilha_real(caminho: Path, linhas: list[list], lista=LISTA_PADROES, com_listas: bool = True) -> Path:
    """Mesmo desenho da planilha entregue: Rotular NÃO é a primeira aba, cabeçalho na linha 1, coluna C oculta."""
    livro = openpyxl.Workbook()
    leia_me = livro.active
    leia_me.title = "Leia-me"
    leia_me.append(["Instruções de rotulagem (sintético)"])
    rotular = livro.create_sheet("Rotular")
    rotular.append(CABECALHO_REAL)
    for linha in linhas:
        rotular.append(linha)
    rotular.column_dimensions["C"].hidden = True
    livro.create_sheet("Padrões").append(["padrão", "definição"])
    if com_listas:
        listas = livro.create_sheet("Listas")
        listas.append(["padroes", "sim_nao"])
        for i, valor in enumerate(lista):
            listas.append([valor, ["sim", "nao"][i] if i < 2 else None])
    livro.save(caminho)
    return caminho


def linhas_reais(n: int, padroes=("preco_objecao", "renovacao", "")) -> list[list]:
    return [[f"G{i:03d}", "ctx a", "ctx b", TEXTO.format(i), padroes[i % len(padroes)], "",
             ("sim", "nao")[i % 2], "", "obs"] for i in range(n)]


def test_layout_real_ids_e_trecho_alvo_com_coluna_oculta(tmp_path, capsys):
    planilha_real(tmp_path / co.ARQUIVOS[1], linhas_reais(9))
    assert co.main(["--pasta", str(tmp_path), "--relatorio", str(tmp_path / "r.md")]) == 0
    ouro = comum.ler_csv(tmp_path / "ouro_final.csv")
    assert len(ouro) == 9 and ouro[0]["id"] == "G000" and ouro[0]["texto"] == TEXTO.format(0)
    assert ouro[0]["padrao_1"] == "preco_objecao" and ouro[1]["interesse"] == "0" and ouro[0]["interesse"] == "1"
    meta = json.loads((tmp_path / "ouro_final.json").read_text(encoding="utf-8"))
    assert meta["invalidos"] == {"padrao": 0, "interesse": 0, "ids_repetidos": 0, "fora_da_lista": 0}
    assert "Frase sintética" not in capsys.readouterr().out


def test_cabecalho_sem_distincao_de_maiusculas(tmp_path):
    linhas = linhas_reais(3)
    planilha_real(tmp_path / co.ARQUIVOS[1], linhas)
    livro = openpyxl.load_workbook(tmp_path / co.ARQUIVOS[1])
    livro["Rotular"]["A1"].value, livro["Rotular"]["D1"].value = "Id", "trecho alvo"
    livro.save(tmp_path / co.ARQUIVOS[1])
    assert co.main(["--pasta", str(tmp_path), "--relatorio", str(tmp_path / "r.md")]) == 0
    assert comum.ler_csv(tmp_path / "ouro_final.csv")[2]["texto"] == TEXTO.format(2)


def test_le_sempre_a_aba_rotular(tmp_path):
    # A 1ª aba (Leia-me) tem uma coluna ID falsa com outro conteúdo: só a Rotular conta.
    planilha_real(tmp_path / co.ARQUIVOS[1], linhas_reais(4))
    livro = openpyxl.load_workbook(tmp_path / co.ARQUIVOS[1])
    livro["Leia-me"].append(["ID", "TRECHO ALVO"])
    livro["Leia-me"].append(["X1", "texto de outra aba"])
    livro.save(tmp_path / co.ARQUIVOS[1])
    assert co.main(["--pasta", str(tmp_path), "--relatorio", str(tmp_path / "r.md")]) == 0
    assert [x["id"] for x in comum.ler_csv(tmp_path / "ouro_final.csv")] == ["G000", "G001", "G002", "G003"]


def test_sem_aba_rotular_erro_claro(tmp_path):
    livro = openpyxl.Workbook()
    livro.active.title = "Outra"
    livro.save(tmp_path / co.ARQUIVOS[1])
    with pytest.raises(SystemExit, match="sem a aba 'Rotular'"):
        co.main(["--pasta", str(tmp_path)])


def test_padrao_fora_da_aba_listas_so_conta(tmp_path, capsys):
    linhas = linhas_reais(6)
    linhas[0][4] = "cancelamento_citado"      # padrão válido, mas fora da aba Listas
    linhas[1][5] = "padrao_inventado_xyz"      # nem padrão é
    linhas[2][4] = "Preço objeção"             # grafia diferente do mesmo valor da lista: aceita
    planilha_real(tmp_path / co.ARQUIVOS[1], linhas)
    co.main(["--pasta", str(tmp_path), "--relatorio", str(tmp_path / "r.md")])
    meta = json.loads((tmp_path / "ouro_final.json").read_text(encoding="utf-8"))
    assert meta["invalidos"]["fora_da_lista"] == 2 and meta["invalidos"]["padrao"] == 0
    ouro = comum.ler_csv(tmp_path / "ouro_final.csv")
    assert ouro[0]["padrao_1"] == "" and ouro[2]["padrao_1"] == "preco_objecao"
    saida = capsys.readouterr().out + (tmp_path / "r.md").read_text(encoding="utf-8")
    assert "cancelamento_citado" not in saida and "padrao_inventado_xyz" not in saida


def test_sem_aba_listas_nao_valida(tmp_path):
    linhas = linhas_reais(3)
    linhas[0][4] = "cancelamento_citado"
    planilha_real(tmp_path / co.ARQUIVOS[1], linhas, com_listas=False)
    co.main(["--pasta", str(tmp_path), "--relatorio", str(tmp_path / "r.md")])
    meta = json.loads((tmp_path / "ouro_final.json").read_text(encoding="utf-8"))
    assert meta["invalidos"]["fora_da_lista"] == 0
    assert comum.ler_csv(tmp_path / "ouro_final.csv")[0]["padrao_1"] == "cancelamento_citado"


def test_verificar_no_layout_real(tmp_path, capsys):
    planilha_real(tmp_path / co.ARQUIVOS[1], linhas_reais(5))
    assert co.main(["--pasta", str(tmp_path), "--verificar"]) == 0
    resumo = json.loads(capsys.readouterr().out)[co.ARQUIVOS[1]]
    assert resumo["linhas"] == 5 and "trecho_alvo" in resumo["colunas"] and resumo["valores_na_aba_listas"] > 0
    assert "Frase sintética" not in json.dumps(resumo)
