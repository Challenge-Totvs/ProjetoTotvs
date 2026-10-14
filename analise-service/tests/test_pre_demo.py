"""scripts/pre_demo.py: regras de OK/FALHOU e relatório, sem rede (a chamada HTTP é injetada). Tudo sintético."""
import importlib.util
import json
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
RESPOSTA_V3 = RAIZ.parent / "docs" / "contrato" / "resposta-v3-llm.json"
HEALTH = RAIZ.parent / "docs" / "contrato" / "health.json"
SIMILARES = RAIZ.parent / "docs" / "contrato" / "resposta-similares.json"


def _carregar():
    spec = importlib.util.spec_from_file_location("pre_demo", RAIZ / "scripts" / "pre_demo.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


pd = _carregar()


def _json(caminho: Path) -> dict:
    return json.loads(caminho.read_text(encoding="utf-8"))


def _resposta(motor: str = "llm1", **extra) -> dict:
    return {"motor": motor, "tentativas": [{"motor": motor, "ok": True}], "versaoContrato": "v3",
            "temas": [{"padrao": "preco_objecao", "turno": 2, "turnoFim": 3, "texto": "texto sintetico qualquer"}],
            "interesse": [{"turno": 4, "texto": "x", "citacao": "x"}], "compromissos": [], **extra}


# ------------------------------------------------------------------ (a) health

def test_health_da_fixture_do_contrato_e_ok():
    item = pd.checar_health(200, _json(HEALTH))
    assert item.ok
    assert "llm1=ok llm2=ok local=ok regras=ok" in item.detalhe


@pytest.mark.parametrize("mudar", [
    lambda h: h["motores"][0].update(ok=False),          # llm1 caída
    lambda h: h["motores"][2].update(ok=False),          # local caído
    lambda h: h.update(status="degradado"),
    lambda h: h["motores"].pop(),                        # regras ausente
])
def test_health_falha_se_algum_motor_nao_esta_ok_ou_status_nao_e_ok(mudar):
    corpo = _json(HEALTH)
    mudar(corpo)
    assert not pd.checar_health(200, corpo).ok


def test_health_falha_com_http_diferente_de_200():
    item = pd.checar_health(500, None)
    assert not item.ok and item.detalhe == "http=500"


# ------------------------------------------------------------------ (b)/(c) analisar

def test_analise_ok_com_a_fixture_v3_do_contrato():
    corpo = _json(RESPOSTA_V3)
    maior = max(pd.turnos_citados(corpo))
    item = pd.checar_analise("b", "x", 200, corpo, maior, 1.23)
    assert item.ok, item.detalhe
    assert item.segundos == 1.23


def test_analise_ok_e_conta_citacoes_e_tentativas():
    item = pd.checar_analise("b", "x", 200, _resposta(), 12, 2.0)
    assert item.ok
    assert "temas=1" in item.detalhe and "citacoes=3" in item.detalhe and "turnos_invalidos=0" in item.detalhe
    assert "tentativas=llm1:ok" in item.detalhe


@pytest.mark.parametrize("corpo, motivo", [
    (_resposta(versaoContrato="v2"), "versaoContrato"),
    (_resposta(temas=[]), "sem_temas"),
    (_resposta(temas=[{"turno": 13, "turnoFim": 13}]), "turno_invalido"),
    (_resposta(temas=[{"turno": 2, "turnoFim": 2}], interesse=[{"turno": 0}]), "turno_invalido"),
    (_resposta(temas=[{"turno": 2, "turnoFim": 2}], eventosConduta=[{"turno": "3"}]), "turno_invalido"),
    (_resposta(motor="llm2"), "motor!=llm1"),
])
def test_analise_falha_pelo_motivo_certo(corpo, motivo):
    item = pd.checar_analise("b", "x", 200, corpo, 12, 1.0)
    assert not item.ok
    assert motivo in item.detalhe.split("falhou=")[1]


def test_analise_aceita_outro_motor_esperado():
    assert pd.checar_analise("b", "x", 200, _resposta(motor="llm2"), 12, 1.0, motor_esperado="llm2").ok


def test_analise_503_mostra_so_http_e_codigo():
    item = pd.checar_analise("c", "x", 503, {"codigo": "analise_indisponivel", "mensagem": "texto"}, 12, 9.0)
    assert not item.ok
    assert item.detalhe == "http=503 codigo=analise_indisponivel"


def test_detalhe_nunca_traz_texto_da_resposta():
    segredo = "FRASE_SINTETICA_QUE_NAO_PODE_APARECER"
    corpo = _resposta(resumo=segredo, temas=[{"turno": 1, "turnoFim": 1, "texto": segredo, "titulo": segredo}])
    relatorio = pd.formatar_relatorio([pd.checar_analise("b", "x", 200, corpo, 12, 1.0)])
    assert segredo not in relatorio


# ------------------------------------------------------------------ (d) similares

IDS = {"sim-1", "sim-2", "sim-3"}


def test_similares_ok():
    corpo = {"similares": [{"id": "sim-1", "score": 0.8}, {"id": "sim-3", "score": 0.1}], "versaoContrato": "v3"}
    item = pd.checar_similares(200, corpo, IDS, 3, 0.05)
    assert item.ok and "similares=2" in item.detalhe


def test_similares_fixture_do_contrato_tem_o_formato_certo():
    corpo = _json(SIMILARES)
    ids = {s["id"] for s in corpo["similares"]}
    assert pd.checar_similares(200, corpo, ids, 3, 0.1).ok


@pytest.mark.parametrize("corpo, motivo", [
    ({"similares": [{"id": "sim-1", "score": 0.5}], "versaoContrato": "v3", "extra": 1}, "campos"),
    ({"similares": [{"id": "sim-1", "score": 0.5}], "versaoContrato": "v2"}, "versaoContrato"),
    ({"similares": [{"id": "outro", "score": 0.5}], "versaoContrato": "v3"}, "itens"),
    ({"similares": [{"id": "sim-1", "score": 1.5}], "versaoContrato": "v3"}, "itens"),
    ({"similares": [{"id": "sim-1", "score": 0.5, "texto": "x"}], "versaoContrato": "v3"}, "itens"),
    ({"similares": [{"id": "sim-1", "score": 0.1}, {"id": "sim-2", "score": 0.9}], "versaoContrato": "v3"}, "ordem"),
    ({"similares": [], "versaoContrato": "v3"}, "nenhum_similar"),
])
def test_similares_falha_pelo_motivo_certo(corpo, motivo):
    item = pd.checar_similares(200, corpo, IDS, 3, 0.1)
    assert not item.ok
    assert motivo in item.detalhe.split("falhou=")[1]


def test_similares_falha_acima_do_top_k():
    corpo = {"similares": [{"id": i, "score": 0.5} for i in ("sim-1", "sim-2", "sim-3")], "versaoContrato": "v3"}
    assert not pd.checar_similares(200, corpo, IDS, 2, 0.1).ok


def test_similares_sem_lista():
    assert not pd.checar_similares(200, {"similares": None, "versaoContrato": "v3"}, IDS, 3, 0.1).ok


# ------------------------------------------------------------------ (e) relatório e veredito

def test_relatorio_pronto():
    itens = [pd.Item("a", "GET /health", True, "status=ok"), pd.Item("b", "POST /analisar", True, "http=200", 3.21)]
    texto = pd.formatar_relatorio(itens)
    assert texto.splitlines()[0].startswith("OK")
    assert "3.2s" in texto
    assert texto.splitlines()[-1] == "e) PRONTO PARA A DEMO"


def test_relatorio_nao_pronto_lista_o_que_falhou():
    itens = [pd.Item("a", "GET /health", False, "status=degradado"), pd.Item("b", "POST /analisar", True, "ok", 1.0),
             pd.Item("d", "POST /similares", False, "http=500", 0.1)]
    texto = pd.formatar_relatorio(itens)
    assert texto.splitlines()[0].startswith("FALHOU")
    assert texto.splitlines()[-1] == "e) NAO PRONTO: a) GET /health; d) POST /similares"
    assert pd.veredito(itens) == (False, ["a) GET /health", "d) POST /similares"])


# ------------------------------------------------------------------ main, com a chamada injetada

def _servico_falso(resposta_analise: dict, health: dict | None = None):
    chamadas = []

    def chamar(metodo, caminho, corpo):
        chamadas.append((metodo, caminho, len(corpo["turnos"]) if corpo and "turnos" in corpo else None))
        if caminho == "/health":
            return 200, health or _json(HEALTH), 0.01
        if caminho == "/similares":
            return 200, {"similares": [{"id": "sim-1", "score": 0.9}], "versaoContrato": "v3"}, 0.02
        return 200, resposta_analise, 1.5

    return chamar, chamadas


def test_main_pronto_sai_com_0_e_manda_curta_e_grande(capsys):
    chamar, chamadas = _servico_falso(_resposta())
    assert pd.main([], chamar=chamar) == 0
    saida = capsys.readouterr().out
    assert saida.strip().splitlines()[-1] == "e) PRONTO PARA A DEMO"
    assert [c[:2] for c in chamadas] == [("GET", "/health"), ("POST", "/analisar"), ("POST", "/analisar"),
                                         ("POST", "/similares")]
    assert chamadas[1][2] == 12 and chamadas[2][2] == 399  # pedido-v3.json e a transcrição grande sintética


def test_main_nao_pronto_sai_com_2(capsys):
    chamar, _ = _servico_falso(_resposta(motor="llm2"))
    assert pd.main([], chamar=chamar) == 2
    assert "NAO PRONTO" in capsys.readouterr().out


def test_main_servico_fora_do_ar_avisa_em_uma_linha_e_sai_com_1(capsys):
    def chamar(*_):
        raise pd.ServicoForaDoAr("URLError")

    assert pd.main(["--porta", "8123"], chamar=chamar) == 1
    saida = capsys.readouterr().out.strip().splitlines()
    assert len(saida) == 1 and "fora do ar" in saida[0] and ":8123" in saida[0]


def test_chamada_real_sem_servico_vira_servico_fora_do_ar():
    chamar = pd.criar_chamada("http://127.0.0.1:9", timeout=0.5)  # porta 9 (discard): nada escuta em loopback
    with pytest.raises(pd.ServicoForaDoAr):
        chamar("GET", "/health", None)
