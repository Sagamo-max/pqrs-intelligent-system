from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.services.classifier import classify_ticket_text
from app.schemas.classification import TicketClassification
from app.schemas.ticket import TicketCreate, TicketResponse
from app.services.ticket_service import create_ticket
from app.core.database import get_db
from app.services.claimant_service import get_or_create_claimant

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
def submit_ticket(request: TicketCreate, db: Session = Depends(get_db)):
    try:
        claimant = get_or_create_claimant(db=db, claimant_data=request.claimant)
        
        ticket = create_ticket(
            db=db, 
            free_text=request.free_text, 
            claimant_id=claimant.id
        )
        
        ai_payload = ticket.original_text
        
        print(f"\n--- ISOLATED PAYLOAD FOR AI ---\n{ai_payload}\n-------------------------------\n")
        
        classification = classify_ticket_text(ai_payload)
        
        print(f"AI Classification Result: {classification}")
        
        return TicketResponse(
            ticket_number=ticket.tracking_number,
            status=ticket.status.value if hasattr(ticket.status, 'value') else str(ticket.status)
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))