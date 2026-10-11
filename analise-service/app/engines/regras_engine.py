"""Motor `regras`: uma expressão regular por padrão (contrato v3 §5, SDD §6.3).

Primeira versão das 14 expressões, pendente de revisão do João Paulo (A8). As expressões casam
sobre o texto SEM acentos e em minúsculas; o recorte devolvido é sempre do texto recebido.
"""
import logging
import re
import unicodedata
from typing import Any, Iterable

from app.citacoes import conferir_citacoes
from app.erros import ErroMotor

logger = logging.getLogger(__name__)

LIMIAR_POSITIVO = 70  # [proposta] score >= 70 -> positivo
LIMIAR_NEUTRO = 45  # [proposta] score >= 45 -> neutro, senão negativo
SCORE_SEM_SINAIS = 50
MAX_INTERESSE = 20  # contrato §7.6
TAMANHO_MAXIMO_TEXTO = 600
TEXTO_DO_INTERESSE = "Palavra de interesse encontrada"

# padrao -> (título, tipo do padrão, expressão). Tipos e nomes: contrato §6.1.
_DEFINICOES: dict[str, tuple[str, str, str]] = {
    "suporte_insatisfacao": (
        "Insatisfação com o suporte", "risco",
        r"\b(suporte|atendimento|chamado|ticket)\b.{0,80}\b(demor\w*|ninguem\s+(retorn\w*|respond\w*)"
        r"|sem\s+(retorno|resposta)|nao\s+(retorn\w*|respond\w*|resolv\w*)|lent[oa]|pessim\w*|ruim|horriv\w*"
        r"|insatisf\w*|reclam\w*)"
        r"|\b(demor\w*|ninguem\s+retorn\w*)\b.{0,80}\b(suporte|atendimento|chamado)\b",
    ),
    "preco_objecao": (
        "Objeção de preço", "risco",
        r"\b(muito\s+caro|ficou\s+caro|esta\s+caro|e\s+caro|salgad[oa]|preco\s+(\w+\s+){0,2}(alto|elevado|puxado)"
        r"|valor\s+(\w+\s+){0,2}(alto|elevado|puxado|salgad[oa])|mais\s+barat[oa]"
        r"|acima\s+do\s+(nosso\s+)?(orcamento|mercado))\b",
    ),
    "prazo_implantacao": (
        "Prazo de implantação", "risco",
        r"\b(prazo|cronograma)\b.{0,60}\b(implanta\w*|implementa\w*|go[- ]?live|virada|migra\w*)"
        r"|\b(implanta\w*|implementa\w*|migra\w*)\b.{0,60}\b(prazo|atras\w*|demor\w*)"
        r"|\batras\w*\b.{0,40}\b(implanta\w*|projeto|go[- ]?live|cronograma)",
    ),
    "concorrente_citado": (
        "Concorrente citado", "risco",
        r"\b(concorrent\w*|outro\s+fornecedor|outra\s+empresa|outro\s+sistema|outra\s+solucao"
        r"|sap|oracle|omie|bling)\b",
    ),
    "cancelamento_citado": (
        "Cancelamento citado", "risco",
        r"\b(cancel\w*|rescind\w*|rescis\w*|encerrar\s+(o\s+)?contrato"
        r"|nao\s+(vamos|vou|pretendemos)\s+renovar|deixar\s+de\s+usar)\b",
    ),
    "adocao_resistencia": (
        "Resistência da equipe", "risco",
        r"\b(equipe|time|pessoal|usuarios|funcionarios|colaboradores)\b.{0,60}\b(resist\w*"
        r"|nao\s+(usa\w*|quer\w*|adaptou|se\s+adapt\w*|gost\w*)|dificuldade)"
        r"|\b(resistencia|ninguem\s+usa)\b",
    ),
    "fiscal_problema": (
        "Problema no fechamento fiscal", "risco",
        r"\b(fiscal|sped|nfe|nf-e|imposto\w*|tribut\w*|apuracao)\b.{0,80}\b(erro\w*|problema\w*|falh\w*|travou"
        r"|nao\s+(fecha|fechou|bate|gera\w*)|divergen\w*|rejei\w*)"
        r"|\b(erro\w*|problema\w*|falh\w*|divergen\w*|rejei\w*)\b.{0,80}\b(fiscal|sped|nfe|nf-e|imposto\w*"
        r"|tribut\w*|apuracao)\b",
    ),
    "orcamento_restrito": (
        "Orçamento restrito", "risco",
        r"\b(orcamento|verba|caixa|budget)\b.{0,60}\b(apertad\w*|curto|limitad\w*|restrit\w*|cortad\w*"
        r"|congelad\w*|estourad\w*|sem\s+folga)"
        r"|\b(sem\s+verba|sem\s+orcamento|corte\s+de\s+(custos|orcamento)"
        r"|congelamento\s+de\s+(gastos|orcamento)|congel\w+\s+(novas\s+)?compras)\b",
    ),
    "expansao_unidade": (
        "Expansão para nova unidade", "oportunidade",
        r"\b(nova|novo|outra|mais\s+uma)\s+(unidade|filial|loja|sede|clinica)\b"
        r"|\b(unidade|filial|loja|sede)\s+nova\b"
        r"|\b(abrir|abrindo|inaugur\w*|expandir)\b.{0,50}\b(unidade|filial|loja|sede|clinica)\b|\bexpansao\b",
    ),
    "modulo_adicional": (
        "Módulo adicional", "oportunidade",
        r"\b(modulos?|add-?on|business\s+intelligence|telemedicina)\b"
        r"|\b(queremos|querem|gostaria\w*|interesse\s+em|precisamos\s+de)\b.{0,40}\b(dashboard|painel|bi)\b",
    ),
    "integracao": (
        "Integração com outro sistema", "oportunidade",
        r"\b(integra\w*|api|webservice|web\s+service|sincroniz\w*|conectar\s+com)\b",
    ),
    "renovacao": (
        "Renovação do contrato", "oportunidade",
        r"\b(renova\w*|prorrog\w*|continuidade\s+do\s+contrato|estender\s+o\s+contrato)\b",
    ),
    "upgrade_licencas": (
        "Ampliação de licenças", "oportunidade",
        r"\b(mais|novas|adicionais|ampliar|aumentar|comprar)\b.{0,30}\blicenc\w*"
        r"|\blicenc\w*\b.{0,30}\b(adicionais|extras?)\b|\bupgrade\b|\bmais\s+usuarios\b"
        r"|\busuarios\s+adicionais\b|\bplano\s+(maior|superior)\b",
    ),
    "treinamento": (
        "Treinamento da equipe", "oportunidade",
        r"\b(treinament\w*|treinar|capacita\w*|onboarding|workshop|reciclagem|aprender\s+a\s+usar)\b",
    ),
}

EXPRESSOES: dict[str, re.Pattern] = {p: re.compile(d[2]) for p, d in _DEFINICOES.items()}
TITULO_DO_PADRAO = {p: d[0] for p, d in _DEFINICOES.items()}
TIPO_DO_PADRAO = {p: d[1] for p, d in _DEFINICOES.items()}

EXPRESSAO_INTERESSE = re.compile(
    r"\b(ajuda\s+bastante|ajuda\s+muito|gostei\w*|interessante|interessad[oa]|otimo|excelente|perfeito"
    r"|combinado|fechado|vamos\s+fechar|pode\s+enviar|manda\s+a\s+proposta|queremos\s+avancar)\b"
)


def dobrar(texto: str) -> str:
    """Minúsculas e sem acentos, caractere a caractere: os índices continuam valendo no original (NFC)."""
    saida = []
    for c in unicodedata.normalize("NFC", texto):
        base = unicodedata.normalize("NFD", c)[0].lower()
        saida.append(base if len(base) == 1 else c)
    return "".join(saida)


def sentimento_do_score(score: int) -> str:
    if score >= LIMIAR_POSITIVO:
        return "positivo"
    if score >= LIMIAR_NEUTRO:
        return "neutro"
    return "negativo"


def _recorte(texto: str, inicio_do_acerto: int) -> str:
    if len(texto) <= TAMANHO_MAXIMO_TEXTO:
        return texto
    inicio = max(0, inicio_do_acerto - TAMANHO_MAXIMO_TEXTO // 4)
    return texto[inicio : inicio + TAMANHO_MAXIMO_TEXTO].strip()


def _turnos_nfc(pedido: Any) -> list[tuple[int, str]]:
    turnos = [(t.n, unicodedata.normalize("NFC", t.texto)) for t in pedido.turnos]
    if not any(texto.strip() for _, texto in turnos):
        raise ErroMotor("entrada_sem_trechos")
    return turnos


def _suprimidos(pedido: Any) -> dict[str, list[str]]:
    """Textos (dobrados) que o vendedor já marcou como 'não procede', por padrão."""
    por_padrao: dict[str, list[str]] = {}
    for c in pedido.contraexemplos:
        por_padrao.setdefault(c.padrao, []).append(dobrar(c.texto).strip())
    for c in pedido.correcoesAnteriores:
        por_padrao.setdefault(c.padrao, []).append(dobrar(c.textoOriginal).strip())
    return por_padrao


def extrair_temas(pedido: Any) -> tuple[list[dict], list[dict]]:
    """Um tema por padrão (primeira ocorrência), conferido por `conferir_citacoes`. Devolve (temas, descartados)."""
    turnos = _turnos_nfc(pedido)
    ativos = list(pedido.padroes) or list(EXPRESSOES)
    suprimidos = _suprimidos(pedido)
    candidatos: list[dict] = []
    for padrao in EXPRESSOES:
        if padrao not in ativos:
            continue
        for n, texto in turnos:
            dobrado = dobrar(texto)
            achado = EXPRESSOES[padrao].search(dobrado)
            if not achado:
                continue
            if any(s and (s in dobrado or dobrado.strip() in s) for s in suprimidos.get(padrao, [])):
                continue
            candidatos.append({
                "padrao": padrao,
                "titulo": TITULO_DO_PADRAO[padrao],
                "tipos": [TIPO_DO_PADRAO[padrao]],
                "turno": n,
                "tratado": None,
                "texto": _recorte(texto, achado.start()),
            })
            break
    candidatos.sort(key=lambda t: t["turno"])
    return conferir_citacoes(pedido.turnos, candidatos, origem="tema")


def extrair_interesse(pedido: Any, turnos_permitidos: Iterable[int] | None = None) -> tuple[list[dict], list[dict]]:
    """Turnos com palavra de interesse. `turnos_permitidos` (opcional) restringe a quais turnos."""
    permitidos = None if turnos_permitidos is None else set(turnos_permitidos)
    candidatos = []
    for n, texto in _turnos_nfc(pedido):
        if permitidos is not None and n not in permitidos:
            continue
        achado = EXPRESSAO_INTERESSE.search(dobrar(texto))
        if achado:
            candidatos.append({"texto": TEXTO_DO_INTERESSE, "turno": n, "citacao": _recorte(texto, achado.start())})
    confirmados, descartados = conferir_citacoes(pedido.turnos, candidatos, origem="interesse", campo_texto="citacao")
    return confirmados[:MAX_INTERESSE], descartados


def calcular_score(temas: list[dict], interesse: list[dict]) -> int:
    """Proporção de sinais positivos (interesse + temas de oportunidade) entre todos os sinais; 50 sem sinais."""
    positivos = len(interesse) + sum(1 for t in temas if "oportunidade" in t["tipos"])
    negativos = sum(1 for t in temas if "risco" in t["tipos"] and "oportunidade" not in t["tipos"])
    if positivos + negativos == 0:
        return SCORE_SEM_SINAIS
    return round(100 * positivos / (positivos + negativos))


def analisar(pedido: Any) -> dict:
    temas, descartados_temas = extrair_temas(pedido)
    interesse, descartados_interesse = extrair_interesse(pedido)
    score = calcular_score(temas, interesse)
    logger.info("regras: temas=%d interesse=%d descartados=%d", len(temas), len(interesse),
                len(descartados_temas) + len(descartados_interesse))
    return {
        "score": score,
        "sentimento": sentimento_do_score(score),
        "interesse": interesse,
        "temas": temas,
        "descartados": [*descartados_temas, *descartados_interesse],
    }
