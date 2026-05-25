import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Message(SQLModel, table=True):
    __tablename__ = "messages"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    contact_id: uuid.UUID = Field(foreign_key="contacts.id", index=True)
    company_id: uuid.UUID = Field(foreign_key="companies.id", index=True)
    run_id: uuid.UUID = Field(foreign_key="runs.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    canal: str  # email / linkedin / whatsapp
    asunto: Optional[str] = Field(default=None)  # solo para email
    mensaje: str
    estado_envio: str = Field(default="pendiente", index=True)
    enviado_at: Optional[datetime] = Field(default=None)
    notas_envio: Optional[str] = Field(default=None)
