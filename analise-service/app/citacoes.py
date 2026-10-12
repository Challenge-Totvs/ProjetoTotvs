"""Conferência de citações literais (contrato v3 §7.2, SDD §5.7). Função pura, sem I/O."""
import unicodedata
from typing import Any, Iterable, Mapping

TAMANHO_MINIMO = 10
TAMANHO_MAXIMO = 600
VIZINHANCA = 2
JANELAS = (2, 3)

_SUBSTITUICOES = {
    "“": '"', "”": '"', "‘": "'", "’": "'",
    "–": "-", "—": "-",
    "…": "...",
}


def _normalizar(texto: str) -> tuple[str, list[int]]:
    """Normaliza e devolve, para cada caractere normalizado, o índice no texto NFC original."""
    nfc = unicodedata.normalize("NFC", texto)
    saida: list[str] = []
    mapa: list[int] = []
    anterior_espaco = True  # descarta espaços do começo
    for i, c in enumerate(nfc):
        if c.isspace():
            if not anterior_espaco:
                saida.append(" ")
                mapa.append(i)
            anterior_espaco = True
            continue
        anterior_espaco = False
        for s in _SUBSTITUICOES.get(c, c).lower():
            saida.append(s)
            mapa.append(i)
    if saida and saida[-1] == " ":
        saida.pop()
        mapa.pop()
    return "".join(saida), mapa


def _campo(obj: Any, nome: str) -> Any:
    return obj[nome] if isinstance(obj, Mapping) else getattr(obj, nome)


class _Turnos:
    def __init__(self, turnos: Iterable[Any]):
        self.numeros: list[int] = []
        self.originais: list[str] = []
        self.normalizados: list[tuple[str, list[int]]] = []
        for t in turnos:
            texto = unicodedata.normalize("NFC", _campo(t, "texto"))
            self.numeros.append(_campo(t, "n"))
            self.originais.append(texto)
            self.normalizados.append(_normalizar(texto))

    def posicao(self, n: int) -> int | None:
        try:
            return self.numeros.index(n)
        except ValueError:
            return None

    def buscar(self, alvo: str, inicio: int, fim: int) -> tuple[int, int, str] | None:
        """Procura `alvo` nos turnos [inicio, fim] (posições) concatenados com um espaço."""
        palheiro = ""
        origem: list[tuple[int, int]] = []  # (posição do turno, índice no original) por caractere
        for p in range(inicio, fim + 1):
            if p > inicio:
                palheiro += " "
                origem.append((p, -1))
            norm, mapa = self.normalizados[p]
            palheiro += norm
            origem.extend((p, idx) for idx in mapa)
        achado = palheiro.find(alvo)
        if achado < 0:
            return None
        p_ini, i_ini = origem[achado]
        p_fim, i_fim = origem[achado + len(alvo) - 1]
        if p_ini == p_fim:
            texto = self.originais[p_ini][i_ini : i_fim + 1]
        else:
            partes = [self.originais[p_ini][i_ini:]]
            partes += [self.originais[p] for p in range(p_ini + 1, p_fim)]
            partes.append(self.originais[p_fim][: i_fim + 1])
            texto = " ".join(partes)
        return self.numeros[p_ini], self.numeros[p_fim], texto

    def localizar(self, alvo: str, turno: int) -> tuple[int, int, str] | None:
        centro = self.posicao(turno)
        if centro is None:
            return None
        centros = [centro]
        for d in range(1, VIZINHANCA + 1):
            centros += [centro - d, centro + d]
        menor = max(0, centro - VIZINHANCA)
        maior = min(len(self.numeros) - 1, centro + VIZINHANCA)
        for c in centros:
            if not menor <= c <= maior:
                continue
            candidatos = [(c, c)]
            for tamanho in JANELAS:
                for ini in range(c - tamanho + 1, c + 1):
                    if ini >= menor and ini + tamanho - 1 <= maior:
                        candidatos.append((ini, ini + tamanho - 1))
            for ini, fim in candidatos:
                achado = self.buscar(alvo, ini, fim)
                if achado:
                    return achado
        return None


def conferir_citacoes(
    turnos: Iterable[Any],
    itens: Iterable[Mapping[str, Any]],
    *,
    origem: str,
    campo_texto: str = "texto",
) -> tuple[list[dict], list[dict]]:
    """Confere cada item contra os turnos recebidos.

    `itens` são mapeamentos com `turno` e o campo de texto (`campo_texto`). Devolve
    `(confirmados, descartados)`: os confirmados são cópias com `turno` corrigido, `turnoFim`
    preenchido e o texto igual ao recebido; os descartados seguem o formato de `descartados`
    do contrato (`texto`, `motivo`, `origem`, `padrao` quando o item tem). Não altera as entradas.
    """
    base = _Turnos(turnos)
    confirmados: list[dict] = []
    descartados: list[dict] = []
    for item in itens:
        texto = item[campo_texto]
        alvo, _ = _normalizar(texto)
        motivo = None
        if len(alvo) < TAMANHO_MINIMO:
            motivo = "trecho_curto"
        elif len(alvo) > TAMANHO_MAXIMO:
            motivo = "trecho_longo"
        else:
            achado = base.localizar(alvo, item["turno"])
            if achado is None:
                motivo = "evidencia_nao_localizada"
        if motivo:
            descarte = {"texto": texto, "motivo": motivo, "origem": origem}
            if item.get("padrao"):
                descarte["padrao"] = item["padrao"]
            descartados.append(descarte)
            continue
        inicio, fim, recebido = achado
        confirmados.append({**item, "turno": inicio, "turnoFim": fim, campo_texto: recebido})
    return confirmados, descartados
