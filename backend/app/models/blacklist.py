import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Blacklist(SQLModel, table=True):
    __tablename__ = "blacklist"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    tipo: str  # empresa / contacto / dominio
    valor: str = Field(index=True)
    razon: Optional[str] = Field(default=None)
