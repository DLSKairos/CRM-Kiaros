"""Endpoints para Contacts."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.contact import ContactList
from app.services import contact_service

router = APIRouter(prefix="/contacts", tags=["contacts"])


@router.get("", response_model=ContactList)
async def list_contacts(
    company_id: Optional[uuid.UUID] = Query(None),
    run_id: Optional[uuid.UUID] = Query(None),
    cargo_prioridad: Optional[int] = Query(None, ge=1, le=5),
    has_email: Optional[bool] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(200, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    contacts, total = await contact_service.list_contacts(
        session,
        company_id=company_id,
        run_id=run_id,
        cargo_prioridad=cargo_prioridad,
        has_email=has_email,
        offset=offset,
        limit=limit,
    )
    return ContactList(items=contacts, total=total)
