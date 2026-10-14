"""Checagem PRÉ-DEMO contra o serviço Python NO AR (rede local). Um comando, OK/FALHOU por item.

    cd analise-service
    python scripts/pre_demo.py                 # http://127.0.0.1:8000
    python scripts/pre_demo.py --porta 8001    # outra porta

Itens: (a) GET /health: status e `ok` de llm1, llm2, local e regras · (b) POST /analisar com o pedido sintético
`docs/contrato/pedido-v3.json`: HTTP 200, versaoContrato "v3", pelo menos 1 tema, todo turno citado dentro da reunião,
motor esperado (llm1) e tempo · (c) o mesmo com a transcrição grande de `scripts/gerar_transcricao_sintetica.py`
(399 turnos, gerada em memória) · (d) POST /similares com 3 referências sintéticas, conferindo o formato ·
(e) resumo: PRONTO PARA A DEMO ou NAO PRONTO e a lista do que falhou.

Imprime só status, contagens e tempos; nunca texto do pedido nem da resposta. Saída: 0 pronto, 1 serviço fora do ar,
2 não pronto. Com a LLM real, (b) e (c) custam uma chamada cada (centavos).
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "scripts"))

PEDIDO_CURTO = RAIZ.parent / "docs" / "contrato" / "pedido-v3.json"
MOTORES = ("llm1", "llm2", "local", "regras")
MOTOR_ESPERADO = "llm1"
TIMEOUT_S = 130.0  # o Java espera no máximo 120 s; um pouco mais para ver o tempo real
GRUPOS_COM_TURNO = ("temas", "interesse", "compromissos", "eventosConduta")
# /similares: tudo inventado aqui. A referência sim-1 repete o texto quase igual, para garantir ao menos um similar.
TEXTO_SIMILARES = "O suporte demora para responder os chamados do faturamento e ninguém retorna."
REFERENCIAS_SIMILARES = [
    {"id": "sim-1", "texto": "O suporte demora para responder os chamados do faturamento e ninguém dá retorno."},
    {"id": "sim-2", "texto": "Vamos abrir uma nova filial no mês que vem e queremos levar o sistema."},
    {"id": "sim-3", "texto": "O preço ficou muito caro para o que a gente usa no dia a dia."},
]
TOP_K = 3

# (status_http, corpo_json_ou_None, segundos). Injetável nos testes; a real usa urllib.
Chamar = Callable[[str, str, dict | None], tuple[int, dict | None, float]]


class ServicoForaDoAr(Exception):
    pass


@dataclass
class Item:
    rotulo: str
    nome: str
    ok: bool
    detalhe: str
    segundos: float | None = None


# ------------------------------------------------------------------ regras de OK/FALHOU (puras)

def checar_health(status_http: int, corpo: dict | None, segundos: float | None = None) -> Item:
    if status_http != 200 or not isinstance(corpo, dict):
        return Item("a", "GET /health", False, f"http={status_http}", segundos)
    ok = {m.get("motor"): m.get("ok") for m in corpo.get("motores") or [] if isinstance(m, dict)}
    motores = " ".join(f"{m}={'ok' if ok.get(m) is True else 'X'}" for m in MOTORES)
    tudo_ok = corpo.get("status") == "ok" and all(ok.get(m) is True for m in MOTORES)
    return Item("a", "GET /health", tudo_ok,
                f"status={corpo.get('status')} pipeline={corpo.get('pipelineVersao')} {motores}", segundos)


def pipeline_real(corpo: dict | None) -> bool:
    return isinstance(corpo, dict) and corpo.get("pipelineVersao") == "real"


def turnos_citados(corpo: dict) -> list[int]:
    """Todo turno que a resposta cita: temas (turno e turnoFim), interesse, compromissos e eventos de conduta."""
    turnos = []
    for grupo in GRUPOS_COM_TURNO:
        for item in corpo.get(grupo) or []:
            if isinstance(item, dict):
                turnos += [item.get(campo) for campo in ("turno", "turnoFim") if campo in item]
    return turnos


def contar_turnos_invalidos(corpo: dict, total_turnos: int) -> int:
    return sum(1 for t in turnos_citados(corpo) if not (isinstance(t, int) and 1 <= t <= total_turnos))


def checar_analise(rotulo: str, nome: str, status_http: int, corpo: dict | None, total_turnos: int,
                   segundos: float, motor_esperado: str = MOTOR_ESPERADO) -> Item:
    if status_http != 200 or not isinstance(corpo, dict):
        codigo = corpo.get("codigo") if isinstance(corpo, dict) else None
        return Item(rotulo, nome, False, f"http={status_http}" + (f" codigo={codigo}" if codigo else ""), segundos)
    temas = len(corpo.get("temas") or [])
    invalidos = contar_turnos_invalidos(corpo, total_turnos)
    motor = corpo.get("motor")
    tentativas = " > ".join(f"{t.get('motor')}:{'ok' if t.get('ok') else t.get('erro', 'falhou')}"
                            for t in corpo.get("tentativas") or [] if isinstance(t, dict))
    falhas = []
    if corpo.get("versaoContrato") != "v3":
        falhas.append("versaoContrato")
    if temas < 1:
        falhas.append("sem_temas")
    if invalidos:
        falhas.append("turno_invalido")
    if motor != motor_esperado:
        falhas.append(f"motor!={motor_esperado}")
    detalhe = (f"http=200 versao={corpo.get('versaoContrato')} turnos={total_turnos} temas={temas} "
               f"citacoes={len(turnos_citados(corpo))} turnos_invalidos={invalidos} motor={motor} "
               f"tentativas={tentativas or '-'}")
    if falhas:
        detalhe += " falhou=" + ",".join(falhas)
    return Item(rotulo, nome, not falhas, detalhe, segundos)


def checar_similares(status_http: int, corpo: dict | None, ids_enviados: set[str], top_k: int,
                     segundos: float) -> Item:
    nome = "POST /similares"
    if status_http != 200 or not isinstance(corpo, dict):
        return Item("d", nome, False, f"http={status_http}", segundos)
    similares = corpo.get("similares")
    falhas = []
    if set(corpo) != {"similares", "versaoContrato"}:
        falhas.append("campos")
    if corpo.get("versaoContrato") != "v3":
        falhas.append("versaoContrato")
    if not isinstance(similares, list):
        return Item("d", nome, False, "similares_nao_e_lista falhou=" + ",".join(falhas + ["formato"]), segundos)
    itens_ok = all(isinstance(s, dict) and set(s) == {"id", "score"} and s["id"] in ids_enviados
                   and isinstance(s["score"], (int, float)) and 0 <= s["score"] <= 1 for s in similares)
    if not itens_ok:
        falhas.append("itens")
    elif [s["score"] for s in similares] != sorted((s["score"] for s in similares), reverse=True):
        falhas.append("ordem")
    if len(similares) > top_k:
        falhas.append("topK")
    if not similares:
        falhas.append("nenhum_similar")
    detalhe = f"http=200 versao={corpo.get('versaoContrato')} referencias={len(ids_enviados)} similares={len(similares)}"
    if falhas:
        detalhe += " falhou=" + ",".join(falhas)
    return Item("d", nome, not falhas, detalhe, segundos)


def veredito(itens: list[Item]) -> tuple[bool, list[str]]:
    falhos = [f"{i.rotulo}) {i.nome}" for i in itens if not i.ok]
    return not falhos, falhos


def formatar_relatorio(itens: list[Item]) -> str:
    linhas = []
    for i in itens:
        tempo = f"{i.segundos:.1f}s" if i.segundos is not None else "-"
        linhas.append(f"{'OK' if i.ok else 'FALHOU':<7}{i.rotulo}) {i.nome:<38}{tempo:>8}  {i.detalhe}")
    pronto, falhos = veredito(itens)
    linhas.append("e) " + ("PRONTO PARA A DEMO" if pronto else "NAO PRONTO: " + "; ".join(falhos)))
    return "\n".join(linhas)


# ------------------------------------------------------------------ rede

def criar_chamada(base: str, timeout: float) -> Chamar:
    def chamar(metodo: str, caminho: str, corpo: dict | None = None) -> tuple[int, dict | None, float]:
        dados = json.dumps(corpo).encode("utf-8") if corpo is not None else None
        pedido = urllib.request.Request(base + caminho, data=dados, method=metodo,
                                        headers={"Content-Type": "application/json"})
        inicio = time.perf_counter()
        try:
            with urllib.request.urlopen(pedido, timeout=timeout) as r:
                status, bruto = r.status, r.read()
        except urllib.error.HTTPError as e:  # 4xx/5xx: o corpo estruturado do contrato
            status, bruto = e.code, e.read()
        except (urllib.error.URLError, ConnectionError) as e:  # não conectou (o urllib embrulha a conexão em URLError)
            raise ServicoForaDoAr(type(e).__name__) from None
        except TimeoutError:  # conectou, mas a resposta não chegou no prazo
            return 0, {"codigo": "timeout_cliente"}, round(time.perf_counter() - inicio, 2)
        segundos = round(time.perf_counter() - inicio, 2)
        try:
            return status, json.loads(bruto), segundos
        except ValueError:
            return status, None, segundos

    return chamar


def pedido_grande() -> dict:
    from gerar_transcricao_sintetica import gerar

    return gerar()  # padrão: ~72 mil caracteres, semente 42 -> 399 turnos


def executar(chamar: Chamar, motor_esperado: str = MOTOR_ESPERADO, exigir_real: bool = False) -> list[Item]:
    """Roda (a)-(d). Levanta ServicoForaDoAr se o /health não conecta.

    Com exigir_real, para no (a) se pipelineVersao != "real": sem gastar chamadas de análise.
    """
    status, corpo, segundos = chamar("GET", "/health", None)
    itens = [checar_health(status, corpo, segundos)]
    if exigir_real and not pipeline_real(corpo):
        valor = corpo.get("pipelineVersao") if isinstance(corpo, dict) else None
        itens[0] = Item("a", "GET /health", False, f"http={status} pipeline={valor} falhou=pipeline_nao_real", segundos)
        return itens
    for rotulo, tamanho, pedido in (
        ("b", "curta", json.loads(PEDIDO_CURTO.read_text(encoding="utf-8"))),
        ("c", "grande", pedido_grande()),
    ):
        nome = f"POST /analisar ({tamanho}, {len(pedido['turnos'])} turnos)"
        status, corpo, segundos = chamar("POST", "/analisar", pedido)
        itens.append(checar_analise(rotulo, nome, status, corpo, len(pedido["turnos"]), segundos, motor_esperado))
    pedido = {"texto": TEXTO_SIMILARES, "referencias": REFERENCIAS_SIMILARES, "topK": TOP_K}
    status, corpo, segundos = chamar("POST", "/similares", pedido)
    itens.append(checar_similares(status, corpo, {r["id"] for r in REFERENCIAS_SIMILARES}, TOP_K, segundos))
    return itens


def main(argv: list[str], chamar: Chamar | None = None) -> int:
    p = argparse.ArgumentParser(description="Checagem pré-demo do serviço Python no ar (só status, contagens e tempos).")
    p.add_argument("--host", default="127.0.0.1", help="127.0.0.1 evita a espera do IPv6 de localhost no Windows")
    p.add_argument("--porta", type=int, default=8000)
    p.add_argument("--timeout", type=float, default=TIMEOUT_S, help=f"segundos por chamada (padrão {TIMEOUT_S:g})")
    p.add_argument("--motor-esperado", default=MOTOR_ESPERADO, choices=MOTORES)
    p.add_argument("--exigir-real", action="store_true",
                   help="falha (saída 2) se o /health não disser pipelineVersao=real")
    args = p.parse_args(argv)
    base = f"http://{args.host}:{args.porta}"
    chamar = chamar or criar_chamada(base, args.timeout)
    try:
        itens = executar(chamar, args.motor_esperado, args.exigir_real)
    except ServicoForaDoAr:
        print(f"FALHOU servico fora do ar em {base} (suba com: uvicorn app.main:app --port {args.porta})")
        return 1
    print(formatar_relatorio(itens))
    return 0 if veredito(itens)[0] else 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
