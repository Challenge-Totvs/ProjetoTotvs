"""Ensaio de falha da cadeia para a demo da banca. SEM rede e SEM chave: os clients das LLMs são simulados.

    cd analise-service
    python scripts/ensaio_falha.py
    python scripts/ensaio_falha.py --entrada tests/fixtures/transcricao-sintetica-p90.json

Roda o app REAL (router -> orquestrador -> cadeia -> /health) em memória, com a transcrição sintética de
`tests/fixtures`, em 5 cenários feitos com a mesma alavanca da demo ao vivo, `FORCAR_FALHA`:
(1) nada falha · (2) llm1 falha · (3) llm1+llm2 falham · (4) llm1+llm2+local falham (só regras) · (5) todos falham (503).
Extras, que o FORCAR_FALHA não produz: (6) a llm1 devolve uma citação inventada (vai para `descartados`, aviso
`saida_parcial`) · (7) a llm1 estoura o tempo (`timeout`; a llm2 assume). Nos extras o tempo é o do simulado, não o real.
Entre os cenários o estado do /health é zerado (equivale a reiniciar o serviço, que é o que se faz ao vivo).
Imprime uma tabela só com nomes e contagens: nunca texto de transcrição, resposta de LLM ou chave.
"""
import argparse
import json
import logging
import os
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from types import SimpleNamespace

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

ENTRADA_PADRAO = RAIZ / "tests" / "fixtures" / "transcricao-sintetica-p90.json"
CENARIOS = (
    (1, "nada falha", ""),
    (2, "llm1 falha", "llm1"),
    (3, "llm1+llm2 falham", "llm1,llm2"),
    (4, "llm1+llm2+local falham (so regras)", "llm1,llm2,local"),
    (5, "todos falham", "llm1,llm2,local,regras"),
)
# Extras que o FORCAR_FALHA não produz (ele só gera erro_provedor): o cliente simulado faz a falha acontecer.
CENARIOS_EXTRAS = (
    (6, "citacao inventada pela llm1", "citacao_inventada"),
    (7, "timeout da llm1", "timeout"),
)
# Valores FICTÍCIOS: o ensaio nunca usa chave real nem lê o .env.
AMBIENTE_SIMULADO = {
    "INSIGHTCALL_IGNORAR_DOTENV": "1",
    "PIPELINE_VERSAO": "real",
    "LLM_PRINCIPAL_API_KEY": "chave-simulada-ensaio", "LLM_PRINCIPAL_MODEL": "modelo-simulado-1",
    "LLM_SECUNDARIA_API_KEY": "chave-simulada-ensaio", "LLM_SECUNDARIA_MODEL": "modelo-simulado-2",
}
VARIAVEIS_LIMPAS = ("FORCAR_FALHA", "LLM_PRINCIPAL_WORKSPACE_ID")
# Saída mínima válida de LLM (formato SaidaLLM): o ensaio fala de motores e tentativas, não de conteúdo.
SAIDA_SIMULADA = {
    "score": 50, "sentimento": "neutro", "papeis": [], "resumo": "Resumo sintetico do ensaio.", "interesse": [],
    "proximosPassos": [], "temas": [], "compromissos": [], "sentimentoSerie": [], "eventosConduta": [],
}


class APITimeoutError(Exception):
    """Mesmo NOME da exceção de timeout dos SDKs: o llm_engine traduz pelo nome da classe para o código `timeout`."""


def _cliente_anthropic_simulado(saida: dict | None = None, erro: Exception | None = None):
    def create(**_):
        if erro is not None:
            raise erro
        bloco = SimpleNamespace(type="tool_use", input=dict(saida or SAIDA_SIMULADA))
        return SimpleNamespace(stop_reason="tool_use", content=[bloco])

    return SimpleNamespace(messages=SimpleNamespace(create=create))


def _saida_com_citacao_inventada(pedido: dict) -> dict:
    """Um tema com recorte literal de um turno do pedido (fica) e um com frase que não está na reunião (descartado)."""
    turno = next(t for t in pedido["turnos"] if len(t["texto"]) >= 30)
    real = {"padrao": "suporte_insatisfacao", "titulo": "Tema com citação real", "tipos": ["risco"],
            "turno": turno["n"], "tratado": None, "texto": turno["texto"][:120], "confianca": 0.9}
    inventada = {**real, "padrao": "preco_objecao", "titulo": "Tema com citação inventada",
                 "texto": "Esta frase foi inventada pela LLM e não aparece na reunião."}
    return {**SAIDA_SIMULADA, "temas": [real, inventada]}


def _cliente_openai_simulado():
    from app.schemas import SaidaLLM

    def parse(**_):
        return SimpleNamespace(status="completed", output_parsed=SaidaLLM.model_validate(SAIDA_SIMULADA), output=[])

    return SimpleNamespace(responses=SimpleNamespace(parse=parse))


@contextmanager
def ambiente_simulado():
    """Chaves fictícias, `.env` ignorado e clients de LLM simulados; tudo é restaurado ao sair."""
    from app import config, saude
    from app.engines import llm_engine

    antes = {k: os.environ.get(k) for k in (*AMBIENTE_SIMULADO, *VARIAVEIS_LIMPAS)}
    obter_original = llm_engine.obter_cliente
    simulados = {"llm1": _cliente_anthropic_simulado(), "llm2": _cliente_openai_simulado()}
    try:
        for k in VARIAVEIS_LIMPAS:
            os.environ.pop(k, None)
        os.environ.update(AMBIENTE_SIMULADO)
        config.obter_config.cache_clear()
        llm_engine.obter_cliente = lambda motor: simulados[motor]
        saude.limpar_estado()
        yield
    finally:
        llm_engine.obter_cliente = obter_original
        for k, v in antes.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        config.obter_config.cache_clear()
        saude.limpar_estado()


def _tentativas(corpo: dict) -> list[tuple[str, str]]:
    return [(t["motor"], "ok" if t["ok"] else t.get("erro", "falhou")) for t in corpo.get("tentativas", [])]


def _rodar_cenario(cliente, pedido: dict, numero: int, nome: str, forcar: str) -> dict:
    from app import saude

    saude.limpar_estado()  # reiniciar o serviço zera o estado em memória do /health
    os.environ["FORCAR_FALHA"] = forcar
    inicio = time.perf_counter()
    resposta = cliente.post("/analisar", json=pedido)
    segundos = round(time.perf_counter() - inicio, 2)
    corpo = resposta.json()
    health = cliente.get("/health").json()
    descartados: dict[str, int] = {}
    for d in corpo.get("descartados") or []:
        descartados[d["motivo"]] = descartados.get(d["motivo"], 0) + 1
    return {
        "cenario": numero, "nome": nome, "forcar_falha": forcar,
        "motor": corpo.get("motor"), "tentativas": _tentativas(corpo), "http": resposta.status_code,
        "codigo": corpo.get("codigo"), "avisos": list(corpo.get("avisos") or []), "segundos": float(segundos),
        "temas": len(corpo.get("temas") or []), "descartados": descartados,
        "health_status": health["status"],
        "health_motores": {m["motor"]: m["ok"] for m in health["motores"]},
    }


def executar_ensaio(entrada: Path = ENTRADA_PADRAO) -> list[dict]:
    """Roda os 5 cenários. Devolve, por cenário, só nomes e contagens (nada de texto de transcrição)."""
    pedido = json.loads(Path(entrada).read_text(encoding="utf-8"))
    with ambiente_simulado():
        from fastapi.testclient import TestClient

        from app.main import app

        cliente = TestClient(app)
        resultados = [_rodar_cenario(cliente, pedido, numero, nome, forcar) for numero, nome, forcar in CENARIOS]
        os.environ.pop("FORCAR_FALHA", None)
    return resultados


def executar_extras(entrada: Path = ENTRADA_PADRAO) -> list[dict]:
    """Cenários 6 e 7 (citação inventada, timeout): sem FORCAR_FALHA; o cliente simulado da llm1 provoca a falha."""
    pedido = json.loads(Path(entrada).read_text(encoding="utf-8"))
    clientes_llm1 = {"citacao_inventada": _cliente_anthropic_simulado(saida=_saida_com_citacao_inventada(pedido)),
                     "timeout": _cliente_anthropic_simulado(erro=APITimeoutError("tempo esgotado (simulado)"))}
    with ambiente_simulado():
        from fastapi.testclient import TestClient

        from app.engines import llm_engine
        from app.main import app

        cliente = TestClient(app)
        resultados = []
        for numero, nome, tipo in CENARIOS_EXTRAS:
            simulados = {"llm1": clientes_llm1[tipo], "llm2": _cliente_openai_simulado()}
            llm_engine.obter_cliente = lambda motor, s=simulados: s[motor]  # o ambiente_simulado restaura ao sair
            resultados.append(_rodar_cenario(cliente, pedido, numero, nome, ""))
        os.environ.pop("FORCAR_FALHA", None)
    return resultados


def formatar_tabela(resultados: list[dict]) -> str:
    cabecalho = ["#", "cenario", "FORCAR_FALHA", "motor", "tentativas (motor:resultado)", "HTTP", "avisos", "descartes",
                 "tempo(s)", "/health depois"]
    linhas = [cabecalho]
    for r in resultados:
        saude = f"{r['health_status']} [" + " ".join(f"{m}={'ok' if ok else 'X'}" for m, ok in r["health_motores"].items()) + "]"
        http = str(r["http"]) + (f" {r['codigo']}" if r["codigo"] else "")
        linhas.append([
            str(r["cenario"]), r["nome"], r["forcar_falha"] or "(vazio)", r["motor"] or "-",
            " > ".join(f"{m}:{res}" for m, res in r["tentativas"]), http, ",".join(r["avisos"]) or "-",
            ",".join(f"{m}:{n}" for m, n in r.get("descartados", {}).items()) or "-", f"{r['segundos']:.2f}", saude,
        ])
    larguras = [max(len(linha[i]) for linha in linhas) for i in range(len(cabecalho))]
    formatadas = ["  ".join(c.ljust(w) for c, w in zip(linha, larguras)).rstrip() for linha in linhas]
    return "\n".join([formatadas[0], "  ".join("-" * w for w in larguras), *formatadas[1:]])


def main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(description="Ensaio de falha da cadeia (clients simulados, sem rede nem chave).")
    p.add_argument("--entrada", type=Path, default=ENTRADA_PADRAO, help="transcrição sintética (formato do pedido)")
    args = p.parse_args(argv)
    logging.disable(logging.CRITICAL)  # os avisos da cadeia vão para o log; aqui só a tabela
    print(formatar_tabela(executar_ensaio(args.entrada) + executar_extras(args.entrada)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
