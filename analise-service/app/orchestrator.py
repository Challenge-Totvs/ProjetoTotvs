from app.engines import llm_engine, modelo_local_engine
from app.schemas import AnaliseResponseV1
from functools import partial


def analisar(conteudo: str) -> AnaliseResponseV1:
    engines = [
            partial(llm_engine.analisar, provider="anthropic"),
            partial(llm_engine.analisar, provider="openai"),
            modelo_local_engine.analisar
        ]
    ultimo_erro = None

    for engine in engines:
        try:
            return engine(conteudo)
        except Exception as e:
            ultimo_erro = e

    raise ultimo_erro