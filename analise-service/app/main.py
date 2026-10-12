# main.py
from fastapi import FastAPI

from app.config import carregar_dotenv, obter_config
from app.erros import registrar_handlers
from app.router import router

carregar_dotenv()  # só se analise-service/.env existir; não sobrescreve o ambiente
obter_config()  # PIPELINE_VERSAO inválida derruba a subida com mensagem clara

app = FastAPI(title="InsightCall - Analise Service")
registrar_handlers(app)
app.include_router(router)
