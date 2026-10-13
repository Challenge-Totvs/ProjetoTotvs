"""Ensaio de falha da cadeia (demo da banca): scripts/ensaio_falha.py com clients de LLM SIMULADOS (sem rede, sem chave)."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
FIXTURE = RAIZ / "tests" / "fixtures" / "transcricao-sintetica-p90.json"


def _carregar():
    spec = importlib.util.spec_from_file_location("ensaio_falha", RAIZ / "scripts" / "ensaio_falha.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def resultados():
    ensaio = _carregar()
    return ensaio, ensaio.executar_ensaio(FIXTURE)


def test_cinco_cenarios_na_ordem(resultados):
    _, r = resultados
    assert [x["cenario"] for x in r] == [1, 2, 3, 4, 5]
    assert [x["forcar_falha"] for x in r] == ["", "llm1", "llm1,llm2", "llm1,llm2,local", "llm1,llm2,local,regras"]


def test_motor_que_respondeu_e_status_http(resultados):
    _, r = resultados
    assert [x["motor"] for x in r] == ["llm1", "llm2", "local", "regras", None]
    assert [x["http"] for x in r] == [200, 200, 200, 200, 503]


def test_tentativas_batem_com_a_cadeia(resultados):
    _, r = resultados
    assert [x["tentativas"] for x in r] == [
        [("llm1", "ok")],
        [("llm1", "erro_provedor"), ("llm2", "ok")],
        [("llm1", "erro_provedor"), ("llm2", "erro_provedor"), ("local", "ok")],
        [("llm1", "erro_provedor"), ("llm2", "erro_provedor"), ("local", "erro_provedor"), ("regras", "ok")],
        [("llm1", "erro_provedor"), ("llm2", "erro_provedor"), ("local", "erro_provedor"),
         ("regras", "erro_provedor")],
    ]


def test_avisos_de_contingencia(resultados):
    _, r = resultados
    assert [x["avisos"] for x in r] == [[], [], ["contingencia_modelo_local"], ["contingencia_regras"], []]


def test_health_depois_de_cada_cenario(resultados):
    _, r = resultados
    assert [x["health_status"] for x in r] == ["ok", "ok", "degradado", "degradado", "indisponivel"]
    todos = {"llm1": True, "llm2": True, "local": True, "regras": True}
    assert [x["health_motores"] for x in r] == [
        todos,
        {**todos, "llm1": False},
        {**todos, "llm1": False, "llm2": False},
        {**todos, "llm1": False, "llm2": False, "local": False},
        {"llm1": False, "llm2": False, "local": False, "regras": False},
    ]


def test_tempo_e_numero_nao_negativo(resultados):
    _, r = resultados
    assert all(isinstance(x["segundos"], float) and x["segundos"] >= 0 for x in r)


def test_tabela_so_com_nomes_e_contagens(resultados):
    ensaio, r = resultados
    tabela = ensaio.formatar_tabela(r)
    for esperado in ("llm1 falha", "todos falham", "503", "degradado", "indisponivel", "contingencia_regras",
                     "llm1:erro_provedor > llm2:ok"):
        assert esperado in tabela
    turnos = json.loads(FIXTURE.read_text(encoding="utf-8"))["turnos"]
    for turno in turnos[:40]:
        assert turno["texto"][:30] not in tabela
    assert "chave" not in tabela.lower()


def test_ambiente_restaurado_depois_do_ensaio(resultados):
    ensaio, _ = resultados
    assert os.environ.get("FORCAR_FALHA") is None
    assert "ensaio" not in os.environ.get("LLM_PRINCIPAL_API_KEY", "")
    from app import saude
    from app.engines import llm_engine

    assert saude._ultimas == {}
    assert llm_engine.obter_cliente.__module__ == "app.engines.llm_engine"


def test_script_roda_como_comando_e_nao_precisa_de_chave():
    ambiente = {k: v for k, v in os.environ.items() if not k.startswith(("LLM_", "FORCAR"))}
    r = subprocess.run([sys.executable, "scripts/ensaio_falha.py"], cwd=RAIZ, capture_output=True, env=ambiente,
                       timeout=120)
    saida = r.stdout.decode("utf-8", "replace")
    assert r.returncode == 0 and "todos falham" in saida and "analise_indisponivel" in saida


@pytest.fixture(scope="module")
def extras():
    return _carregar().executar_extras(FIXTURE)


def test_extra_citacao_inventada_vai_para_descartados(extras):
    r = extras[0]
    assert (r["cenario"], r["motor"], r["http"], r["forcar_falha"]) == (6, "llm1", 200, "")
    assert r["temas"] == 1 and r["descartados"] == {"evidencia_nao_localizada": 1} and r["avisos"] == ["saida_parcial"]


def test_extra_timeout_da_llm1_passa_para_a_llm2(extras):
    r = extras[1]
    assert (r["cenario"], r["motor"], r["http"]) == (7, "llm2", 200)
    assert r["tentativas"] == [("llm1", "timeout"), ("llm2", "ok")] and r["health_motores"]["llm1"] is False


def test_extras_restauram_o_ambiente(extras):
    from app.engines import llm_engine

    assert llm_engine.obter_cliente.__module__ == "app.engines.llm_engine"
    assert os.environ.get("FORCAR_FALHA") is None


def test_tabela_mostra_os_extras(extras):
    tabela = _carregar().formatar_tabela(extras)
    assert "evidencia_nao_localizada:1" in tabela and "llm1:timeout > llm2:ok" in tabela
    assert "inventada pela LLM" not in tabela  # o texto da citação nunca aparece
