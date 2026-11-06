from fastapi import FastAPI
from app.core.config import settings
from app.routers import ticket, health
from app.routers import area as area_router
from app.routers import area as area_router, audit as audit_router
from app.routers import alert as alert_router
from app.routers import auth as auth_router
from app.routers import stats as stats_router
from app.routers import events as events_router
from app.routers import integration as integration_router
from app.routers import organizacion as organizacion_router

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(auth_router.router)
app.include_router(health.router)
app.include_router(ticket.router, prefix=settings.API_V1_STR)
app.include_router(area_router.router, prefix=settings.API_V1_STR)
app.include_router(audit_router.router, prefix=settings.API_V1_STR)
app.include_router(stats_router.router, prefix=settings.API_V1_STR)
app.include_router(alert_router.router, prefix=settings.API_V1_STR)
app.include_router(events_router.router)
app.include_router(integration_router.router)
app.include_router(organizacion_router.router)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Ticket triage API operational"}