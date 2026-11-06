from uuid import UUID

from pydantic import BaseModel, ConfigDict


class OrganizacionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    is_active: bool
