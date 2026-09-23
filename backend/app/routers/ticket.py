from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.services.classifier import classify_ticket_text
from app.schemas.classification import TicketClassification
from app.schemas.ticket import TicketCreate, TicketResponse
from app.services.ticket_service import create_ticket
from app.core.database import get_db

router = APIRouter(prefix="/pqrs", tags=["Tickets"])

class TicketClassificationRequest(BaseModel):
    text: str

@router.post("/classify-poc", response_model=TicketClassification)
def classify_ticket(payload: TicketClassificationRequest):
    try:
        return classify_ticket_text(payload.text)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=TicketResponse, status_code=201)
def submit_ticket(payload: TicketCreate, database: Session = Depends(get_db)):
    try:
        ticket = create_ticket(db=database, ticket_data=payload)
        return TicketResponse(
            ticket_number=ticket.tracking_number,
            status=ticket.status.value,
        )
    except Exception as e:
        database.rollback()
        raise HTTPException(status_code=500, detail=str(e))