import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ContactRead(BaseModel):
    id: uuid.UUID
    company_id: uuid.UUID
    run_id: uuid.UUID
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
