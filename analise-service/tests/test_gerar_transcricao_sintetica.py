"""scripts/gerar_transcricao_sintetica.py e a entrada alternativa do smoke. Tudo sintético, sem rede."""
import importlib.util
import json
from pathlib import Path

import pytest

from app.engines import regras_engine
from app.schemas import PedidoAnalise

RAIZ = Path(__file__).resolve().parent.parent


def _carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, RAIZ / "scripts" / f"{nome}.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture
def gerador():
    return _carregar("gerar_transcricao_sintetica")


@pytest.fixture
def smoke():
    return _carregar("smoke_llm")


def _total(dados):
    return sum(len(t["texto"]) for t in dados["turnos"])


@pytest.mark.parametrize("caracteres", [3_000, 20_000, 72_000])
def test_respeita_o_tamanho_pedido(gerador, caracteres):
    dados = gerador.gerar(caracteres=caracteres)
    pedido = PedidoAnalise.model_validate(dados)
    assert caracteres <= _total(dados) <= caracteres + 600
    assert [t.n for t in pedido.turnos] == list(range(1, len(pedido.turnos) + 1))
    assert len(pedido.turnos) <= 3000 and max(len(t.texto) for t in pedido.turnos) <= 5000


def test_padrao_e_o_p90(gerador):
    assert gerador.CARACTERES_P90 == 72_000
    assert 72_000 <= _total(gerador.gerar()) <= 72_600


def test_e_deterministico_e_varia_com_a_semente(gerador):
    assert gerador.gerar(5_000, semente=1) == gerador.gerar(5_000, semente=1)
    assert gerador.gerar(5_000, semente=1) != gerador.gerar(5_000, semente=2)


def test_cada_frase_plantada_casa_com_o_proprio_padrao(gerador):
    assert set(gerador.PLANTADOS) == set(regras_engine.EXPRESSOES)  # os 14
    for padrao, modelo in gerador.PLANTADOS.items():
        frase = modelo.format(m="financeiro", a="a diretoria", t="na terça")
        assert regras_engine.EXPRESSOES[padrao].search(regras_engine.dobrar(frase)), padrao


def test_fundo_neutro_nao_casa_com_nenhum_padrao(gerador):
    import random

    rng = random.Random(7)
    for _ in range(300):
        dobrado = regras_engine.dobrar(gerador._turno_neutro(rng))
        assert not any(e.search(dobrado) for e in regras_engine.EXPRESSOES.values())
        assert not regras_engine.EXPRESSAO_INTERESSE.search(dobrado)


def test_os_temas_achados_sao_exatamente_os_plantados(gerador):
    padroes = ("preco_objecao", "renovacao", "fiscal_problema", "upgrade_licencas")
    dados = gerador.gerar(20_000, padroes=padroes)
    achados = {t["padrao"]: t["turno"] for t in regras_engine.analisar(PedidoAnalise.model_validate(dados))["temas"]}
    assert achados == gerador.plantados(dados, padroes)
    assert set(achados) == set(padroes)


def test_plantados_espalhados_ate_o_fim_da_reuniao(gerador):
    dados = gerador.gerar()
    turnos = sorted(gerador.plantados(dados).values())
    assert len(turnos) == len(gerador.PADROES_PADRAO)
    assert turnos[-1] >= 0.6 * len(dados["turnos"])


def test_padrao_desconhecido_falha_com_mensagem(gerador):
    with pytest.raises(ValueError, match="padrão sem frase plantada"):
        gerador.gerar(1_000, padroes=("nao_existe",))


def test_main_grava_arquivo_e_imprime_so_contagens(gerador, tmp_path, capsys):
    destino = tmp_path / "transcricao.json"
    assert gerador.main(["--caracteres", "3000", "--saida", str(destino), "--padroes", "renovacao"]) == 0
    saida = capsys.readouterr().out
    dados = json.loads(destino.read_text(encoding="utf-8"))
    assert all(t["texto"] not in saida for t in dados["turnos"])
    resumo = json.loads(saida)
    assert resumo["turnos"] == len(dados["turnos"]) and resumo["caracteres"] >= 3000
    assert list(resumo["plantados"]) == ["renovacao"]


def test_saida_padrao_fica_em_tests_fixtures(gerador):
    assert gerador.SAIDA_PADRAO.parent == RAIZ / "tests" / "fixtures"


def test_smoke_aceita_pedido_alternativo(smoke, gerador, tmp_path, monkeypatch, capsys):
    destino = tmp_path / "p.json"
    destino.write_text(json.dumps(gerador.gerar(6_000)), encoding="utf-8")
    vistos = []
    monkeypatch.setattr(smoke, "rodar", lambda motor, pedido: vistos.append((motor, len(pedido.turnos))) or {"motor": motor, "ok": True})
    assert smoke.main(["--pedido", str(destino), "llm1"]) == 0
    assert vistos and vistos[0][0] == "llm1" and vistos[0][1] > 12
    saida = capsys.readouterr().out
    assert "entrada" in saida and "caracteres" in saida


def test_smoke_entrada_usa_a_transcricao_gerada(smoke, gerador, tmp_path, monkeypatch, capsys):
    destino = tmp_path / "t.json"
    gerador.main(["--caracteres", "8000", "--saida", str(destino)])
    capsys.readouterr()
    vistos = []
    monkeypatch.setattr(smoke, "rodar", lambda motor, pedido: vistos.append((motor, pedido)) or {"motor": motor, "ok": True})
    assert smoke.main(["--entrada", str(destino)]) == 0
    assert [m for m, _ in vistos] == ["llm1", "llm2"]
    total = sum(len(t.texto) for t in vistos[0][1].turnos)
    assert total >= 8000
    cabecalho = json.loads(next(x for x in capsys.readouterr().out.splitlines() if x.startswith("{")))
    assert cabecalho == {"entrada": "t.json", "turnos": len(vistos[0][1].turnos), "caracteres": total}


def test_smoke_sem_entrada_usa_o_pedido_do_contrato(smoke, monkeypatch, capsys):
    vistos = []
    monkeypatch.setattr(smoke, "rodar", lambda motor, pedido: vistos.append(motor) or {"motor": motor, "ok": True})
    assert smoke.main(["llm2"]) == 0
    assert vistos == ["llm2"] and '"entrada": "pedido-v3.json"' in capsys.readouterr().out


def test_smoke_recusa_motor_desconhecido(smoke):
    with pytest.raises(SystemExit):
        smoke.main(["llm3"])


def test_smoke_resumo_lista_padroes_confirmados(smoke, monkeypatch):
    from test_p2_llm import ClienteAnthropicFalso, instalar, resposta_anthropic, saida_valida

    instalar(monkeypatch, llm1=ClienteAnthropicFalso(resposta_anthropic(saida_valida())))
    pedido = PedidoAnalise.model_validate(json.loads(smoke.PEDIDO.read_text(encoding="utf-8")))
    resultado = smoke.rodar("llm1", pedido)
    assert resultado["padroes_confirmados"] == sorted({t["padrao"] for t in saida_valida()["temas"]})
