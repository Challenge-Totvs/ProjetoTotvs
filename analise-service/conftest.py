"""Configuração global dos testes.

Nenhum teste chama rede: conexões só são aceitas para loopback (o asyncio no Windows
usa um socketpair em 127.0.0.1 internamente, e o TestClient depende disso).
"""
import ipaddress
import os
import socket

import pytest

# Antes de qualquer import de app.main: nenhum teste lê o .env real nem usa chaves (regra 4).
os.environ["INSIGHTCALL_IGNORAR_DOTENV"] = "1"

_HOSTS_LOCAIS = {"localhost", ""}


class RedeBloqueadaEmTeste(RuntimeError):
    pass


def _eh_loopback(host) -> bool:
    if isinstance(host, bytes):
        host = host.decode()
    if not isinstance(host, str):
        return False
    if host in _HOSTS_LOCAIS:
        return True
    try:
        return ipaddress.ip_address(host.split("%")[0]).is_loopback
    except ValueError:
        return False


def _host_de(endereco):
    if isinstance(endereco, tuple) and endereco:
        return endereco[0]
    return None


@pytest.fixture(autouse=True)
def bloquear_rede(monkeypatch):
    connect_original = socket.socket.connect
    connect_ex_original = socket.socket.connect_ex
    create_connection_original = socket.create_connection
    getaddrinfo_original = socket.getaddrinfo

    def connect(self, endereco):
        if not _eh_loopback(_host_de(endereco)):
            raise RedeBloqueadaEmTeste(f"teste tentou conectar em {endereco!r}")
        return connect_original(self, endereco)

    def connect_ex(self, endereco):
        if not _eh_loopback(_host_de(endereco)):
            raise RedeBloqueadaEmTeste(f"teste tentou conectar em {endereco!r}")
        return connect_ex_original(self, endereco)

    def create_connection(endereco, *args, **kwargs):
        if not _eh_loopback(_host_de(endereco)):
            raise RedeBloqueadaEmTeste(f"teste tentou conectar em {endereco!r}")
        return create_connection_original(endereco, *args, **kwargs)

    def getaddrinfo(host, *args, **kwargs):
        if not _eh_loopback(host) and host is not None:
            raise RedeBloqueadaEmTeste(f"teste tentou resolver {host!r}")
        return getaddrinfo_original(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)
    monkeypatch.setattr(socket, "create_connection", create_connection)
    monkeypatch.setattr(socket, "getaddrinfo", getaddrinfo)


@pytest.fixture(autouse=True)
def sem_chaves_no_ambiente(monkeypatch):
    """Nenhum teste usa chave: o que estiver no ambiente do desenvolvedor é removido (regra 4)."""
    for variavel in ("LLM_PRINCIPAL_API_KEY", "LLM_PRINCIPAL_MODEL", "LLM_SECUNDARIA_API_KEY", "LLM_SECUNDARIA_MODEL"):
        monkeypatch.delenv(variavel, raising=False)
    monkeypatch.delenv("FORCAR_FALHA", raising=False)


@pytest.fixture(autouse=True)
def estado_de_saude_limpo():
    from app import saude

    saude.limpar_estado()
    yield
    saude.limpar_estado()


@pytest.fixture
def pipeline_versao(monkeypatch):
    """Define PIPELINE_VERSAO para o teste e limpa o cache da configuração."""
    from app import config

    def definir(valor: str) -> None:
        monkeypatch.setenv("PIPELINE_VERSAO", valor)
        config.obter_config.cache_clear()

    yield definir
    config.obter_config.cache_clear()
