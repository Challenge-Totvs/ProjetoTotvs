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
    with open(caminho, encoding="utf-8-sig", errors="replace", newline="") as f:
        return list(csv.DictReader(f))


def cabecalho_csv(caminho: Path) -> tuple[list[str], int]:
    """Nomes das colunas e número de linhas de dados, sem devolver conteúdo."""
    with open(caminho, encoding="utf-8-sig", errors="replace", newline="") as f:
        leitor = csv.reader(f)
        cabecalho = next(leitor, [])
        return cabecalho, sum(1 for _ in leitor)


# --- corpus no formato quebrado ------------------------------------------------------------------------------------
# O CSV exportado do corpus da TOTVS não segue o padrão: só a PRIMEIRA e a ÚLTIMA linha física de cada reunião vêm
# entre aspas (com `"` dobradas) e as linhas do meio vêm soltas. O `csv` padrão lê isso como centenas de milhares de
# "linhas" de um campo só. `ler_corpus` reconstrói uma linha por reunião; um CSV normal continua passando pelo `csv`.
_RE_INICIO_REUNIAO = re.compile(r'^"\d+,\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},')
_RE_FIM_REUNIAO = re.compile(r'^(.*)",([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*),([^,]*)$', re.DOTALL)
_CAMPOS_ANTES_DO_TEXTO = 10  # ID_MEETING..DT_CRIACAO (sem vírgula nem aspas); o texto é o 11º campo
_CAMPOS_DEPOIS_DO_TEXTO = 7  # UF..NOTA_NPS


def _abrir_texto(caminho: Path) -> str:
    return caminho.read_text(encoding="utf-8-sig", errors="replace")


def _linhas_do_arquivo(caminho: Path) -> list[str]:
    linhas = _abrir_texto(caminho).replace("\r\n", "\n").split("\n")
    while linhas and linhas[-1] == "":  # o arquivo termina com quebra de linha
        linhas.pop()
    return linhas


def _desembrulhar(linha: str) -> str:
    """Tira as aspas que embrulham a linha e desdobra as `""` internas."""
    if len(linha) >= 2 and linha.startswith('"') and linha.endswith('"'):
        linha = linha[1:-1]
    return linha.replace('""', '"')


def _corpus_quebrado(linhas: list[str]) -> bool:
    return len(linhas) > 1 and bool(_RE_INICIO_REUNIAO.match(linhas[1]))


def _registros_quebrados(linhas: list[str]) -> tuple[list[list[str]], int]:
    """Agrupa as linhas físicas por reunião (a partir de cada linha de início). Devolve (registros, linhas_orfas)."""
    grupos: list[list[str]] = []
    orfas = 0
    for linha in linhas[1:]:
        if _RE_INICIO_REUNIAO.match(linha):
            grupos.append([linha])
        elif grupos:
            grupos[-1].append(linha)
        elif linha.strip():
            orfas += 1
    return grupos, orfas


def _montar_reuniao(grupo: list[str], colunas: list[str]) -> dict[str, str] | None:
    primeira = _desembrulhar(grupo[0])
    partes = primeira.split(",", _CAMPOS_ANTES_DO_TEXTO)
    if len(partes) != _CAMPOS_ANTES_DO_TEXTO + 1 or not partes[-1].startswith('"'):
        return None
    texto = [partes[-1][1:]]
    if len(grupo) > 1:
        texto += grupo[1:-1]
        texto.append(_desembrulhar(grupo[-1]))
    achado = _RE_FIM_REUNIAO.match(texto[-1])
    if not achado:
        return None
    texto[-1] = achado.group(1)
    campos = partes[:-1] + ["\n".join(texto)] + list(achado.groups()[1:])
    return dict(zip(colunas, campos)) if len(campos) == len(colunas) else None


def ler_corpus(caminho: Path, contagem: dict | None = None) -> list[dict[str, str]]:
    """Uma linha por reunião, no formato normal do CSV ou no formato quebrado do corpus (ver acima).
    Registro que não fecha direito é descartado e só contado em `contagem["registros_invalidos"]`."""
    linhas = _linhas_do_arquivo(caminho)
    if not _corpus_quebrado(linhas):
        return ler_csv(caminho)
    colunas = next(csv.reader([linhas[0]]))
    if len(colunas) != _CAMPOS_ANTES_DO_TEXTO + 1 + _CAMPOS_DEPOIS_DO_TEXTO:
        raise SystemExit(f"erro: o corpus tem {len(colunas)} colunas; o leitor do formato quebrado espera 18")
    grupos, orfas = _registros_quebrados(linhas)
    reunioes = [m for m in (_montar_reuniao(g, colunas) for g in grupos) if m is not None]
    if contagem is not None:
        contagem["registros_invalidos"] = len(grupos) - len(reunioes)
        contagem["linhas_orfas"] = orfas
    return reunioes


def cabecalho_corpus(caminho: Path) -> tuple[list[str], int]:
    """Nomes das colunas e número de REUNIÕES (não de linhas físicas), sem devolver conteúdo."""
    linhas = _linhas_do_arquivo(caminho)
    if not _corpus_quebrado(linhas):
        return cabecalho_csv(caminho)
    return next(csv.reader([linhas[0]])), len(_registros_quebrados(linhas)[0])


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
