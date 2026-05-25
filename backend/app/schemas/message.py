import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MessageRead(BaseModel):
    id: uuid.UUID
    contact_id: uuid.UUID
    company_id: uuid.UUID
    run_id: uuid.UUID
    created_at: datetime
    canal: str
    asunto: Optional[str]
    mensaje: str
    estado_envio: str
    enviado_at: Optional[datetime]
    notas_envio: Optional[str]

    model_config = {"from_attributes": True}


class MessageList(BaseModel):
    items: list[MessageRead]
    total: int


class MessageStatusUpdate(BaseModel):
    estado_envio: str
    notas_envio: Optional[str] = None
