"""Lógica de negocio para Runs."""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.run import Run
from app.models.run_log import RunLog
from app.schemas.run import RunCreate


async def create_run(session: AsyncSession, data: RunCreate) -> Run:
    run = Run(
        sector=data.sector,
        ciudad=data.ciudad,
        cantidad_target=data.cantidad_target,
        tamano_min=data.tamano_min,
        tamano_max=data.tamano_max,
    )
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def get_run(session: AsyncSession, run_id: uuid.UUID) -> Optional[Run]:
    return await session.get(Run, run_id)


async def list_runs(session: AsyncSession, offset: int = 0, limit: int = 50) -> tuple[list[Run], int]:
    result = await session.execute(
        select(Run).order_by(Run.created_at.desc()).offset(offset).limit(limit)
    )
    runs = result.scalars().all()
    count_result = await session.execute(select(func.count()).select_from(Run))
    total = count_result.scalar_one()
    return list(runs), total


async def cancel_run(session: AsyncSession, run_id: uuid.UUID) -> Optional[Run]:
    from datetime import datetime
    run = await session.get(Run, run_id)
    if not run:
        return None
    if run.status in ("completed", "failed", "cancelled"):
        return run
    run.status = "cancelled"
    run.finished_at = datetime.utcnow()
    run.updated_at = datetime.utcnow()
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


async def get_run_logs(
    session: AsyncSession,
    run_id: uuid.UUID,
    step: Optional[str] = None,
    level: Optional[str] = None,
) -> list[RunLog]:
    q = select(RunLog).where(RunLog.run_id == run_id).order_by(RunLog.created_at)
    if step:
        q = q.where(RunLog.step == step)
    if level:
        q = q.where(RunLog.level == level)
    result = await session.execute(q)
    return list(result.scalars().all())
