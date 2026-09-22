# main.py
from fastapi import FastAPI
from app.router import router

app = FastAPI(title="InsightCall - Analise Service")
app.include_router(router)