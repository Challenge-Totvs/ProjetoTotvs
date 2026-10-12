"""P9 — validar_professora.py: LLM da destilação × rótulos do João no ouro. Tudo SINTÉTICO, cliente simulado."""
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

from treino import comum, conciliar_ouro, validar_professora as vp

RAIZ = Path(__file__).resolve().parent.parent
MARCA = {"risco": "alfaRISCO", "oportunidade": "betaOPORT", "interesse": "gamaINTER"}


def linha_ouro(i: int, risco=0, oportunidade=0, interesse=0, duvida=0, texto=None) -> dict:
    marcas = " ".join(MARCA[g] for g, v in (("risco", risco), ("oportunidade", oportunidade), ("interesse", interesse))
                      if v)
    return {"id": f"G{i:03d}", "texto": texto or f"Frase sintética {i} {marcas}".strip(), "padrao_1": "",
            "padrao_2": "", "risco": str(risco), "oportunidade": str(oportunidade),
            "interesse": "" if interesse is None else str(interesse), "duvida": str(duvida), "metade": "A"}


def cache_de(ouro: list[dict], erros=(), ausentes=()) -> dict[str, dict]:
    """Cache da professora: acerta tudo, exceto os índices em `erros` (inverte o risco) e `ausentes` (sem resposta)."""
    cache = {}
    for i, r in enumerate(ouro):
        if i in ausentes:
            cache[r["id"]] = {"id": r["id"], "ok": False}
            continue
        reg = {g: r[g] == "1" for g in vp.GRUPOS}
        if i in erros:
            reg["risco"] = not reg["risco"]
        cache[r["id"]] = {"id": r["id"], "ok": True, **reg}
    return cache


def ouro_base() -> list[dict]:
    # 10 de risco, 10 sem; 10 de oportunidade (os mesmos sem risco), 8 de interesse
    ouro = [linha_ouro(i, risco=1) for i in range(10)]
    ouro += [linha_ouro(10 + i, oportunidade=1, interesse=int(i < 8)) for i in range(10)]
    ouro += [linha_ouro(20 + i) for i in range(10)]
    return ouro


# ------------------------------------------------------------------ etapa 1: núcleo

def test_professora_perfeita_vira_usar():
    ouro = ouro_base()
    r = vp.comparar(ouro, cache_de(ouro))
    assert r["risco"]["revocacao"] == 1.0 and r["risco"]["alarme_falso"] == 0.0 and r["risco"]["kappa"] == 1.0
    assert r["risco"]["precisao"] == 1.0 and r["risco"]["f1"] == 1.0
    assert all(vp.veredito(r[g]) == vp.USAR for g in vp.GRUPOS)


def test_metricas_com_erros_conhecidos():
    ouro = ouro_base()
    # Erra o risco em 2 positivos (índices 0,1 -> FN) e em 1 negativo (índice 20 -> FP)
    r = vp.comparar(ouro, cache_de(ouro, erros={0, 1, 20}))["risco"]
    assert (r["n"], r["positivos"], r["tp"], r["fn"], r["fp"], r["tn"]) == (30, 10, 8, 2, 1, 19)
    assert r["revocacao"] == 0.8 and r["alarme_falso"] == pytest.approx(1 / 20, abs=1e-4)
    assert r["precisao"] == pytest.approx(8 / 9, abs=1e-4)
    assert 0 < r["kappa"] < 1


def test_veredito_exige_kappa_e_revocacao_em_cada_grupo():
    ok = {"kappa": 0.6, "revocacao": 0.7, "positivos": 5}
    assert vp.veredito(ok) == vp.USAR
    assert vp.veredito({**ok, "kappa": 0.59}) == vp.NAO_USAR
    assert vp.veredito({**ok, "revocacao": 0.69}) == vp.NAO_USAR
    assert vp.veredito({**ok, "positivos": 0, "revocacao": 0.0}) == vp.NAO_USAR
    assert vp.veredito({**ok, "kappa": None}) == vp.NAO_USAR
    assert vp.NAO_USAR == "NÃO usar para rótulos fracos nesse grupo"


def test_duvida_vazio_e_sem_resposta_ficam_de_fora_e_sao_contados():
    ouro = ouro_base()
    ouro[0]["duvida"] = "1"        # dúvida do João: fora de todos os grupos
    ouro[10]["interesse"] = ""     # sem rótulo de interesse: fora só do interesse
    r = vp.comparar(ouro, cache_de(ouro, ausentes={1}))  # índice 1 sem resposta da LLM: fora de todos
    assert r["risco"]["n"] == 30 - 2 and r["interesse"]["n"] == 30 - 3
    assert r["_fora"] == {"duvida": 1, "sem_resposta_da_llm": 1}


def test_grupo_so_com_um_valor_nao_quebra():
    ouro = [linha_ouro(i) for i in range(6)]  # nenhum positivo
    r = vp.comparar(ouro, cache_de(ouro))
    assert r["risco"]["positivos"] == 0 and vp.veredito(r["risco"]) == vp.NAO_USAR
