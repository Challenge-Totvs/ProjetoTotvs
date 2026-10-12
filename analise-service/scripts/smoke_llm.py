"""Smoke MANUAL das LLMs reais (AC10). Rodado pelo João Paulo, com chaves de DESENVOLVIMENTO.

    cd analise-service
    python scripts/smoke_llm.py            # llm1 e llm2
    python scripts/smoke_llm.py llm1       # só uma

Envia docs/contrato/pedido-v3.json (sintético) a cada LLM, lendo as chaves do ambiente (e de
analise-service/.env, se existir), valida a resposta contra AnaliseResponse e imprime SÓ motor,
tempo, contagens e o resultado da conferência de citações. Em falha, imprime o código do contrato, o código
HTTP e o tipo do erro do provedor (`authentication_error`, `not_found_error`, `permission_error`,
`rate_limit_error`, `invalid_request_error`...). Nunca imprime texto da transcrição, texto devolvido pela
LLM, mensagens de erro do provedor, corpo da requisição nem chaves.

ATENÇÃO: o prompt NÃO foi validado com LLM real até este script rodar e o resultado ser registrado
em docs/evidencias/smoke-12-10.md.
"""
import json
import sys
import time
from collections import Counter
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from app import config  # noqa: E402
from app.cadeia import Prazo  # noqa: E402
from app.engines import llm_engine  # noqa: E402
from app.erros import ErroMotor  # noqa: E402
from app.schemas import AnaliseResponse, PedidoAnalise  # noqa: E402

PEDIDO = RAIZ.parent / "docs" / "contrato" / "pedido-v3.json"
GRUPOS = ("temas", "interesse", "compromissos", "eventosConduta")


def resumir(devolvido_pela_llm, resposta: dict) -> dict:
    """Só números: o que a LLM devolveu, o que a conferência confirmou e o que descartou (por motivo e origem)."""
    descartados = resposta["descartados"]
    return {
        "devolvido_pela_llm": {g: len(getattr(devolvido_pela_llm, g)) for g in GRUPOS},
        "confirmado_pela_conferencia": {g: len(resposta[g]) for g in GRUPOS},
        "descartados_por_motivo": dict(Counter(d["motivo"] for d in descartados)),
        "descartados_por_origem": dict(Counter(d.get("origem", "?") for d in descartados)),
        "avisos": resposta["avisos"],
        "score": resposta["score"],
        "sentimento": resposta["sentimento"],
    }


def rodar(motor: str, pedido: PedidoAnalise) -> dict:
    capturado = {}
    original = llm_engine.processar_saida

    def espiar(ped, saida):
        capturado["saida"] = saida
        return original(ped, saida)

    llm_engine.processar_saida = espiar
    inicio = time.perf_counter()
    try:
        resposta = llm_engine.criar_motor(motor, Prazo())(pedido)
    except ErroMotor as e:  # código do contrato + código HTTP e tipo do erro do provedor, se houver
        resultado = {"motor": motor, "ok": False, "erro": e.codigo, "tempo_s": round(time.perf_counter() - inicio, 1)}
        if e.status_http is not None:
            resultado["http"] = e.status_http
        if e.tipo_provedor is not None:
            resultado["tipo_erro_provedor"] = e.tipo_provedor
        return resultado
    except Exception as e:  # ValidationError e afins: só o tipo, nunca a mensagem
        return {"motor": motor, "ok": False, "erro": type(e).__name__, "tempo_s": round(time.perf_counter() - inicio, 1)}
    finally:
        llm_engine.processar_saida = original
    tempo = round(time.perf_counter() - inicio, 1)
    AnaliseResponse(**resposta, motor=motor, tentativas=[{"motor": motor, "ok": True}], versaoContrato="v3")
    return {"motor": motor, "ok": True, "tempo_s": tempo, "valida_em_AnaliseResponse": True,
            **resumir(capturado["saida"], resposta)}


def main(argv: list[str]) -> int:
    config.carregar_dotenv()
    args = list(argv)
    caminho = PEDIDO
    if "--pedido" in args:  # pedido alternativo, ex.: o sintético de tamanho P90 (scripts/gerar_transcricao_sintetica.py)
        i = args.index("--pedido")
        caminho = Path(args[i + 1])
        del args[i : i + 2]
    motores = [m for m in args if m in ("llm1", "llm2")] or ["llm1", "llm2"]
    pedido = PedidoAnalise.model_validate(json.loads(caminho.read_text(encoding="utf-8")))
    print("SMOKE MANUAL — prompt NÃO validado com LLM real até este resultado ser registrado.")
    print(json.dumps({"entrada": caminho.name, "turnos": len(pedido.turnos),
                      "caracteres": sum(len(t.texto) for t in pedido.turnos)}, ensure_ascii=False))
    falhou = False
    for motor in motores:
        credenciais = config.credenciais_llm(motor)  # só o NOME do modelo é impresso, nunca a chave
        linha = f"{motor}: modelo={credenciais[1] if credenciais else 'nao_configurado'}"
        if motor == "llm1":  # só se o workspace está definido, nunca o valor
            linha += f" workspace={'definido' if config.workspace_llm1() else 'ausente'}"
        print(linha)
        resultado = rodar(motor, pedido)
        falhou |= not resultado["ok"]
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
