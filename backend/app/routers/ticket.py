import logging

from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.classification import TicketClassification
from app.schemas.ticket import TicketCreate, TicketResponse
from app.services.claimant_service import get_or_create_claimant
from app.services.classifier import classify_ticket_text
from app.services.ticket_service import create_ticket

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/pqrs", tags=["Tickets"])


class TicketClassificationRequest(BaseModel):
    text: str


@router.post("/classify-poc", response_model=TicketClassification)
def classify_ticket(payload: TicketClassificationRequest):
    try:
        return classify_ticket_text(payload.text)
    except Exception as e:
        logger.error(f"Classification failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/", response_model=TicketResponse, status_code=status.HTTP_201_CREATED)
def submit_ticket(request: TicketCreate, db: Session = Depends(get_db)):
    try:
        claimant = get_or_create_claimant(db=db, claimant_data=request.claimant)

        ticket = create_ticket(
            db=db,
            free_text=request.free_text,
            claimant_id=claimant.id,
        )

        return TicketResponse.model_validate(ticket)

    except Exception as e:
        db.rollback()
        logger.exception(f"Failed to create PQRS: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")