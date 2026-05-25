"""Lógica de negocio para Companies."""

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.company import Company
from app.schemas.company import CompanyPipelineUpdate

_VALID_STAGES = {"prospecto", "contactado", "demo", "negociación", "cerrado", "descartado"}


async def list_companies(
    session: AsyncSession,
    run_id: Optional[uuid.UUID] = None,
    sector: Optional[str] = None,
    clasificacion: Optional[str] = None,
    pipeline_stage: Optional[str] = None,
    score_min: Optional[float] = None,
    score_max: Optional[float] = None,
    incluir_en_pipeline: Optional[bool] = None,
    offset: int = 0,
    limit: int = 100,
) -> tuple[list[Company], int]:
    q = select(Company)
    if run_id:
        q = q.where(Company.run_id == run_id)
    if sector:
        q = q.where(Company.sector == sector)
    if clasificacion:
        q = q.where(Company.clasificacion == clasificacion)
    if pipeline_stage:
        q = q.where(Company.pipeline_stage == pipeline_stage)
    if score_min is not None:
        q = q.where(Company.score >= score_min)
    if score_max is not None:
        q = q.where(Company.score <= score_max)
    if incluir_en_pipeline is not None:
        q = q.where(Company.incluir_en_pipeline == incluir_en_pipeline)

    count_q = select(func.count()).select_from(q.subquery())
    count_result = await session.execute(count_q)
    total = count_result.scalar_one()

    q = q.order_by(Company.score.desc().nullslast()).offset(offset).limit(limit)
    result = await session.execute(q)
    return list(result.scalars().all()), total


async def get_company(session: AsyncSession, company_id: uuid.UUID) -> Optional[Company]:
    return await session.get(Company, company_id)


async def update_pipeline(
    session: AsyncSession,
    company_id: uuid.UUID,
    data: CompanyPipelineUpdate,
) -> Optional[Company]:
    company = await session.get(Company, company_id)
    if not company:
        return None
    update_data = data.model_dump(exclude_none=True)
    for key, val in update_data.items():
        setattr(company, key, val)
    company.pipeline_updated_at = datetime.utcnow()
    company.updated_at = datetime.utcnow()
    session.add(company)
    await session.commit()
    await session.refresh(company)
    return company


async def get_kanban_board(session: AsyncSession, run_id: Optional[uuid.UUID] = None) -> dict:
    """Devuelve empresas agrupadas por pipeline_stage para kanban."""
    q = select(Company).where(Company.incluir_en_pipeline == True)
    if run_id:
        q = q.where(Company.run_id == run_id)
    q = q.order_by(Company.score.desc().nullslast())
    result = await session.execute(q)
    companies = result.scalars().all()

    board: dict[str, list[Company]] = {stage: [] for stage in _VALID_STAGES}
    for c in companies:
        stage = c.pipeline_stage if c.pipeline_stage in _VALID_STAGES else "prospecto"
        board[stage].append(c)
    return board
