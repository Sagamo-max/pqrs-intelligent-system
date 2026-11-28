import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routers import alert as alert_router
from app.routers import area as area_router
from app.routers import audit as audit_router
from app.routers import auth as auth_router
from app.routers import dashboard as dashboard_router
from app.routers import health
from app.routers import stats as stats_router
from app.routers import ticket


def get_cors_origins() -> list[str]:
    raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
    return [origin.strip() for origin in raw_origins.split(",") if origin.strip()]


app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router)
app.include_router(health.router)

# Orden crítico: rutas estáticas (/pqrs/stats, /pqrs/alerts) y sub-rutas de auditoría
# deben registrarse ANTES de ticket.router para evitar colisión con GET /pqrs/{ticket_id}.
for prefix in (settings.API_V1_STR, "/api"):
    app.include_router(stats_router.router, prefix=prefix)
    app.include_router(alert_router.router, prefix=prefix)
    app.include_router(audit_router.router, prefix=prefix)
    app.include_router(area_router.router, prefix=prefix)
    app.include_router(dashboard_router.router, prefix=prefix)
    app.include_router(ticket.router, prefix=prefix)


@app.get("/")
def read_root():
    return {"status": "ok", "message": "Ticket triage API operational"}
