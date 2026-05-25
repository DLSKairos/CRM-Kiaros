import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Contact(SQLModel, table=True):
    __tablename__ = "contacts"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    company_id: uuid.UUID = Field(foreign_key="companies.id", index=True)
    run_id: uuid.UUID = Field(foreign_key="runs.id", index=True)
    external_id: str  # 'C001' asignado por el agente
    created_at: datetime = Field(default_factory=datetime.utcnow)

    nombre: str
    cargo: str
    cargo_prioridad: int = Field(ge=1, le=5, index=True)
    email: Optional[str] = Field(default=None)
    email_dominio_probable: Optional[str] = Field(default=None)
    confianza_email: Optional[str] = Field(default=None)  # alta / media / baja
    linkedin: Optional[str] = Field(default=None)
    telefono: Optional[str] = Field(default=None)
    fuente: Optional[str] = Field(default=None)
    accion_sugerida: Optional[str] = Field(default=None)
