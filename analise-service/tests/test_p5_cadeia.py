import pytest

from app.cadeia import executar_cadeia
from app.erros import AnaliseIndisponivel, ErroMotor
from app.schemas import AnaliseResponse

PEDIDO = object()  # a cadeia só repassa o pedido aos motores


def _corpo(**extra):
    return {"score": 70, "sentimento": "neutro", **extra}


def _ok(**extra):
    return lambda pedido: _corpo(**extra)


def _falha(excecao):
    def motor(pedido):
        raise excecao
    return motor


def test_primeiro_motor_responde():
    r = executar_cadeia(PEDIDO, [("llm1", _ok()), ("llm2", _ok())])
    assert isinstance(r, AnaliseResponse)
    assert r.motor == "llm1" and r.versaoContrato == "v3" and r.descartados == []
    assert [(t.motor, t.ok, t.erro) for t in r.tentativas] == [("llm1", True, None)]
    assert isinstance(r.tentativas[0].duracaoMs, int) and r.tentativas[0].duracaoMs >= 0


def test_o_codigo_escreve_motor_tentativas_e_versao_mesmo_se_o_motor_devolver():
    r = executar_cadeia(PEDIDO, [("llm2", _ok(motor="regras", tentativas=[], versaoContrato="v9"))])
    assert r.motor == "llm2" and r.versaoContrato == "v3"
    assert [t.motor for t in r.tentativas] == ["llm2"]


def test_descartados_calculados_pelo_codigo_sao_preservados():
    descartado = {"texto": "nao existe", "motivo": "evidencia_nao_localizada", "origem": "tema"}
    r = executar_cadeia(PEDIDO, [("llm1", _ok(descartados=[descartado]))])
    assert r.descartados[0].texto == "nao existe"


def test_llm1_falha_llm2_responde():
    r = executar_cadeia(PEDIDO, [("llm1", _falha(ErroMotor("timeout"))), ("llm2", _ok())])
    assert r.motor == "llm2"
    assert [(t.motor, t.ok, t.erro) for t in r.tentativas] == [("llm1", False, "timeout"), ("llm2", True, None)]
    assert not r.avisos


def test_contingencia_local_avisa():
    r = executar_cadeia(PEDIDO, [
        ("llm1", _falha(ErroMotor("nao_configurado"))), ("llm2", _falha(ErroMotor("autenticacao"))), ("local", _ok()),
    ])
    assert r.motor == "local" and r.avisos == ["contingencia_modelo_local"]
    assert [t.erro for t in r.tentativas] == ["nao_configurado", "autenticacao", None]


def test_contingencia_regras_avisa():
    r = executar_cadeia(PEDIDO, [("local", _falha(ErroMotor("modelo_indisponivel"))), ("regras", _ok())])
    assert r.motor == "regras" and r.avisos == ["contingencia_regras"]


def test_excecoes_viram_codigos_sem_mensagem_livre():
    with pytest.raises(AnaliseIndisponivel) as e:
        executar_cadeia(PEDIDO, [
            ("llm1", _falha(TimeoutError("trecho secreto"))),
            ("llm2", _falha(ValueError("trecho secreto"))),
            ("local", _falha(RuntimeError("trecho secreto"))),
        ])
    assert [t.erro for t in e.value.tentativas] == ["timeout", "erro_interno", "erro_interno"]
    assert all("secreto" not in t.model_dump_json() for t in e.value.tentativas)


def test_saida_fora_do_contrato_vira_schema_invalido_e_a_cadeia_segue():
    r = executar_cadeia(PEDIDO, [("llm1", lambda p: {"score": 70, "sentimento": "POSITIVO"}), ("llm2", _ok())])
    assert r.motor == "llm2" and r.tentativas[0].erro == "schema_invalido"


def test_todos_falham_levanta_analise_indisponivel_com_tentativas_em_ordem():
    motores = [(m, _falha(ErroMotor("erro_provedor"))) for m in ("llm1", "llm2", "local", "regras")]
    with pytest.raises(AnaliseIndisponivel) as e:
        executar_cadeia(PEDIDO, motores)
    assert [(t.motor, t.ok) for t in e.value.tentativas] == [(m, False) for m in ("llm1", "llm2", "local", "regras")]


def test_codigo_de_erro_invalido_nao_e_aceito():
    with pytest.raises(ValueError):
        ErroMotor("deu_ruim")
