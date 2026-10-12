"""Resposta gravada do PIPELINE_VERSAO=mock (contrato v3 §8.2)."""
import json
from functools import lru_cache
from pathlib import Path

CAMINHO_RESPOSTA_MOCK = Path(__file__).resolve().parents[2] / "docs" / "contrato" / "resposta-v3-llm.json"


@lru_cache
def carregar_resposta_mock() -> dict:
    if not CAMINHO_RESPOSTA_MOCK.is_file():
        raise FileNotFoundError(f"Resposta do mock não encontrada: {CAMINHO_RESPOSTA_MOCK}")
    return json.loads(CAMINHO_RESPOSTA_MOCK.read_text(encoding="utf-8"))
