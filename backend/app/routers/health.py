from fastapi import APIRouter, status

# APIRouter agrupa endpoints por dominio o funcionalidad
router = APIRouter(tags=["Health"])

@router.get("/", status_code=status.HTTP_200_OK)
def root():
    return {
        "status": "online",
        "service": "PQRS Triage Backend",
        "version": "0.1.0"
    }