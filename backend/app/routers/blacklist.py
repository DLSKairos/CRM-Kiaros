"""Endpoints para Blacklist — CRUD de empresas/contactos/dominios excluidos."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.blacklist import BlacklistCreate, BlacklistList, BlacklistRead
from app.services import blacklist_service

router = APIRouter(prefix="/blacklist", tags=["blacklist"])


@router.post("", response_model=BlacklistRead, status_code=201)
async def create_entry(data: BlacklistCreate, session: AsyncSession = Depends(get_session)):
    return await blacklist_service.create_entry(session, data)


@router.get("", response_model=BlacklistList)
async def list_entries(
    tipo: Optional[str] = Query(None, description="empresa | contacto | dominio"),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    entries, total = await blacklist_service.list_entries(session, tipo=tipo, offset=offset, limit=limit)
    return BlacklistList(items=entries, total=total)


@router.delete("/{entry_id}", status_code=204)
async def delete_entry(entry_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    deleted = await blacklist_service.delete_entry(session, entry_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Entrada no encontrada")
