from fastapi import FastAPI
from app.core.config import settings
from app.routers import ticket, health
from app.routers import area as area_router
from app.routers import area as area_router, audit as audit_router
from app.routers import stats as stats_router

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(health.router)
app.include_router(ticket.router, prefix=settings.API_V1_STR)
app.include_router(area_router.router, prefix=settings.API_V1_STR)
app.include_router(audit_router.router, prefix=settings.API_V1_STR)
app.include_router(stats_router.router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Ticket triage API operational"}