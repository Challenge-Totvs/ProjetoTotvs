"""P8 etapa 5 — portao.py: métricas por grupo, bootstrap e decisão, com ouro e modelos SINTÉTICOS."""
import json
import subprocess
import sys
from pathlib import Path

import joblib
import numpy as np
import pytest

from sintetico_p8 import FRASES_INTERESSE, FRASES_NEUTRAS, FRASES_OPORTUNIDADE, FRASES_RISCO
from treino import comum, conciliar_ouro, portao

RAIZ = Path(__file__).resolve().parent.parent


class Fixo:
    """Modelo sintético: p = 0,9 se alguma palavra-gatilho aparece no texto, senão 0,1."""

    def __init__(self, gatilhos):
        self.gatilhos = gatilhos

    def predict_proba(self, textos):
        p = np.array([0.9 if any(g in t.lower() for g in self.gatilhos) else 0.1 for t in textos])
        return np.column_stack([1 - p, p])


def _ouro():
    linhas = []
    for i, t in enumerate(FRASES_RISCO):
        linhas.append({"id": f"G{i}", "texto": t, "padrao_1": "suporte_insatisfacao", "padrao_2": "", "risco": "1",
                       "oportunidade": "0", "interesse": "0", "duvida": "0", "metade": "A"})
    for i, t in enumerate(FRASES_OPORTUNIDADE):
        linhas.append({"id": f"O{i}", "texto": t, "padrao_1": "expansao_unidade", "padrao_2": "", "risco": "0",
                       "oportunidade": "1", "interesse": "0", "duvida": "0", "metade": "A"})
    for i, t in enumerate(FRASES_INTERESSE):
        linhas.append({"id": f"I{i}", "texto": t, "padrao_1": "", "padrao_2": "", "risco": "0",
                       "oportunidade": "0", "interesse": "1", "duvida": "0", "metade": "A"})
    for i, t in enumerate(FRASES_NEUTRAS):
        linhas.append({"id": f"N{i}", "texto": t, "padrao_1": "", "padrao_2": "", "risco": "0",
                       "oportunidade": "0", "interesse": "0", "duvida": "1" if i == 0 else "0", "metade": "A"})
    return linhas


def _cenario(tmp_path, completo=True, atual=("suporte",), cand_risco=("suporte", "caro", "cancelar", "sped"),
             cand_interesse=("ajuda", "interessante")):
    ouro = tmp_path / "ouro_final.csv"
    comum.gravar_csv(ouro, _ouro(), conciliar_ouro.COLUNAS_OURO)
    ouro.with_suffix(".json").write_text(json.dumps({"modo": "unico", "completo": completo, "kappas": {},
                                                     "limitacao": conciliar_ouro.LIMITACAO_UNICO}), encoding="utf-8")
    pasta = tmp_path / "candidatos" / "2026-10-14"
    pasta.mkdir(parents=True)
    joblib.dump(Fixo(cand_risco), pasta / "risco.joblib")
    joblib.dump(Fixo(cand_interesse), pasta / "interesse.joblib")
    (pasta / "metadata.json").write_text(json.dumps({"pasta": pasta.name, "mudancas": []}), encoding="utf-8")
    joblib.dump(Fixo(atual), tmp_path / "atual.joblib")
    return ["--ouro", str(ouro), "--candidatos", str(tmp_path / "candidatos"), "--atual", str(tmp_path / "atual.joblib"),
            "--relatorio", str(tmp_path / "portao.md"), "--repeticoes", "300"]


def test_metricas():
    m = portao.metricas([1, 1, 0, 0], [1, 0, 1, 0])
    assert (m["tp"], m["fp"], m["fn"], m["precisao"], m["revocacao"], m["f1"]) == (1, 1, 1, 0.5, 0.5, 0.5)
    assert portao.metricas([0, 0], [0, 0])["f1"] == 0.0


def test_ic95_e_deterministico_e_pareado():
    y, a, c = [1, 1, 1, 0, 0, 0] * 5, [1, 0, 0, 0, 0, 0] * 5, [1, 1, 1, 0, 0, 0] * 5
    ic = portao.ic95_diferenca_f1(y, a, c, repeticoes=500)
    assert ic == portao.ic95_diferenca_f1(y, a, c, repeticoes=500)
    assert 0 < ic[0] <= ic[1]
    assert portao.ic95_diferenca_f1(y, a, a, repeticoes=200) == (0.0, 0.0)


@pytest.mark.parametrize("atual,candidato,ic,aprova", [
    ({"f1": 0.5, "precisao": 0.6, "positivos": 8}, {"f1": 0.6, "precisao": 0.59, "positivos": 8}, (-0.1, 0.3), True),
    ({"f1": 0.5, "precisao": 0.6, "positivos": 8}, {"f1": 0.49, "precisao": 0.7, "positivos": 8}, (-0.2, 0.1), False),
    ({"f1": 0.5, "precisao": 0.6, "positivos": 8}, {"f1": 0.6, "precisao": 0.55, "positivos": 8}, (0.0, 0.2), False),
    ({"f1": 0.5, "precisao": 0.6, "positivos": 8}, {"f1": 0.5, "precisao": 0.6, "positivos": 8}, (-0.3, -0.01), False),
    ({"f1": 0.0, "precisao": 0.0, "positivos": 0}, {"f1": 0.0, "precisao": 0.0, "positivos": 0}, (0.0, 0.0), False),
])
def test_regra_de_aprovacao(atual, candidato, ic, aprova):
    assert portao.decidir(atual, candidato, ic)[0] is aprova


def test_candidato_melhor_com_ouro_completo_imprime_comando(tmp_path, capsys):
    assert portao.main(_cenario(tmp_path)) == 0
    saida = capsys.readouterr().out
    assert "risco: APROVADO" in saida and "interesse: APROVADO" in saida
    assert 'Copy-Item "dados_locais/candidatos/2026-10-14/risco.joblib" "app/modelos/classificador_risco.joblib"' in saida
    assert "classificador_interesse.joblib" in saida and "INTERESSE_MODELO=1" in saida
    assert all(t not in saida for t in FRASES_RISCO + FRASES_INTERESSE + FRASES_NEUTRAS)
    relatorio = (tmp_path / "portao.md").read_text(encoding="utf-8")
    assert "APENAS INDICATIVO" in relatorio and "completo" in relatorio and "Rotulador único" in relatorio
    assert all(t not in relatorio for t in FRASES_RISCO + FRASES_INTERESSE + FRASES_NEUTRAS)


def test_ouro_parcial_nunca_recomenda_promocao(tmp_path, capsys):
    portao.main(_cenario(tmp_path, completo=False))
    saida = capsys.readouterr().out
    assert "Copy-Item" not in saida and "NÃO promover" in saida
    assert "PARCIAL" in (tmp_path / "portao.md").read_text(encoding="utf-8")


def test_candidato_pior_e_reprovado(tmp_path, capsys):
    portao.main(_cenario(tmp_path, atual=("suporte", "caro", "cancelar", "sped"), cand_risco=("suporte",),
                         cand_interesse=("bom dia",)))
    saida = capsys.readouterr().out
    assert "risco: REPROVADO: mantém o atual" in saida and "interesse: REPROVADO: mantém o atual" in saida
    assert "Copy-Item" not in saida


def test_grupos_e_duvida(tmp_path, capsys):
    portao.main(_cenario(tmp_path))
    resumo = json.loads(capsys.readouterr().out.split("\nrisco:")[0])
    grupos = resumo["grupos"]
    assert grupos["risco"]["candidato"]["n"] == len(_ouro()) - 1  # o trecho com dúvida fica de fora
    assert grupos["risco"]["candidato"]["revocacao"] == 1.0 and grupos["risco"]["atual"]["revocacao"] == 0.25
    assert grupos["oportunidade"]["candidato"] is None and grupos["oportunidade"]["atual"]["revocacao"] == 1.0
    # filtro atual de interesse: palavra-chave v2 E risco do atual < 0,3
    assert grupos["interesse"]["atual"]["tp"] == 2


def test_sem_meta_do_ouro_conta_como_parcial(tmp_path, capsys):
    args = _cenario(tmp_path)
    (tmp_path / "ouro_final.json").unlink()
    portao.main(args)
    assert "Copy-Item" not in capsys.readouterr().out


def test_sem_candidato_devolve_1(tmp_path, capsys):
    ouro = tmp_path / "ouro_final.csv"
    comum.gravar_csv(ouro, _ouro(), conciliar_ouro.COLUNAS_OURO)
    assert portao.main(["--ouro", str(ouro), "--candidatos", str(tmp_path / "vazio")]) == 1


def test_help_roda():
    r = subprocess.run([sys.executable, "treino/portao.py", "--help"], cwd=RAIZ, capture_output=True)
    assert r.returncode == 0 and b"--candidato" in r.stdout


def test_pipeline_ponta_a_ponta_sintetico(tmp_path, capsys):
    """Etapas 1 a 5 encadeadas pelos main(), só com arquivos sintéticos em tmp_path (nenhum em dados_locais/)."""
    openpyxl = pytest.importorskip("openpyxl")
    from sintetico_p8 import base_sintetica, corpus, gravar
    from treino import extrair_trechos, rotulos_fracos, treinar

    gravar(tmp_path / "corpus.csv", corpus(60))
    gravar(tmp_path / "holdout.csv", [{"reuniao": "R000"}])
    assert extrair_trechos.main(["--corpus", str(tmp_path / "corpus.csv"), "--holdout", str(tmp_path / "holdout.csv"),
                                 "--saida", str(tmp_path / "trechos.csv")]) == 0
    assert rotulos_fracos.main(["--trechos", str(tmp_path / "trechos.csv"), "--saida", str(tmp_path / "rotulos.csv"),
                                "--pasta-destilacao", str(tmp_path / "destilacao")]) == 0
    base = base_sintetica(tmp_path / "base.joblib")
    assert treinar.main(["--rotulos", str(tmp_path / "rotulos.csv"), "--base", str(base), "--holdout",
                         str(tmp_path / "holdout.csv"), "--ouro", str(tmp_path / "ouro_final.csv"),
                         "--candidatos", str(tmp_path / "candidatos")]) == 0

    livro = openpyxl.Workbook()
    aba = livro.active
    aba.append(["id", "texto", "padrao_1", "padrao_2", "interesse", "duvida"])
    for i, linha in enumerate(_ouro()):
        aba.append([f"G{i:03d}", linha["texto"], linha["padrao_1"], "", "sim" if linha["interesse"] == "1" else "nao", ""])
    livro.save(tmp_path / conciliar_ouro.ARQUIVOS[1])
    assert conciliar_ouro.main(["--pasta", str(tmp_path), "--relatorio", str(tmp_path / "ouro.md")]) == 0
    assert portao.main(["--ouro", str(tmp_path / "ouro_final.csv"), "--candidatos", str(tmp_path / "candidatos"),
                        "--atual", str(base), "--relatorio", str(tmp_path / "portao.md"), "--repeticoes", "200"]) == 0
    saida = capsys.readouterr().out
    assert "NÃO promover" in saida or "REPROVADO" in saida  # só a metade A: ouro parcial nunca promove
    assert "Copy-Item" not in saida
