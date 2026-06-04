import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ContactCreate(BaseModel):
    company_id: uuid.UUID
    nombre: str
    cargo: str
    cargo_prioridad: int = 3
    email: Optional[str] = None
    linkedin: Optional[str] = None
    telefono: Optional[str] = None


class ContactRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    run_id: Optional[uuid.UUID]
    external_id: str
    created_at: datetime
    nombre: str
    cargo: str
    cargo_prioridad: int
    email: Optional[str]
    confianza_email: Optional[str]
    linkedin: Optional[str]
    telefono: Optional[str]
    fuente: Optional[str]
    accion_sugerida: Optional[str]

    model_config = {"from_attributes": True}


class ContactList(BaseModel):
    items: list[ContactRead]
    total: int
