from pydantic import BaseModel, ConfigDict, Field
from uuid import UUID


class AreaCreate(BaseModel):
    code: str = Field(min_length=2, max_length=50)
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None
    manager_email: str | None = None
    is_active: bool = True


class AreaUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    manager_email: str | None = None
    is_active: bool | None = None


class AreaOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    code: str
    name: str
    description: str | None
    manager_email: str | None
    is_active: bool
    is_default: bool