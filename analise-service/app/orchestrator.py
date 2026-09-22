from app.engines import llm_engine, modelo_local_engine
from app.schemas import AnaliseResponse

def analisar(conteudo : str) -> AnaliseResponse:
    try: 
        return llm_engine.analisar(conteudo)
    except Exception:
        pass   

    try:
        return modelo_local_engine.analisar(conteudo)
    except Exception:
        pass


    