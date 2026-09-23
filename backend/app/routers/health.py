from fastapi import APIRouter, status


router = APIRouter(tags=["Health"])

@router.get("/", status_code=status.HTTP_200_OK)
def root():
    return {
        "status": "online",
        "service": "Ticket Triage Backend",
        "version": "0.1.0"
    }