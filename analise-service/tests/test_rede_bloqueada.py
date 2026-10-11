import socket

import pytest

from conftest import RedeBloqueadaEmTeste


def test_conexao_externa_e_bloqueada():
    with pytest.raises(RedeBloqueadaEmTeste):
        socket.create_connection(("203.0.113.1", 443), timeout=1)


def test_socket_connect_externo_e_bloqueado():
    with socket.socket() as s, pytest.raises(RedeBloqueadaEmTeste):
        s.connect(("203.0.113.1", 443))


def test_resolucao_de_nome_externo_e_bloqueada():
    with pytest.raises(RedeBloqueadaEmTeste):
        socket.getaddrinfo("api.anthropic.com", 443)
