"""scripts/gerar_pedido_sintetico.py e a opção --pedido do smoke. Tudo sintético, sem rede."""
import importlib.util
import json
from pathlib import Path

import pytest

from app.schemas import PedidoAnalise

RAIZ = Path(__file__).resolve().parent.parent


def _carregar(nome):
    spec = importlib.util.spec_from_file_location(nome, RAIZ / "scripts" / f"{nome}.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture
def gerador():
    return _carregar("gerar_pedido_sintetico")


@pytest.fixture
def smoke():
    return _carregar("smoke_llm")


def test_gera_pedido_valido_no_tamanho_pedido(gerador):
    dados = gerador.gerar(caracteres=72_000)
    pedido = PedidoAnalise.model_validate(dados)
    total = sum(len(t.texto) for t in pedido.turnos)
    assert 72_000 <= total <= 72_000 + 600
    assert [t.n for t in pedido.turnos] == list(range(1, len(pedido.turnos) + 1))
    assert len(pedido.turnos) <= 3000 and max(len(t.texto) for t in pedido.turnos) <= 5000


def test_e_deterministico_e_varia_com_a_semente(gerador):
    assert gerador.gerar(5_000, semente=1) == gerador.gerar(5_000, semente=1)
    assert gerador.gerar(5_000, semente=1) != gerador.gerar(5_000, semente=2)


def test_tem_sinais_para_os_motores_acharem_temas(gerador):
    from app.engines import regras_engine

    pedido = PedidoAnalise.model_validate(gerador.gerar(20_000))
    padroes = {t["padrao"] for t in regras_engine.analisar(pedido)["temas"]}
    assert len(padroes) >= 5


def test_main_grava_arquivo_e_imprime_so_contagens(gerador, tmp_path, capsys):
    destino = tmp_path / "pedido.json"
    assert gerador.main(["--caracteres", "3000", "--saida", str(destino)]) == 0
    saida = capsys.readouterr().out
    assert json.loads(destino.read_text(encoding="utf-8"))["turnos"]
    primeiro = json.loads(destino.read_text(encoding="utf-8"))["turnos"][0]["texto"]
    assert primeiro not in saida and "turnos" in saida and "caracteres" in saida


def test_smoke_aceita_pedido_alternativo(smoke, gerador, tmp_path, monkeypatch, capsys):
    destino = tmp_path / "p.json"
    destino.write_text(json.dumps(gerador.gerar(6_000)), encoding="utf-8")
    vistos = []
    monkeypatch.setattr(smoke, "rodar", lambda motor, pedido: vistos.append((motor, len(pedido.turnos))) or {"motor": motor, "ok": True})
    assert smoke.main(["--pedido", str(destino), "llm1"]) == 0
    assert vistos and vistos[0][0] == "llm1" and vistos[0][1] > 12
    saida = capsys.readouterr().out
    assert "entrada" in saida and "caracteres" in saida
