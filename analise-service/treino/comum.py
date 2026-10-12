"""Peças comuns do pipeline de retreino (P8). Nada aqui imprime texto de trecho: só contagens e métricas.

Dados reais ficam em `analise-service/dados_locais/` (ignorado pelo git). Os testes usam dados sintéticos.
"""
import csv
import hashlib
import json
import re
import sys
import unicodedata
from pathlib import Path
from typing import Iterable

RAIZ = Path(__file__).resolve().parent.parent
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from app.engines.regras_engine import TIPO_DO_PADRAO  # noqa: E402

DADOS = RAIZ / "dados_locais"
EVIDENCIAS = RAIZ.parent / "docs" / "evidencias"
CAMINHO_MODELO_ATUAL = RAIZ / "app" / "modelos" / "classificador_risco.joblib"

GRUPOS = ("risco", "oportunidade", "interesse")
PADROES = tuple(TIPO_DO_PADRAO)
SEM_PADRAO = "nenhum"

# Regra única de leitura dos turnos (SDD §5.2, a mesma do Java).
_RE_LOCUTOR = re.compile(r"^\s*\[LOCUTOR\s*(\d+)\]\s*:?\s*(.*)$", re.IGNORECASE)

# Campos de texto do corpus podem passar do limite padrão do módulo csv (128 KB).
csv.field_size_limit(min(sys.maxsize, 2**31 - 1))


def dividir_turnos(transcricao: str) -> list[tuple[int, str]]:
    """`[(locutor, texto)]` na ordem; o número do turno é a posição + 1 (SDD §5.2)."""
    turnos: list[list] = []
    for linha in transcricao.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        achado = _RE_LOCUTOR.match(linha)
        if achado:
            turnos.append([int(achado.group(1)), achado.group(2).strip()])
        elif linha.strip() and turnos:
            turnos[-1][1] = (turnos[-1][1] + " " + linha.strip()).strip()
    return [(locutor, unicodedata.normalize("NFC", texto)) for locutor, texto in turnos if texto]


def sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn").lower().strip()


def normalizar_padrao(valor: object) -> str | None:
    """Um dos 14 padrões, `nenhum` (vazio/sem padrão) ou None (valor que não é padrão: provável erro de digitação)."""
    texto = sem_acento(str(valor or "")).replace(" ", "_").replace("-", "_")
    if texto in ("", "nenhum", "nao", "none", "na", "n/a", "sem_padrao", "_"):
        return SEM_PADRAO
    return texto if texto in PADROES else None


def normalizar_sim_nao(valor: object) -> bool | None:
    texto = sem_acento(str(valor if valor is not None else ""))
    if texto in ("sim", "s", "1", "true", "x", "yes", "verdadeiro"):
        return True
    if texto in ("nao", "n", "0", "false", "", "no", "falso"):
        return False
    return None


def grupos_dos_padroes(padroes: Iterable[str]) -> dict[str, bool]:
    tipos = {TIPO_DO_PADRAO[p] for p in padroes if p in TIPO_DO_PADRAO}
    return {"risco": "risco" in tipos, "oportunidade": "oportunidade" in tipos}


def sha256_arquivo(caminho: Path) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def ler_csv(caminho: Path) -> list[dict[str, str]]:
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def cabecalho_csv(caminho: Path) -> tuple[list[str], int]:
    """Nomes das colunas e número de linhas de dados, sem devolver conteúdo."""
    with open(caminho, encoding="utf-8-sig", newline="") as f:
        leitor = csv.reader(f)
        cabecalho = next(leitor, [])
        return cabecalho, sum(1 for _ in leitor)


def gravar_csv(caminho: Path, linhas: list[dict], colunas: list[str]) -> None:
    caminho.parent.mkdir(parents=True, exist_ok=True)
    with open(caminho, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=colunas, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(linhas)


def imprimir(resumo: dict) -> None:
    """Saída padrão dos scripts: um JSON só com contagens e métricas."""
    print(json.dumps(resumo, ensure_ascii=False, indent=2))


def bool_csv(valor: object) -> str:
    return "" if valor is None else ("1" if valor else "0")


def ler_bool_csv(valor: str | None) -> bool | None:
    return None if valor in (None, "") else valor == "1"
