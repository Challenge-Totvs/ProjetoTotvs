import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fluxo_integracao  # noqa: E402


def test_hora_da_reuniao_e_hoje_as_nove_no_fuso_local():
    noite = datetime(2026, 10, 13, 22, 30, tzinfo=timezone(timedelta(hours=-3)))
    assert fluxo_integracao.hora_da_reuniao(noite) == "2026-10-13T09:00:00-03:00"


def test_texto_de_usa_marcacao_do_leitor_de_turnos():
    assert fluxo_integracao.texto_de([(1, "oi"), (2, "tudo bem")]) == "[LOCUTOR 1] oi\n[LOCUTOR 2] tudo bem"


def test_turnos_do_pedido_le_pedido_v3(tmp_path):
    arq = tmp_path / "pedido.json"
    arq.write_text(json.dumps({"turnos": [{"n": 1, "locutor": 2, "texto": "fala"}]}), encoding="utf-8")
    assert fluxo_integracao.turnos_do_pedido(str(arq)) == [(2, "fala")]


def test_resumo_reuniao_nao_carrega_texto():
    detalhe = {
        "status": "analisada", "temTranscricao": True, "turnos": 7,
        "analise": {"motor": "llm2", "score": 65, "resumo": "TEXTO SECRETO",
                    "tentativas": [{"motor": "llm1", "ok": False}, {"motor": "llm2", "ok": True}]},
        "temas": [{"tema": {"titulo": "TEXTO SECRETO"}, "citacao": {"texto": "TEXTO SECRETO"}}, {"tema": {}}],
        "compromissos": [{}],
    }
    resumo = fluxo_integracao.resumo_reuniao(detalhe)
    assert "TEXTO SECRETO" not in json.dumps(resumo)
    assert resumo["motor"] == "llm2" and resumo["temas"] == 2 and resumo["temasComCitacao"] == 1
    assert resumo["tentativas"] == [("llm1", False), ("llm2", True)]
