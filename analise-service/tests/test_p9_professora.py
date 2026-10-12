"""P9 — validar_professora.py: LLM da destilação × rótulos do João no ouro. Tudo SINTÉTICO, cliente simulado."""
import datetime as dt
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


# ------------------------------------------------------------------ etapa 2: CLI, cache, teto, relatório

class LLMFalsa:
    """Cliente simulado: lê as marcas sintéticas do prompt e devolve os rótulos 'certos' (nenhuma rede)."""

    def __init__(self, erro_risco_em=(), tokens=(1000, 200)):
        self.chamadas, self.erro_risco_em, self.tokens = 0, set(erro_risco_em), tokens

    def __call__(self, prompt):
        self.chamadas += 1
        itens = []
        for m in re.finditer(r"\[item (\d+)\] contexto:.*?\|\| FALA ALVO: (.*)", prompt):
            texto = m.group(2)
            risco = (MARCA["risco"] in texto) != (int(texto.split()[2]) in self.erro_risco_em)
            itens.append({"item": int(m.group(1)), "risco": risco, "oportunidade": MARCA["oportunidade"] in texto,
                          "interesse": MARCA["interesse"] in texto})
        return itens, *self.tokens


def montar_pasta(tmp_path: Path, completo=False, modo="unico", ouro=None) -> Path:
    comum.gravar_csv(tmp_path / "ouro_final.csv", ouro or ouro_base(), conciliar_ouro.COLUNAS_OURO)
    (tmp_path / "ouro_final.json").write_text(json.dumps({"modo": modo, "completo": completo}), encoding="utf-8")
    return tmp_path


def rodar(tmp_path: Path, llm, *extra, teto="0.5"):
    return vp.main(["--ouro", str(tmp_path / "ouro_final.csv"), "--pasta", str(tmp_path / "professora"),
                    "--veredito", str(tmp_path / "professora_veredito.json"),
                    "--relatorio", str(tmp_path / "professora.md"), "--teto-usd", teto, "--preco-entrada", "0.15",
                    "--preco-saida", "0.60", *extra], chamar=llm)


def test_main_gera_relatorio_so_com_metricas(tmp_path, capsys):
    montar_pasta(tmp_path)
    llm = LLMFalsa()
    assert rodar(tmp_path, llm) == 0 and llm.chamadas == 2  # 30 trechos em lotes de 20
    relatorio = (tmp_path / "professora.md").read_text(encoding="utf-8")
    saida = capsys.readouterr().out
    for texto in (relatorio, saida):
        assert "Frase sintética" not in texto and "alfaRISCO" not in texto
    assert "rotulador único" in relatorio and "PARCIAL" in relatorio and "indicativ" in relatorio
    assert relatorio.count(f"**{vp.USAR}**") == 3 and "kappa" in relatorio and "alarme falso" in relatorio.lower()
    assert json.loads(saida)["veredito"] == {"risco": "usar", "oportunidade": "usar", "interesse": "usar"}


def test_main_ouro_completo_e_veredito_nao_usar(tmp_path):
    montar_pasta(tmp_path, completo=True)
    assert rodar(tmp_path, LLMFalsa(erro_risco_em=range(0, 6))) == 0  # erra 6 dos 10 positivos de risco
    relatorio = (tmp_path / "professora.md").read_text(encoding="utf-8")
    assert "COMPLETO" in relatorio and "PARCIAL" not in relatorio
    assert f"risco: **{vp.NAO_USAR}**" in relatorio and f"oportunidade: **{vp.USAR}**" in relatorio


def test_main_retoma_do_cache_sem_chamar_de_novo(tmp_path):
    montar_pasta(tmp_path)
    rodar(tmp_path, LLMFalsa())
    segunda = LLMFalsa()
    assert rodar(tmp_path, segunda) == 0 and segunda.chamadas == 0


def test_main_para_no_teto_e_marca_preliminar(tmp_path):
    montar_pasta(tmp_path)
    llm = LLMFalsa()
    # preço absurdo: a estimativa do 1º lote já passa do teto => nenhuma chamada
    codigo = vp.main(["--ouro", str(tmp_path / "ouro_final.csv"), "--pasta", str(tmp_path / "professora"),
                      "--veredito", str(tmp_path / "professora_veredito.json"),
                      "--relatorio", str(tmp_path / "professora.md"), "--teto-usd", "0.01",
                      "--preco-entrada", "1000", "--preco-saida", "1000"], chamar=llm)
    assert codigo == 0 and llm.chamadas == 0
    relatorio = (tmp_path / "professora.md").read_text(encoding="utf-8")
    assert "PRELIMINAR" in relatorio and f"**{vp.NAO_USAR}**" in relatorio


def test_teto_obrigatorio_e_no_maximo_meio_dolar(tmp_path):
    montar_pasta(tmp_path)
    base = ["--ouro", str(tmp_path / "ouro_final.csv"), "--pasta", str(tmp_path / "professora"),
            "--veredito", str(tmp_path / "professora_veredito.json"),
            "--relatorio", str(tmp_path / "professora.md"), "--preco-entrada", "0.15", "--preco-saida", "0.6"]
    llm = LLMFalsa()
    with pytest.raises(SystemExit):
        vp.main(base, chamar=llm)  # sem --teto-usd
    with pytest.raises(SystemExit):
        vp.main([*base, "--teto-usd", "0.51"], chamar=llm)
    with pytest.raises(SystemExit):
        vp.main([*base, "--teto-usd", "0"], chamar=llm)
    assert llm.chamadas == 0
    assert vp.main([*base, "--teto-usd", "0.5"], chamar=llm) == 0


def test_erro_do_provedor_mostra_so_codigo(tmp_path, capsys):
    montar_pasta(tmp_path)

    def quebrada(prompt):
        raise RuntimeError("mensagem secreta Frase sintética 3")

    assert rodar(tmp_path, quebrada) == 2
    texto = capsys.readouterr().out + (tmp_path / "professora.md").read_text(encoding="utf-8")
    assert "mensagem secreta" not in texto and "Frase sintética" not in texto and "PRELIMINAR" in texto


def test_sem_ouro_final_para_com_mensagem(tmp_path, capsys):
    assert vp.main(["--ouro", str(tmp_path / "nao_existe.csv"), "--teto-usd", "0.5", "--preco-entrada", "1",
                    "--preco-saida", "1"], chamar=LLMFalsa()) == 1
    assert "não encontrado" in capsys.readouterr().out


def test_help_roda():
    r = subprocess.run([sys.executable, "treino/validar_professora.py", "--help"], cwd=RAIZ, capture_output=True)
    assert r.returncode == 0 and b"--teto-usd" in r.stdout


def test_main_grava_o_veredito_por_grupo_para_o_treino(tmp_path, capsys):
    montar_pasta(tmp_path, completo=True)
    assert rodar(tmp_path, LLMFalsa(erro_risco_em=range(0, 6))) == 0
    caminho = tmp_path / "professora_veredito.json"
    veredito = json.loads(caminho.read_text(encoding="utf-8"))
    assert veredito == {"risco": "nao_usar", "oportunidade": "usar", "interesse": "usar",
                        "data": dt.date.today().isoformat()}
    assert json.loads(capsys.readouterr().out)["veredito_gravado"] == "professora_veredito.json"
    assert "Frase sintética" not in caminho.read_text(encoding="utf-8")
    from treino import treinar

    assert treinar.ler_veredito(caminho) == veredito  # o treino lê o mesmo formato


def test_rodada_preliminar_nao_grava_nem_sobrescreve_o_veredito(tmp_path):
    montar_pasta(tmp_path)
    caro = ("--preco-entrada", "1000", "--preco-saida", "1000")  # o 1º lote já passa do teto: nada é chamado
    assert rodar(tmp_path, LLMFalsa(), *caro, teto="0.01") == 0
    assert not (tmp_path / "professora_veredito.json").exists()
    anterior = '{"risco": "usar", "oportunidade": "usar", "interesse": "usar", "data": "2026-10-01"}\n'
    (tmp_path / "professora_veredito.json").write_text(anterior, encoding="utf-8")
    assert rodar(tmp_path, LLMFalsa(), *caro, teto="0.01") == 0
    assert (tmp_path / "professora_veredito.json").read_text(encoding="utf-8") == anterior
