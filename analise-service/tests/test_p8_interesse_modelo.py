"""P8 etapa 6 — encaixe do classificador de interesse no motor local: DESLIGADO por padrão, com fallback."""
import logging
import unicodedata
from pathlib import Path

import joblib
import numpy as np
import pytest

from app import config
from app.engines import modelo_local_engine as local
from app.schemas import AnaliseResponse, PedidoAnalise
from sintetico_p8 import ModeloInteresseFixo, ModeloQueFalha

RAIZ = Path(__file__).resolve().parent.parent
TEXTOS = [
    "Isso ajuda bastante, gostei da demonstração.",  # palavra-chave de interesse, risco baixo
    "O orçamento foi aprovado pela diretoria ontem.",  # sem palavra-chave, mas o modelo sintético vê interesse
    "Excelente, mas vamos cancelar mesmo assim.",  # palavra-chave, risco alto (vetado no filtro atual)
]
P_RISCO = [0.05, 0.1, 0.9]


class RiscoFalso:
    def predict_proba(self, trechos):
        p = np.array(P_RISCO[: len(trechos)])
        return np.column_stack([1 - p, p])


@pytest.fixture(autouse=True)
def risco_falso(monkeypatch):
    carregar = local._carregar  # o cache do joblib.load é por caminho: limpo antes e depois
    monkeypatch.setattr(local, "carregar_pipeline", lambda caminho=None: RiscoFalso())
    carregar.cache_clear()
    yield
    carregar.cache_clear()


def _pedido(textos=TEXTOS):
    turnos = [{"n": i, "locutor": 1 + i % 2, "texto": t} for i, t in enumerate(textos, start=1)]
    return PedidoAnalise.model_validate({"turnos": turnos})


def _turnos_de_interesse(pedido=None):
    return [i["turno"] for i in local.analisar(pedido or _pedido())["interesse"]]


@pytest.fixture
def artefato_valido(tmp_path):
    caminho = tmp_path / "classificador_interesse.joblib"
    joblib.dump(ModeloInteresseFixo(), caminho)
    return caminho


FALLBACK = [1]  # filtro atual: palavra-chave v2 E risco < 0,3


def test_flag_ausente_usa_o_fallback_mesmo_com_artefato_e_candidato(monkeypatch, tmp_path, artefato_valido):
    candidatos = tmp_path / "dados_locais" / "candidatos" / "2026-10-14"
    candidatos.mkdir(parents=True)
    joblib.dump(ModeloInteresseFixo(), candidatos / "interesse.joblib")
    monkeypatch.setattr(config, "CAMINHO_MODELO_INTERESSE", artefato_valido)  # até o promovido existe
    monkeypatch.delenv("INTERESSE_MODELO", raising=False)
    chamado = []
    monkeypatch.setattr(local, "_carregar", lambda caminho: chamado.append(caminho) or RiscoFalso())
    assert config.interesse_modelo_ligado() is False
    assert _turnos_de_interesse() == FALLBACK
    assert chamado == []  # nenhum artefato de interesse foi sequer carregado


@pytest.mark.parametrize("valor", ["0", "", "true", "sim", " 0 "])
def test_flag_diferente_de_1_e_desligada(monkeypatch, artefato_valido, valor):
    monkeypatch.setattr(config, "CAMINHO_MODELO_INTERESSE", artefato_valido)
    monkeypatch.setenv("INTERESSE_MODELO", valor)
    assert config.interesse_modelo_ligado() is False and _turnos_de_interesse() == FALLBACK


def test_flag_1_com_artefato_valido_chama_o_modelo(monkeypatch, artefato_valido):
    monkeypatch.setattr(config, "CAMINHO_MODELO_INTERESSE", artefato_valido)
    monkeypatch.setenv("INTERESSE_MODELO", "1")
    saida = local.analisar(_pedido())
    assert [i["turno"] for i in saida["interesse"]] == [2]  # o modelo substitui o filtro (sem palavra-chave)
    assert saida["interesse"][0]["citacao"] == TEXTOS[1] and saida["interesse"][0]["texto"] == local.TEXTO_DO_INTERESSE_MODELO
    AnaliseResponse(**saida, motor="local", tentativas=[{"motor": "local", "ok": True}])


def test_interface_recebe_n_e_texto_nfc_e_devolve_p_por_turno(monkeypatch, artefato_valido):
    monkeypatch.setattr(config, "CAMINHO_MODELO_INTERESSE", artefato_valido)
    monkeypatch.setenv("INTERESSE_MODELO", "1")
    decomposto = unicodedata.normalize("NFD", "Orçamento aprovado.")
    trechos = [(1, unicodedata.normalize("NFC", decomposto)), (4, "Bom dia.")]
    p = local.prever_interesse(trechos)
    assert set(p) == {1, 4} and p[1] == pytest.approx(0.9) and p[4] == pytest.approx(0.1)


def test_limiar_nomeado_decide(monkeypatch, artefato_valido):
    monkeypatch.setattr(config, "CAMINHO_MODELO_INTERESSE", artefato_valido)
    monkeypatch.setenv("INTERESSE_MODELO", "1")
    monkeypatch.setattr(local, "LIMIAR_P_INTERESSE", 0.95)
    assert _turnos_de_interesse() == []
    monkeypatch.setattr(local, "LIMIAR_P_INTERESSE", 0.05)
    assert _turnos_de_interesse() == [1, 2, 3]


def test_flag_1_sem_artefato_cai_no_fallback(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(config, "CAMINHO_MODELO_INTERESSE", tmp_path / "nao-existe.joblib")
    monkeypatch.setenv("INTERESSE_MODELO", "1")
    with caplog.at_level(logging.WARNING):
        assert _turnos_de_interesse() == FALLBACK
    assert "filtro atual" in caplog.text


def test_flag_1_com_artefato_corrompido_cai_no_fallback(monkeypatch, tmp_path, caplog):
    corrompido = tmp_path / "classificador_interesse.joblib"
    corrompido.write_text("nao e um modelo", encoding="utf-8")
    monkeypatch.setattr(config, "CAMINHO_MODELO_INTERESSE", corrompido)
    monkeypatch.setenv("INTERESSE_MODELO", "1")
    with caplog.at_level(logging.WARNING):
        assert _turnos_de_interesse() == FALLBACK
    assert all(t not in caplog.text for t in TEXTOS)


def test_flag_1_com_modelo_que_falha_cai_no_fallback(monkeypatch, tmp_path):
    caminho = tmp_path / "classificador_interesse.joblib"
    joblib.dump(ModeloQueFalha(), caminho)
    monkeypatch.setattr(config, "CAMINHO_MODELO_INTERESSE", caminho)
    monkeypatch.setenv("INTERESSE_MODELO", "1")
    assert _turnos_de_interesse() == FALLBACK


def test_artefato_de_interesse_fica_em_app_modelos_e_nao_em_dados_locais():
    assert config.CAMINHO_MODELO_INTERESSE == RAIZ / "app" / "modelos" / "classificador_interesse.joblib"
    assert "dados_locais" not in config.CAMINHO_MODELO_INTERESSE.parts


def test_flag_nao_aparece_no_env_example():
    assert "INTERESSE_MODELO" not in (RAIZ / ".env.example").read_text(encoding="utf-8")


def test_padrao_do_ambiente_de_teste_e_desligado():
    assert config.interesse_modelo_ligado() is False
