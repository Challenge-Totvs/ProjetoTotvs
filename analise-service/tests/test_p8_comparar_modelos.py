"""P8 — comparar_modelos.py: divergências, revisão cega, placar e promoção, com dados e modelos SINTÉTICOS."""
import json

import numpy as np
import pytest

from treino import comparar_modelos as cm


class Fixo:
    """Modelo sintético: p = 0,9 se alguma palavra-gatilho aparece no texto, senão 0,1."""

    def __init__(self, gatilhos):
        self.gatilhos = gatilhos

    def predict_proba(self, textos):
        p = np.array([0.9 if any(g in t.lower() for g in self.gatilhos) else 0.1 for t in textos])
        return np.column_stack([1 - p, p])


TEXTOS = [
    "O suporte demorou duas semanas para responder o chamado.",   # os dois marcam risco
    "A gente recebeu uma proposta de outra empresa mais barata.",  # só o candidato marca
    "O reajuste ficou alto, mas seguimos com o contrato.",         # só o atual marca
    "Vamos marcar a próxima reunião para quinta-feira à tarde.",   # nenhum marca
]
ATUAL = Fixo(["suporte", "reajuste"])
CANDIDATO = Fixo(["suporte", "proposta"])


def test_divergencias_so_onde_discordam():
    dec = cm.decisoes(TEXTOS, ATUAL, CANDIDATO, None)
    assert cm.divergencias(dec) == {"risco": [1, 2]}


def test_interesse_usa_o_filtro_atual_e_o_limiar_do_candidato():
    textos = ["Gostei muito, quero ver uma demonstração do módulo.", "Nada a declarar sobre isso hoje, obrigado."]
    dec = cm.decisoes(textos, Fixo([]), Fixo([]), Fixo(["demonstração"]))
    assert dec["interesse"]["candidato"] == [1, 0]
    assert len(dec["interesse"]["atual"]) == 2


def test_amostra_reprodutivel_e_limitada():
    a = cm.amostrar(list(range(100)), 10, semente=1)
    assert a == cm.amostrar(list(range(100)), 10, semente=1)
    assert len(a) == 10 and len(set(a)) == 10
    assert sorted(cm.amostrar([3, 5], 10)) == [3, 5]


def test_teste_do_sinal():
    assert cm.teste_do_sinal(0, 0) == 1.0
    assert cm.teste_do_sinal(5, 5) == 1.0
    assert cm.teste_do_sinal(15, 0) < 0.001
    assert cm.teste_do_sinal(9, 6) > 0.05


def _chave(n_cand_marca, n_atual_marca):
    chave = {"_totais": {"risco": n_cand_marca + n_atual_marca}, "risco": {}}
    for i in range(n_cand_marca):
        chave["risco"][f"C{i}"] = {"atual": 0, "candidato": 1}
    for i in range(n_atual_marca):
        chave["risco"][f"A{i}"] = {"atual": 1, "candidato": 0}
    return chave


def test_placar_candidato_melhor():
    chave = _chave(20, 0)
    respostas = [{"id": f"C{i}", "grupo": "risco", "resposta": "sim" if i < 18 else "nao"} for i in range(20)]
    r = cm.placar(respostas, chave)["risco"]
    assert (r["vitorias_candidato"], r["vitorias_atual"]) == (18, 2)
    assert r["veredito"] == "candidato melhor"
    assert r["por_direcao"]["so_candidato_marca"] == {"candidato": 18, "atual": 2}


def test_placar_atual_melhor_e_duvida_fora():
    chave = _chave(16, 0)
    respostas = [{"id": f"C{i}", "grupo": "risco", "resposta": "nao"} for i in range(15)]
    respostas.append({"id": "C15", "grupo": "risco", "resposta": "duvida"})
    r = cm.placar(respostas, chave)["risco"]
    assert r["veredito"] == "atual melhor"
    assert r["duvida"] == 1 and r["revisados"] == 15


def test_placar_inconclusivo_e_em_branco():
    chave = _chave(3, 3)
    respostas = [{"id": "C0", "grupo": "risco", "resposta": "sim"}, {"id": "A0", "grupo": "risco", "resposta": "sim"},
                 {"id": "C1", "grupo": "risco", "resposta": ""}]
    r = cm.placar(respostas, chave)["risco"]
    assert r["veredito"] == "inconclusivo"
    assert r["em_branco"] == 1


def test_planilha_e_cega(tmp_path):
    linhas = [{"id": "R-x:1", "grupo": "risco", "pergunta": cm.PERGUNTA["risco"], "contexto": "c", "trecho": "t",
               "resposta": ""}]
    caminho = tmp_path / "revisao.xlsx"
    cm.gravar_planilha(caminho, linhas)
    lidas = cm.ler_planilha(caminho)
    assert list(lidas[0]) == cm.COLUNAS_PLANILHA
    assert not {"atual", "candidato"} & set(lidas[0])


def test_relatorio_sem_texto(tmp_path):
    chave = _chave(2, 0)
    resultado = cm.placar([{"id": "C0", "grupo": "risco", "resposta": "sim"}], chave)
    caminho = tmp_path / "rel.md"
    cm.escrever_relatorio(caminho, "cand", resultado, {"trechos": 10})
    texto = caminho.read_text(encoding="utf-8")
    assert "| risco |" in texto and "suporte" not in texto


def test_promover_guarda_o_anterior(tmp_path, monkeypatch):
    pasta = tmp_path / "cand"
    pasta.mkdir()
    (pasta / "risco.joblib").write_bytes(b"novo")
    destino = tmp_path / "app" / "classificador_risco.joblib"
    destino.parent.mkdir()
    destino.write_bytes(b"velho")
    monkeypatch.setitem(cm.DESTINO, "risco", destino)
    feito = cm.promover(["risco"], pasta, tmp_path / "backup")
    assert destino.read_bytes() == b"novo"
    assert (tmp_path / "backup" / "classificador_risco.joblib").read_bytes() == b"velho"
    assert len(feito) == 2


def test_trechos_do_holdout_fora_do_ouro():
    corpus = [{"ID_MEETING": "1", "ANON_TRANSCRICAO": "[LOCUTOR 1]: " + TEXTOS[0] + "\n[LOCUTOR 2]: ok"},
              {"ID_MEETING": "2", "ANON_TRANSCRICAO": "[LOCUTOR 1]: " + TEXTOS[1]},
              {"ID_MEETING": "3", "ANON_TRANSCRICAO": "[LOCUTOR 1]: " + TEXTOS[2]}]
    holdout = [{"ID_MEETING": "1", "no_ouro": "0"}, {"ID_MEETING": "2", "no_ouro": "1"}]
    trechos, contagem = cm.trechos_do_holdout(corpus, holdout, "ID_MEETING", "ANON_TRANSCRICAO", "ID_MEETING")
    assert [t["id"] for t in trechos] == ["1:1"]          # reunião 2 está no ouro, reunião 3 não é holdout
    assert contagem["trechos_curtos_ignorados"] == 1     # "ok"


def test_placar_recusa_chave_de_outro_candidato(tmp_path):
    cand = tmp_path / "candidatos" / "2026-10-14"
    cand.mkdir(parents=True)
    saida = tmp_path / "cmp"
    saida.mkdir()
    (saida / "chave.json").write_text(json.dumps({"_candidato": "outro"}), encoding="utf-8")
    cm.gravar_planilha(saida / "revisao.xlsx", [])
    with pytest.raises(SystemExit):
        cm.main(["placar", "--candidato", str(cand), "--saida", str(saida)])
