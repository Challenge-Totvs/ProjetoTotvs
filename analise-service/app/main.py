# main.py
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError

from app.config import obter_config
from app.erros import tratar_pedido_invalido
from app.router import router

obter_config()  # PIPELINE_VERSAO inválida derruba a subida com mensagem clara

app = FastAPI(title="InsightCall - Analise Service")
app.add_exception_handler(RequestValidationError, tratar_pedido_invalido)
app.include_router(router)
