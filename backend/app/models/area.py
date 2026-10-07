import uuid

from sqlalchemy import Boolean, Column, DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Area(Base):
    __tablename__ = "areas"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    manager_email = Column(String(150), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    tickets = relationship("Ticket", back_populates="area")