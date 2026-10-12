import os
import subprocess
import sys
from pathlib import Path

import pytest

from app import config

RAIZ_SERVICO = Path(__file__).resolve().parent.parent


@pytest.fixture(autouse=True)
def restaurar_ambiente():
    antes = dict(os.environ)
    yield
    os.environ.clear()
    os.environ.update(antes)


def test_carrega_variaveis_do_arquivo(tmp_path):
    env = tmp_path / ".env"
    env.write_text("VARIAVEL_FICTICIA_A=valor-a\n", encoding="utf-8")
    os.environ.pop("VARIAVEL_FICTICIA_A", None)
    assert config.carregar_dotenv(env) is True
    assert os.environ["VARIAVEL_FICTICIA_A"] == "valor-a"


def test_nao_sobrescreve_variavel_ja_definida(tmp_path):
    env = tmp_path / ".env"
    env.write_text("VARIAVEL_FICTICIA_B=do-arquivo\n", encoding="utf-8")
    os.environ["VARIAVEL_FICTICIA_B"] = "do-ambiente"
    config.carregar_dotenv(env)
    assert os.environ["VARIAVEL_FICTICIA_B"] == "do-ambiente"


def test_arquivo_ausente_nao_da_erro(tmp_path):
    assert config.carregar_dotenv(tmp_path / "nao-existe.env") is False


def test_padrao_respeita_a_variavel_de_ignorar(monkeypatch, tmp_path):
    env = tmp_path / ".env"
    env.write_text("VARIAVEL_FICTICIA_C=x\n", encoding="utf-8")
    monkeypatch.setattr(config, "CAMINHO_ENV", env)
    os.environ.pop("VARIAVEL_FICTICIA_C", None)
    monkeypatch.setenv(config.VARIAVEL_IGNORAR_DOTENV, "1")
    assert config.carregar_dotenv() is False and "VARIAVEL_FICTICIA_C" not in os.environ
    monkeypatch.delenv(config.VARIAVEL_IGNORAR_DOTENV)
    assert config.carregar_dotenv() is True and os.environ["VARIAVEL_FICTICIA_C"] == "x"


def test_app_sobe_sem_env():
    # O ambiente do teste ignora o .env real; mesmo assim o app importa sem arquivo nenhum.
    r = subprocess.run(
        [sys.executable, "-c", "import app.main"], cwd=RAIZ_SERVICO, capture_output=True, text=True, timeout=60
    )
    assert r.returncode == 0, r.stderr
