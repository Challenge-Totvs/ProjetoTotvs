"""Configuração do serviço, lida das variáveis de ambiente em um único lugar."""
import os
from dataclasses import dataclass
from functools import lru_cache

VERSOES_PIPELINE = ("real", "mock")


@dataclass(frozen=True)
class Config:
    pipeline_versao: str


@lru_cache
def obter_config() -> Config:
    pipeline_versao = os.environ.get("PIPELINE_VERSAO", "real").strip().lower() or "real"
    if pipeline_versao not in VERSOES_PIPELINE:
        raise ValueError(
            f"PIPELINE_VERSAO inválida: {pipeline_versao!r}. Use um de: {', '.join(VERSOES_PIPELINE)}."
        )
    return Config(pipeline_versao=pipeline_versao)
