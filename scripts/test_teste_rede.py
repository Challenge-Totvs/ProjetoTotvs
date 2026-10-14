import socket
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import teste_rede  # noqa: E402


def test_ler_env_aceita_ponto_e_virgula_e_linhas(tmp_path):
    arq = tmp_path / ".env"
    arq.write_text("DB_URL=host.exemplo;DB_PORT=1521\n# comentario\nDB_SID=\"orcl\"\n", encoding="utf-8")
    assert teste_rede.ler_env(arq) == {"DB_URL": "host.exemplo", "DB_PORT": "1521", "DB_SID": "orcl"}


def test_ler_env_sem_arquivo_devolve_vazio(tmp_path):
    assert teste_rede.ler_env(tmp_path / "nao-existe") == {}


def test_host_do_banco_tolera_url_jdbc():
    assert teste_rede.host_do_banco("host.exemplo") == "host.exemplo"
    assert teste_rede.host_do_banco("jdbc:oracle:thin:@host.exemplo:1521:orcl") == "host.exemplo"


def test_tcp_ok_em_porta_local_aberta():
    servidor = socket.socket()
    servidor.bind(("127.0.0.1", 0))
    servidor.listen(1)
    try:
        ok, segundos, erro = teste_rede.testar_tcp("127.0.0.1", servidor.getsockname()[1], 2)
    finally:
        servidor.close()
    assert ok and erro == "" and segundos >= 0


def test_linha_nao_mostra_host():
    texto = teste_rede.linha("oracle (tcp)", False, 0.25, "TimeoutError")
    assert "FALHOU" in texto and "250 ms" in texto and "TimeoutError" in texto
