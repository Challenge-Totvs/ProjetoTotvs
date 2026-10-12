"""scripts/inspecionar_modelo.py: imprime só estrutura e hiperparâmetros, nunca o vocabulário aprendido."""
import importlib.util
from pathlib import Path

import joblib
import pytest
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

RAIZ = Path(__file__).resolve().parent.parent
SENTINELA = "palavrasentinelasecreta"  # termo que só existe no vocabulário aprendido


@pytest.fixture
def inspecionar():
    spec = importlib.util.spec_from_file_location("inspecionar_modelo", RAIZ / "scripts" / "inspecionar_modelo.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture
def artefato(tmp_path):
    textos = [f"{SENTINELA} cancelar contrato", "tudo bem obrigado", f"{SENTINELA} muito caro", "bom dia equipe"]
    pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True, stop_words=["de", "a"])),
        ("clf", LogisticRegression(C=2.5, class_weight="balanced", max_iter=300)),
    ])
    pipeline.fit(textos, [1, 0, 1, 0])
    caminho = tmp_path / "modelo.joblib"
    joblib.dump(pipeline, caminho)
    return caminho


def test_imprime_steps_hiperparametros_e_classes(inspecionar, artefato, capsys):
    assert inspecionar.main([str(artefato)]) == 0
    saida = capsys.readouterr().out
    assert "tfidf" in saida and "TfidfVectorizer" in saida and "LogisticRegression" in saida
    assert "ngram_range" in saida and "(1, 2)" in saida and "sublinear_tf" in saida
    assert "'C': 2.5" in saida or "C: 2.5" in saida
    assert "classes_" in saida and "[0, 1]" in saida
    assert "tamanho_vocabulario" in saida


def test_nunca_imprime_vocabulario_nem_stop_words(inspecionar, artefato, capsys):
    inspecionar.main([str(artefato)])
    saida = capsys.readouterr().out
    assert SENTINELA not in saida and "cancelar" not in saida and "obrigado" not in saida
    assert "stop_words" in saida and "len=2" in saida


def test_artefato_inexistente_nao_levanta_e_devolve_1(inspecionar, tmp_path, capsys):
    assert inspecionar.main([str(tmp_path / "nao_existe.joblib")]) == 1
    assert "nao_encontrado" in capsys.readouterr().out
