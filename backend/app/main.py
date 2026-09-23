from fastapi import FastAPI
from app.core.config import settings
from app.routers import ticket, health

app = FastAPI(title=settings.PROJECT_NAME)

app.include_router(health.router)
app.include_router(ticket.router, prefix=settings.API_V1_STR)

@app.get("/")
def read_root():
    return {"status": "ok", "message": "Ticket triage API operational"}