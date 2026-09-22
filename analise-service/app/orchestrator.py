from app.engines import llm_engine, modelo_local_engine
from app.schemas import AnaliseResponse

def analisar(conteudo: str) -> AnaliseResponse:
    engines = [llm_engine.analisar, modelo_local_engine.analisar]
    ultimo_erro = None

    for engine in engines:
        try:
            return engine(conteudo)
        except Exception as e:
            ultimo_erro = e

    raise ultimo_erro