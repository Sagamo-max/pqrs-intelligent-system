from fastapi import FastAPI
from app.routers import health

# Inicialización de la aplicación FastAPI
app = FastAPI(
    title="PQRS Intelligent Triage API",
    description="Módulo inteligente para clasificación y direccionamiento de PQRS",
    version="0.1.0"
)

# Conectar el router de health a la app principal
app.include_router(health.router)
