"""Endpoints para Companies — listar con filtros y actualizar pipeline CRM."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.company import CompanyCreate, CompanyList, CompanyPipelineUpdate, CompanyRead
from app.services import company_service

router = APIRouter(prefix="/companies", tags=["companies"])


@router.post("", response_model=CompanyRead, status_code=status.HTTP_201_CREATED)
async def create_company(
    data: CompanyCreate,
    session: AsyncSession = Depends(get_session),
):
    """Crea una empresa manualmente, sin pasar por el pipeline de agentes."""
    return await company_service.create_company(session, data)


@router.get("", response_model=CompanyList)
async def list_companies(
    run_id: Optional[uuid.UUID] = Query(None),
    sector: Optional[str] = Query(None),
    clasificacion: Optional[str] = Query(None, description="caliente | tibio | frío"),
    pipeline_stage: Optional[str] = Query(None),
    score_min: Optional[float] = Query(None, ge=0, le=10),
    score_max: Optional[float] = Query(None, ge=0, le=10),
    incluir_en_pipeline: Optional[bool] = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session),
):
    companies, total = await company_service.list_companies(
        session,
        run_id=run_id,
        sector=sector,
        clasificacion=clasificacion,
        pipeline_stage=pipeline_stage,
        score_min=score_min,
        score_max=score_max,
        incluir_en_pipeline=incluir_en_pipeline,
        offset=offset,
        limit=limit,
    )
    return CompanyList(items=companies, total=total)


@router.get("/{company_id}", response_model=CompanyRead)
async def get_company(company_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    company = await company_service.get_company(session, company_id)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return company


@router.delete("/{company_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_company(
    company_id: uuid.UUID,
    session: AsyncSession = Depends(get_session),
):
    """Elimina una empresa y sus datos asociados."""
    deleted = await company_service.delete_company(session, company_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")


@router.patch("/{company_id}/pipeline", response_model=CompanyRead)
async def update_pipeline(
    company_id: uuid.UUID,
    data: CompanyPipelineUpdate,
    session: AsyncSession = Depends(get_session),
):
    """Actualiza la etapa CRM, responsable y notas de una empresa."""
    company = await company_service.update_pipeline(session, company_id, data)
    if not company:
        raise HTTPException(status_code=404, detail="Empresa no encontrada")
    return company
