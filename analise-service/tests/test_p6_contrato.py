"""Contrato Python x Java (AC2, AC9 lado Python). O Java é a referência (CLAUDE.md, regra 1)."""
import json
import re
from pathlib import Path
from typing import get_args

import pytest

from app.schemas import AnaliseResponse, Aviso, ErroTentativa, MotivoDescarte, Motor, Padrao, Papel, RegraPrazo, Sentimento, TipoTema

RAIZ = Path(__file__).resolve().parents[2]
CONTRATO = RAIZ / "docs" / "contrato"
DOMINIO_JAVA = RAIZ / "backend" / "src" / "main" / "java" / "com" / "challengetotvs" / "api" / "domain" / "analise"

# Origem: MotorUtilizado.java e SentimentoGeral.java (o JSON usa name().toLowerCase()); contrato-v3.md §4 e §6.
MOTORES_JAVA = {"llm1", "llm2", "local", "regras"}
SENTIMENTOS_JAVA = {"positivo", "neutro", "negativo"}
CAMPOS_DA_RESPOSTA_JAVA = {  # ContratoV3.Resposta
    "motor", "tentativas", "score", "sentimento", "papeis", "resumo", "interesse", "proximosPassos", "temas",
    "compromissos", "sentimentoSerie", "descartados",
}


def _json(nome):
    return json.loads((CONTRATO / nome).read_text(encoding="utf-8"))


def _valores_do_enum_java(arquivo: str) -> set[str]:
    corpo = re.search(r"enum\s+\w+\s*\{\s*([A-Z0-9_,\s]+);", (DOMINIO_JAVA / arquivo).read_text(encoding="utf-8"))
    return {nome.strip().lower() for nome in corpo.group(1).split(",") if nome.strip()}


def _campos_da_resposta_java() -> set[str]:
    texto = (DOMINIO_JAVA / "ContratoV3.java").read_text(encoding="utf-8")
    cabecalho = re.search(r"record\s+Resposta\((.*?)\)\s*\{", texto, re.DOTALL).group(1)
    while re.search(r"<[^<>]*>", cabecalho):  # tira os genéricos, de dentro para fora
        cabecalho = re.sub(r"<[^<>]*>", "", cabecalho)
    return {componente.split()[-1] for componente in cabecalho.split(",") if componente.strip()}


# --- constantes (valem mesmo sem o backend no checkout) ---

def test_enums_do_python_batem_com_os_valores_do_java():
    assert set(get_args(Motor)) == MOTORES_JAVA
    assert set(get_args(Sentimento)) == SENTIMENTOS_JAVA


def test_campos_lidos_pelo_java_existem_na_resposta_do_python():
    assert CAMPOS_DA_RESPOSTA_JAVA <= set(AnaliseResponse.model_fields)


def test_tipos_do_tema_sao_minusculos_como_o_java_compara():
    assert set(get_args(TipoTema)) == {"risco", "oportunidade"}


@pytest.mark.parametrize("nome", ["resposta-v3-llm.json", "resposta-v3-local.json", "resposta-v3-regras.json"])
def test_fixtures_usam_so_valores_que_o_java_aceita(nome):
    resposta = _json(nome)
    assert resposta["motor"] in MOTORES_JAVA and resposta["sentimento"] in SENTIMENTOS_JAVA
    assert all(t["motor"] in MOTORES_JAVA for t in resposta["tentativas"])
    assert all(set(t["tipos"]) <= {"risco", "oportunidade"} and isinstance(t["turno"], int) for t in resposta["temas"])
    assert all(isinstance(i["turno"], int) for i in resposta.get("interesse", []) + resposta.get("compromissos", []))
    assert all(isinstance(p, list) and len(p) == 2 for p in resposta.get("sentimentoSerie", []))
    AnaliseResponse.model_validate(resposta)


def test_listas_fechadas_do_python_batem_com_o_contrato():
    texto = (CONTRATO / "contrato-v3.md").read_text(encoding="utf-8")
    secao = texto.split("### 6.1", 1)[1].split("### 6.2", 1)[0]
    assert set(re.findall(r"^\| `(\w+)` \|", secao, re.MULTILINE)) == set(get_args(Padrao))
    assert len(get_args(Padrao)) == 14

    def lista(titulo):
        corpo = texto.split(titulo, 1)[1].split("###", 1)[0]
        paragrafo = corpo.split("\n\n", 1)[1]
        return set(re.findall(r"(?:^|·\s*)`(\w+)`", paragrafo.strip()))  # só o 1º código de cada item "a · b · c"

    assert set(get_args(ErroTentativa)) == lista("### 6.5")
    assert set(get_args(Aviso)) == lista("### 6.6")
    assert set(get_args(MotivoDescarte)) == lista("### 6.7") - {"tema", "interesse", "compromisso", "eventoConduta"}
    assert set(get_args(RegraPrazo)) | {"null"} == lista("### 6.4") | {"null"}
    assert set(get_args(Papel)) == {"vendedor", "cliente"}


# --- comparação direta com o Java, quando o backend está no checkout ---

@pytest.mark.skipif(not (DOMINIO_JAVA / "ContratoV3.java").exists(), reason="backend/ ausente deste checkout")
def test_enums_e_campos_lidos_direto_dos_arquivos_java():
    assert _valores_do_enum_java("MotorUtilizado.java") == set(get_args(Motor))
    assert _valores_do_enum_java("SentimentoGeral.java") == set(get_args(Sentimento))
    campos_java = _campos_da_resposta_java()
    assert campos_java == CAMPOS_DA_RESPOSTA_JAVA
    assert campos_java <= set(AnaliseResponse.model_fields)
