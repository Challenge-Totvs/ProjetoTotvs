from fastapi import APIRouter
from app.schemas import AnaliseRequest, AnaliseResponse
from app.orchestrator import analisar

router = APIRouter()

@router.post("/analisar", response_model=AnaliseResponse)
def post_analisar(request: AnaliseRequest) -> AnaliseResponse:
    return analisar(request.conteudo)

