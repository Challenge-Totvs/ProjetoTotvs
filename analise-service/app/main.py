# main.py
from fastapi import FastAPI

from app.config import obter_config
from app.erros import registrar_handlers
from app.router import router

obter_config()  # PIPELINE_VERSAO inválida derruba a subida com mensagem clara

app = FastAPI(title="InsightCall - Analise Service")
registrar_handlers(app)
app.include_router(router)
