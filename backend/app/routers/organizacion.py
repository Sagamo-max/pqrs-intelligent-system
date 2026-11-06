from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.organizacion import Organizacion
from app.schemas.organizacion import OrganizacionOut

router = APIRouter(
    prefix="/api/v1/organizaciones",
    tags=["Organizaciones"],
)


@router.get("/active", response_model=OrganizacionOut)
def get_active_organization(
    slug: str = Query("demo", description="Slug de la organización"),
    db: Session = Depends(get_db),
):
    """Return an active organization by slug for public form initialization."""
    organization = db.scalar(
        select(Organizacion).where(
            Organizacion.slug == slug,
            Organizacion.is_active.is_(True),
        )
    )
    if not organization:
        raise HTTPException(
            status_code=404,
            detail=f"Organización '{slug}' no encontrada o inactiva",
        )
    return organization
