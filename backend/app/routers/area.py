from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth_deps import get_current_user, require_role
from app.core.database import get_db
from app.models.area import Area
from app.models.funcionario import Funcionario, FuncionarioRole
from app.schemas.area import AreaCreate, AreaOut, AreaUpdate

router = APIRouter(
    prefix="/areas",
    tags=["areas"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/", response_model=list[AreaOut])
def list_areas(db: Session = Depends(get_db)):
    return list(db.scalars(select(Area).order_by(Area.name)))


@router.get("/{area_id}", response_model=AreaOut)
def get_area(area_id: str, db: Session = Depends(get_db)):
    area = db.get(Area, area_id)
    if not area:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Área no encontrada")
    return area


@router.post("/", response_model=AreaOut, status_code=status.HTTP_201_CREATED)
def create_area(
    payload: AreaCreate,
    db: Session = Depends(get_db),
    _: Funcionario = Depends(require_role(FuncionarioRole.MASTER)),
):
    if db.scalar(select(Area).where(Area.code == payload.code)):
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe un área con ese code")
    area = Area(**payload.model_dump())
    db.add(area)
    db.commit()
    db.refresh(area)
    return area


@router.patch("/{area_id}", response_model=AreaOut)
def update_area(
    area_id: str,
    payload: AreaUpdate,
    db: Session = Depends(get_db),
    _: Funcionario = Depends(require_role(FuncionarioRole.MASTER)),
):
    area = db.get(Area, area_id)
    if not area:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Área no encontrada")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(area, field, value)
    db.commit()
    db.refresh(area)
    return area