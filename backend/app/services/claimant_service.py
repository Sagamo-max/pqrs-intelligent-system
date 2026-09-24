from sqlalchemy.orm import Session
from app.models.claimant import Claimant
from app.schemas.ticket import ClaimantCreate

def get_or_create_claimant(db: Session, claimant_data: ClaimantCreate) -> Claimant:
    claimant = db.query(Claimant).filter(
        Claimant.document_number == claimant_data.document_number
    ).first()

    if not claimant:
        claimant = Claimant(
            first_name=claimant_data.full_name,
            last_name="",
            document_type=claimant_data.document_type,
            document_number=claimant_data.document_number,
            email=claimant_data.email,
            phone=claimant_data.phone
        )
        db.add(claimant)
        db.commit()
        db.refresh(claimant)

    return claimant