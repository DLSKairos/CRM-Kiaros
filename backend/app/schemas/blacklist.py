import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class BlacklistCreate(BaseModel):
    tipo: str  # empresa / contacto / dominio
    valor: str
    razon: Optional[str] = None


class BlacklistRead(BaseModel):
    id: uuid.UUID
    created_at: datetime
    tipo: str
    valor: str
    razon: Optional[str]

    model_config = {"from_attributes": True}


class BlacklistList(BaseModel):
    items: list[BlacklistRead]
    total: int
