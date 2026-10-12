import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.main import app
from app.schemas import AnaliseResponse, PedidoAnalise, SaidaLLM

CONTRATO = Path(__file__).resolve().parents[2] / "docs" / "contrato"


def _json(nome: str) -> dict:
    return json.loads((CONTRATO / nome).read_text(encoding="utf-8"))


# --- AC2: fixtures validam na resposta v3 ---

@pytest.mark.parametrize("nome", ["resposta-v3-llm.json", "resposta-v3-local.json", "resposta-v3-regras.json"])
def test_ac2_fixtures_validam(nome):
    AnaliseResponse.model_validate(_json(nome))


def test_resposta_llm_mantem_campos_do_contrato():
    r = AnaliseResponse.model_validate(_json("resposta-v3-llm.json"))
    assert r.motor == "llm1" and r.versaoContrato == "v3"
    assert r.papeis == {"1": "vendedor", "2": "cliente", "3": "cliente"}
    assert r.sentimentoSerie[0] == (2, -0.2)
    assert r.temas[0].confianca == 0.9 and r.eventosConduta[0].tipo == "desconto_fora_da_politica"


def test_local_e_regras_nao_tem_campos_so_de_llm():
    for nome in ("resposta-v3-local.json", "resposta-v3-regras.json"):
        r = AnaliseResponse.model_validate(_json(nome))
        assert all(t.confianca is None for t in r.temas)
        assert all(t.tratado is None for t in r.temas)


# --- enums fechados ---

def _com(alteracao):
    d = _json("resposta-v3-llm.json")
    alteracao(d)
    return d


@pytest.mark.parametrize(
    "alteracao",
    [
        lambda d: d.update(motor="LLM_PRIMARIA"),
        lambda d: d.update(sentimento="POSITIVO"),
        lambda d: d["temas"][0].update(padrao="inventado"),
        lambda d: d["temas"][0].update(tipos=["Risco"]),
        lambda d: d["temas"][0].update(tipos=["risco", "risco"]),
        lambda d: d["temas"][0].update(tipos=[]),
        lambda d: d["compromissos"][0].update(regra="amanha"),
        lambda d: d["descartados"][0].update(motivo="porque_sim"),
        lambda d: d["tentativas"][0].update(erro="deu_ruim"),
        lambda d: d["avisos"].append("aviso_novo"),
        lambda d: d.update(score=101),
        lambda d: d["temas"][0].update(confianca=1.5),
        lambda d: d["papeis"].update({"4": "gerente"}),
    ],
    ids=["motor", "sentimento", "padrao", "tipos_caixa", "tipos_repetido", "tipos_vazio", "regra",
         "motivo", "erro", "aviso", "score", "confianca", "papel"],
)
def test_valor_fora_da_lista_e_rejeitado(alteracao):
    with pytest.raises(ValidationError):
        AnaliseResponse.model_validate(_com(alteracao))


def test_regra_null_e_aceita():
    d = _com(lambda d: d["compromissos"][0].update(regra=None))
    assert AnaliseResponse.model_validate(d).compromissos[0].regra is None


# --- SaidaLLM: só o que a LLM preenche, compatível com saída estruturada estrita ---

def test_saida_llm_nao_tem_campos_do_codigo():
    campos = set(SaidaLLM.model_fields)
    assert not campos & {"motor", "tentativas", "versaoContrato", "descartados", "avisos"}
    assert {"score", "sentimento", "papeis", "resumo", "interesse", "proximosPassos", "temas",
            "compromissos", "sentimentoSerie", "eventosConduta"} <= campos


def _varrer(no, achados):
    if isinstance(no, dict):
        if "prefixItems" in no:
            achados.append("tupla")
        if "additionalProperties" in no and no["additionalProperties"] is not False:
            achados.append("additionalProperties livre")
        if no.get("type") == "object" and "properties" in no:
            if set(no.get("required", [])) != set(no["properties"]):
                achados.append(f"campo opcional em {sorted(no['properties'])}")
            if no.get("additionalProperties") is not False:
                achados.append("objeto sem additionalProperties=false")
        for v in no.values():
            _varrer(v, achados)
    elif isinstance(no, list):
        for v in no:
            _varrer(v, achados)


def test_saida_llm_schema_e_estrito():
    achados: list[str] = []
    _varrer(SaidaLLM.model_json_schema(), achados)
    assert achados == []


def test_saida_llm_usa_listas_de_objetos():
    s = SaidaLLM.model_validate({
        "score": 70, "sentimento": "neutro",
        "papeis": [{"locutor": 1, "papel": "vendedor"}],
        "resumo": "r", "interesse": [], "proximosPassos": [],
        "temas": [], "compromissos": [],
        "sentimentoSerie": [{"turno": 2, "valor": -0.2}],
        "eventosConduta": [],
    })
    assert s.papeis[0].papel == "vendedor" and s.sentimentoSerie[0].valor == -0.2


# --- Pedido: extras passam; limites e padrões ---

def test_pedido_extras_passa():
    PedidoAnalise.model_validate(_json("pedido-v3-extras.json"))


def test_pedido_ignora_campos_desconhecidos():
    d = _json("pedido-v3.json") | {"campoNovo": 1}
    PedidoAnalise.model_validate(d)


def _turnos(n):
    return [{"n": i, "locutor": 1, "texto": "oi"} for i in range(1, n + 1)]


@pytest.fixture
def cliente(pipeline_versao):
    pipeline_versao("mock")
    return TestClient(app)


def test_padrao_fora_da_lista_da_422_padrao_desconhecido(cliente):
    r = cliente.post("/analisar", json={"turnos": _turnos(1), "padroes": ["inventado"]})
    assert r.status_code == 422 and r.json()["codigo"] == "padrao_desconhecido"


@pytest.mark.parametrize(
    "corpo",
    [
        {"turnos": _turnos(3001)},
        {"turnos": [{"n": 1, "locutor": 1, "texto": "x" * 5001}]},
        {"turnos": [{"n": 1, "locutor": 1, "texto": "oi"}, {"n": 3, "locutor": 1, "texto": "oi"}]},
        {"turnos": _turnos(1), "contraexemplos": [{"padrao": "renovacao", "texto": "x", "motivo": "outro"}] * 51},
        {"turnos": _turnos(1), "contraexemplos": [{"padrao": "renovacao", "texto": "x" * 501, "motivo": "outro"}]},
        {"turnos": _turnos(1), "contraexemplos": [{"padrao": "renovacao", "texto": "x", "motivo": "porque"}]},
    ],
    ids=["turnos_demais", "texto_longo", "n_nao_consecutivo", "itens_demais", "campo_longo", "motivo_invalido"],
)
def test_limites_do_pedido_dao_422_pedido_invalido(cliente, corpo):
    r = cliente.post("/analisar", json=corpo)
    assert r.status_code == 422 and r.json()["codigo"] == "pedido_invalido"
