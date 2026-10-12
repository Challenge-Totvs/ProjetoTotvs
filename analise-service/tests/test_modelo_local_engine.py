import numpy as np
import pytest

from app import config
from app.engines import modelo_local_engine
from app.erros import ErroMotor
from app.schemas import AnaliseResponse, PedidoAnalise


def _pedido(textos, **extra):
    turnos = [{"n": i, "locutor": 1 + i % 2, "texto": t} for i, t in enumerate(textos, start=1)]
    return PedidoAnalise.model_validate({"turnos": turnos, **extra})


class PipelineFalso:
    """Devolve a probabilidade de risco combinada, na ordem em que os trechos chegam."""

    def __init__(self, probabilidades):
        self.probabilidades = probabilidades
        self.recebido = None

    def predict_proba(self, trechos):
        self.recebido = list(trechos)
        p = np.array(self.probabilidades[: len(trechos)])
        return np.column_stack([1 - p, p])


@pytest.fixture
def pipeline_falso(monkeypatch):
    def instalar(probabilidades):
        falso = PipelineFalso(probabilidades)
        monkeypatch.setattr(modelo_local_engine, "carregar_pipeline", lambda caminho=None: falso)
        return falso

    return instalar


TRANSCRICAO_B = [
    "Bom dia, como está o uso do sistema?",
    "Bom dia. Sendo bem sincero, não estamos satisfeitos.",
    "O suporte demora demais para responder, já abrimos 3 chamados esse mês.",
    "Estamos avaliando seriamente cancelar o contrato e migrar para outro fornecedor.",
]


def test_artefato_real_responde_e_a_saida_vira_analise_response():
    saida = modelo_local_engine.analisar(_pedido(TRANSCRICAO_B))
    r = AnaliseResponse(**saida, motor="local", tentativas=[{"motor": "local", "ok": True}])
    assert 0 <= r.score <= 100 and r.sentimento in ("positivo", "neutro", "negativo")
    assert {"suporte_insatisfacao", "cancelamento_citado"} <= {t.padrao for t in r.temas}
    assert all(t.tratado is None and t.confianca is None for t in r.temas)


def test_divide_por_turno_e_calcula_o_score_pelo_risco(pipeline_falso):
    falso = pipeline_falso([0.9, 0.1, 0.8, 0.2])
    textos = ["Primeiro turno qualquer.", "Segundo turno qualquer.", "Terceiro turno qualquer.", "Quarto turno qualquer."]
    saida = modelo_local_engine.analisar(_pedido(textos))
    assert falso.recebido == textos
    assert saida["score"] == 50 and saida["sentimento"] == "neutro"


def test_score_100_sem_risco_e_0_com_tudo_risco(pipeline_falso):
    pipeline_falso([0.0, 0.0])
    assert modelo_local_engine.analisar(_pedido(["Turno um comum.", "Turno dois comum."]))["score"] == 100
    pipeline_falso([1.0, 1.0])
    assert modelo_local_engine.analisar(_pedido(["Turno um comum.", "Turno dois comum."]))["score"] == 0


def test_interesse_exige_palavra_chave_e_baixo_risco_no_classificador(pipeline_falso):
    pipeline_falso([0.05, 0.9, 0.1])
    textos = ["Isso ajuda bastante, gostei.", "Excelente, mas vamos cancelar mesmo assim.", "Gostei, podemos seguir."]
    saida = modelo_local_engine.analisar(_pedido(textos))
    assert [i["turno"] for i in saida["interesse"]] == [1, 3]


def test_temas_vem_das_expressoes_e_nao_do_classificador(pipeline_falso):
    pipeline_falso([0.0, 0.0])
    saida = modelo_local_engine.analisar(_pedido(["Bom dia, tudo bem?", "Precisamos de um treinamento para a equipe."]))
    assert [t["padrao"] for t in saida["temas"]] == ["treinamento"]


def test_sem_artefato_levanta_modelo_indisponivel(monkeypatch, tmp_path):
    monkeypatch.setattr(config, "CAMINHO_MODELO_LOCAL", tmp_path / "nao-existe.joblib")
    with pytest.raises(ErroMotor) as e:
        modelo_local_engine.analisar(_pedido(TRANSCRICAO_B))
    assert e.value.codigo == "modelo_indisponivel"


def test_artefato_corrompido_levanta_modelo_indisponivel(monkeypatch, tmp_path):
    corrompido = tmp_path / "corrompido.joblib"
    corrompido.write_text("nao e um modelo", encoding="utf-8")
    monkeypatch.setattr(config, "CAMINHO_MODELO_LOCAL", corrompido)
    with pytest.raises(ErroMotor) as e:
        modelo_local_engine.analisar(_pedido(TRANSCRICAO_B))
    assert e.value.codigo == "modelo_indisponivel"


def test_turnos_em_branco_levantam_entrada_sem_trechos(pipeline_falso):
    pipeline_falso([0.0])
    with pytest.raises(ErroMotor) as e:
        modelo_local_engine.analisar(_pedido(["   ", "\n"]))
    assert e.value.codigo == "entrada_sem_trechos"
