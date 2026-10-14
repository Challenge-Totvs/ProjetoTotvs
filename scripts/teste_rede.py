"""Teste de rede antes da demo: Oracle (TCP) e as duas APIs de LLM (HTTPS).

Lê DB_URL e DB_PORT de backend/.env (linhas ou pares separados por ';');
se o arquivo não existir, usa as variáveis de ambiente. Imprime só
OK/FALHOU, a latência e o tipo do erro: nunca host, porta ou chave.

Uso: python scripts/teste_rede.py [--timeout 5]
"""
import argparse
import os
import re
import socket
import ssl
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
ENV_BACKEND = RAIZ / "backend" / ".env"
APIS = ("api.anthropic.com", "api.openai.com")


def ler_env(caminho: Path) -> dict:
    """Aceita KEY=valor por linha ou KEY=valor;KEY=valor (formato do .env.example)."""
    if not caminho.exists():
        return {}
    pares = {}
    for parte in re.split(r"[;\r\n]+", caminho.read_text(encoding="utf-8")):
        parte = parte.strip()
        if not parte or parte.startswith("#") or "=" not in parte:
            continue
        chave, valor = parte.split("=", 1)
        pares[chave.strip()] = valor.strip().strip('"').strip("'")
    return pares


def host_do_banco(db_url: str) -> str:
    """DB_URL costuma ser só o host; tolera 'jdbc:oracle:thin:@host:porta:sid'."""
    if "@" in db_url:
        db_url = db_url.split("@", 1)[1]
    return db_url.split(":", 1)[0].strip("/")


def testar_tcp(host: str, porta: int, timeout: float) -> tuple:
    inicio = time.perf_counter()
    try:
        with socket.create_connection((host, porta), timeout=timeout):
            pass
        return True, time.perf_counter() - inicio, ""
    except OSError as erro:
        return False, time.perf_counter() - inicio, type(erro).__name__


def testar_https(host: str, timeout: float) -> tuple:
    """Qualquer resposta HTTP (até 401/404) prova DNS, TCP e TLS de pé."""
    inicio = time.perf_counter()
    pedido = urllib.request.Request(f"https://{host}/", method="GET")
    try:
        urllib.request.urlopen(pedido, timeout=timeout, context=ssl.create_default_context())
        return True, time.perf_counter() - inicio, ""
    except urllib.error.HTTPError:
        return True, time.perf_counter() - inicio, ""
    except (urllib.error.URLError, OSError) as erro:
        motivo = getattr(erro, "reason", erro)
        return False, time.perf_counter() - inicio, type(motivo).__name__


def linha(nome: str, ok: bool, segundos: float, erro: str) -> str:
    status = "OK" if ok else "FALHOU"
    extra = f" ({erro})" if erro else ""
    return f"{nome:<26} {status:<7} {segundos * 1000:8.0f} ms{extra}"


def main(argv=None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timeout", type=float, default=5.0)
    args = parser.parse_args(argv)

    env = {**{k: os.environ[k] for k in ("DB_URL", "DB_PORT") if k in os.environ}, **ler_env(ENV_BACKEND)}
    resultados = []

    if env.get("DB_URL") and env.get("DB_PORT", "").isdigit():
        ok, seg, erro = testar_tcp(host_do_banco(env["DB_URL"]), int(env["DB_PORT"]), args.timeout)
        resultados.append(("oracle (tcp)", ok, seg, erro))
    else:
        resultados.append(("oracle (tcp)", False, 0.0, "DB_URL/DB_PORT ausentes"))

    for host in APIS:
        resultados.append((f"{host} (https)", *testar_https(host, args.timeout)))

    for r in resultados:
        print(linha(*r))
    return 0 if all(r[1] for r in resultados) else 1


if __name__ == "__main__":
    sys.exit(main())
