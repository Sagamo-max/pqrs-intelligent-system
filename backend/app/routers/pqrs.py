from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.classifier import classify_pqrs_text
from app.schemas.classification import PQRSClassification

router = APIRouter(prefix="/pqrs", tags=["PQRS"])

class PQRSRequestPoC(BaseModel):
    texto: str

@router.post("/classify-poc", response_model=PQRSClassification)
def test_classification_poc(request: PQRSRequestPoC):
    try:
        return classify_pqrs_text(request.texto)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))