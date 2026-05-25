"""Endpoints para el Kanban de Pipeline CRM."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.company import CompanyRead
from app.services import company_service

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/kanban")
async def get_kanban(
    run_id: Optional[uuid.UUID] = Query(None, description="Filtrar por run específico"),
    session: AsyncSession = Depends(get_session),
):
    """
    Devuelve empresas agrupadas por etapa de pipeline para el kanban.
    Respuesta: { "prospecto": [...], "contactado": [...], ... }
    """
    board = await company_service.get_kanban_board(session, run_id=run_id)
    return {
        stage: [CompanyRead.model_validate(c) for c in companies]
        for stage, companies in board.items()
    }
