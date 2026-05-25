"""Endpoints para Messages — listar y actualizar estado de envío."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.message import MessageList, MessageRead, MessageStatusUpdate
from app.services import message_service

router = APIRouter(prefix="/messages", tags=["messages"])


@router.get("", response_model=MessageList)
async def list_messages(
    run_id: Optional[uuid.UUID] = Query(None),
    company_id: Optional[uuid.UUID] = Query(None),
    contact_id: Optional[uuid.UUID] = Query(None),
    canal: Optional[str] = Query(None, description="email | linkedin | whatsapp"),
    estado_envio: Optional[str] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    messages, total = await message_service.list_messages(
        session,
        run_id=run_id,
        company_id=company_id,
        contact_id=contact_id,
        canal=canal,
        estado_envio=estado_envio,
        offset=offset,
        limit=limit,
    )
    return MessageList(items=messages, total=total)


@router.patch("/{message_id}/status", response_model=MessageRead)
async def update_message_status(
    message_id: uuid.UUID,
    data: MessageStatusUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Actualiza el estado de envío de un mensaje (enviado, respondió, etc.)."""
    message = await message_service.update_message_status(session, message_id, data)
    if not message:
        raise HTTPException(status_code=404, detail="Mensaje no encontrado")
    return message
