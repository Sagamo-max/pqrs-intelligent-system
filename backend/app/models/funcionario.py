import enum
import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum as SQLEnum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class FuncionarioRole(str, enum.Enum):
    ANALISTA = "ANALISTA"
    SUPERVISOR = "SUPERVISOR"
    MASTER = "MASTER"


ROLE_LEVEL = {
    FuncionarioRole.ANALISTA: 1,
    FuncionarioRole.SUPERVISOR: 2,
    FuncionarioRole.MASTER: 3,
}


def role_at_least(role: FuncionarioRole, minimum: FuncionarioRole) -> bool:
    return ROLE_LEVEL[role] >= ROLE_LEVEL[minimum]


class Funcionario(Base):
    __tablename__ = "funcionarios"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=True)
    role = Column(
        SQLEnum(FuncionarioRole, name="funcionario_role_enum"),
        nullable=False,
        default=FuncionarioRole.ANALISTA,
    )
    area_id = Column(
        UUID(as_uuid=True),
        ForeignKey("areas.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    area = relationship("Area")
