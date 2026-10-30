from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.models.funcionario import FuncionarioRole


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: FuncionarioRole


class RefreshRequest(BaseModel):
    refresh_token: str


class FuncionarioOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    username: str
    full_name: str | None
    role: FuncionarioRole
    area_id: UUID | None
    is_active: bool


class FuncionarioCreate(BaseModel):
    username: str
    password: str
    full_name: str | None = None
    role: FuncionarioRole = FuncionarioRole.ANALISTA
    area_id: UUID | None = None
