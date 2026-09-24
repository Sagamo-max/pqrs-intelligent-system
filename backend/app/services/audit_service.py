from sqlalchemy.orm import Session
from app.models.audit import AIAudit
from app.core.config import settings

def create_ai_audit(
    db: Session, 
    ticket_id: str, 
    classification_data: dict,
    original_text: str,
    sanitized_text: str
) -> AIAudit:
    
    audit = AIAudit(
        ticket_id=ticket_id,
        ai_model=settings.AI_MODEL_NAME,
        provider=settings.AI_PROVIDER,
        original_text=original_text,
        sanitized_text=sanitized_text,
        decision_justification=classification_data.get("decision_justification", ""),
        suggested_type=classification_data.get("ticket_type"),
        suggested_priority=classification_data.get("priority"),
        suggested_department_code=classification_data.get("responsible_area", "DEFAULT")
    )
    
    db.add(audit)
    db.commit()
    db.refresh(audit)
    return audit