from fastapi import APIRouter, status

router = APIRouter(prefix="/health", tags=["Health"])


@router.get("", status_code=status.HTTP_200_OK)
def health_check():
    return {
        "status": "online",
        "service": "Ticket Triage Backend",
        "version": "0.1.0",
    }