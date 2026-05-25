"""Lógica de negocio para Messages."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.message import Message
from app.schemas.message import MessageStatusUpdate

_VALID_ESTADOS = {"pendiente", "enviado", "respondió", "rebotó", "descartado"}


async def list_messages(
    session: AsyncSession,
    run_id: Optional[uuid.UUID] = None,
    company_id: Optional[uuid.UUID] = None,
    contact_id: Optional[uuid.UUID] = None,
    canal: Optional[str] = None,
    estado_envio: Optional[str] = None,
    offset: int = 0,
    limit: int = 200,
) -> tuple[list[Message], int]:
    q = select(Message)
    if run_id:
        q = q.where(Message.run_id == run_id)
    if company_id:
        q = q.where(Message.company_id == company_id)
    if contact_id:
        q = q.where(Message.contact_id == contact_id)
    if canal:
        q = q.where(Message.canal == canal)
    if estado_envio:
        q = q.where(Message.estado_envio == estado_envio)

    count_q = select(func.count()).select_from(q.subquery())
    count_result = await session.execute(count_q)
    total = count_result.scalar_one()

    q = q.order_by(Message.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(q)
    return list(result.scalars().all()), total


async def update_message_status(
    session: AsyncSession,
    message_id: uuid.UUID,
    data: MessageStatusUpdate,
) -> Optional[Message]:
    message = await session.get(Message, message_id)
    if not message:
        return None
    message.estado_envio = data.estado_envio
    if data.notas_envio is not None:
        message.notas_envio = data.notas_envio
    if data.estado_envio == "enviado" and not message.enviado_at:
        message.enviado_at = datetime.utcnow()
    message.updated_at = datetime.utcnow()
    session.add(message)
    await session.commit()
    await session.refresh(message)
    return message
