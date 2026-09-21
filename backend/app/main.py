from fastapi import FastAPI
from app.core.config import settings
from app.routers import pqrs

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(pqrs.router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"estado": "ok", "mensaje": "API de Triaje PQRS operativa"}