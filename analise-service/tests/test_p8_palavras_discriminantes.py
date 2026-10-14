"""P8 — palavras_discriminantes.py: top-N palavras por classe, com modelos SINTÉTICOS (sem texto de trecho real)."""
import json
import subprocess
import sys
from pathlib import Path

import joblib
import pytest

from treino import palavras_discriminantes as pd

RAIZ = Path(__file__).resolve().parent.parent


def _pipeline_sintetico():
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline

    textos = [
        "cliente reclamou do preco alto e quer cancelar",
        "vai cancelar o contrato por causa do preco",
        "preco muito caro, pensando em cancelar tudo",
        "insatisfeito com o suporte, quer cancelar o plano",
        "gostou da reuniao e elogiou o suporte",
        "ficou satisfeito e quer continuar o plano",
        "elogiou o atendimento e a equipe de suporte",
        "achou tudo otimo e quer renovar o contrato",
    ]
    y = [1, 1, 1, 1, 0, 0, 0, 0]
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(min_df=1)),
        ("clf", LogisticRegression(max_iter=1000, random_state=42)),
    ])
    pipeline.fit(textos, y)
    return pipeline


def test_palavras_de_maior_peso_formato():
    pipeline = _pipeline_sintetico()
    resultado = pd.palavras_de_maior_peso(pipeline, top=5)
    assert set(resultado) == {"positivas", "negativas"}
    assert len(resultado["positivas"]) <= 5 and len(resultado["negativas"]) <= 5
    assert all(c > 0 for _, c in resultado["positivas"])
    assert all(c < 0 for _, c in resultado["negativas"])
    # "cancelar"/"preco" devem pesar para a classe 1 (risco), "suporte"/"elogiou" para a classe 0
    positivas = {p for p, _ in resultado["positivas"]}
    negativas = {p for p, _ in resultado["negativas"]}
    assert positivas & {"cancelar", "preco"}
    assert negativas & {"suporte", "elogiou", "otimo", "satisfeito"}


def test_ordenado_por_peso_absoluto_decrescente():
    pipeline = _pipeline_sintetico()
    resultado = pd.palavras_de_maior_peso(pipeline, top=20)
    pesos_pos = [c for _, c in resultado["positivas"]]
    pesos_neg = [c for _, c in resultado["negativas"]]
    assert pesos_pos == sorted(pesos_pos, reverse=True)
    assert pesos_neg == sorted(pesos_neg)


def test_respeita_top(tmp_path):
    pipeline = _pipeline_sintetico()
    resultado = pd.palavras_de_maior_peso(pipeline, top=2)
    assert len(resultado["positivas"]) <= 2 and len(resultado["negativas"]) <= 2


def test_main_escreve_relatorio_e_nao_vaza_frase_inteira(tmp_path, capsys):
    pasta = tmp_path / "candidatos" / "2026-10-14"
    pasta.mkdir(parents=True)
    joblib.dump(_pipeline_sintetico(), pasta / "risco.joblib")
    joblib.dump(_pipeline_sintetico(), pasta / "interesse.joblib")
    (pasta / "metadata.json").write_text(json.dumps({"pasta": pasta.name}), encoding="utf-8")

    assert pd.main(["--candidatos", str(tmp_path / "candidatos"), "--saida", str(tmp_path / "palavras.md"),
                    "--top", "10"]) == 0
    saida = capsys.readouterr().out
    resumo = json.loads(saida)
    assert resumo["candidato"] == "2026-10-14"
    assert set(resumo["grupos"]) == {"risco", "interesse"}

    relatorio = (tmp_path / "palavras.md").read_text(encoding="utf-8")
    assert "Palavras de maior peso por classe" in relatorio
    assert "cancelar" in relatorio or "preco" in relatorio
    # nenhuma frase completa do corpus sintético deve aparecer inteira (só palavras/n-gramas)
    assert "cliente reclamou do preco alto e quer cancelar" not in relatorio


def test_sem_candidato_devolve_1(tmp_path):
    assert pd.main(["--candidatos", str(tmp_path / "vazio")]) == 1


def test_grupo_faltando_devolve_1(tmp_path, capsys):
    pasta = tmp_path / "candidatos" / "2026-10-14"
    pasta.mkdir(parents=True)
    joblib.dump(_pipeline_sintetico(), pasta / "risco.joblib")
    (pasta / "metadata.json").write_text(json.dumps({"pasta": pasta.name}), encoding="utf-8")
    assert pd.main(["--candidatos", str(tmp_path / "candidatos")]) == 1
    assert "interesse" in capsys.readouterr().out


def test_help_roda():
    r = subprocess.run([sys.executable, "treino/palavras_discriminantes.py", "--help"], cwd=RAIZ, capture_output=True)
    assert r.returncode == 0 and b"--top" in r.stdout
