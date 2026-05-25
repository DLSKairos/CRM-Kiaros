"""Endpoints para Runs — crear, listar, cancelar, obtener logs y descargar Excel."""

import os
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.schemas.run import RunCreate, RunList, RunLogRead, RunRead
from app.services import run_service
from app.tasks.pipeline import run_prospecting_pipeline

router = APIRouter(prefix="/runs", tags=["runs"])


@router.post("", response_model=RunRead, status_code=201)
async def create_run(data: RunCreate, session: AsyncSession = Depends(get_session)):
    """Crea un nuevo run y encola el pipeline en Celery."""
    run = await run_service.create_run(session, data)
    # Encolar tarea Celery
    task = run_prospecting_pipeline.delay(str(run.id))
    run.celery_task_id = task.id
    session.add(run)
    await session.commit()
    await session.refresh(run)
    return run


@router.get("", response_model=RunList)
async def list_runs(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    session: AsyncSession = Depends(get_session),
):
    runs, total = await run_service.list_runs(session, offset=offset, limit=limit)
    return RunList(items=runs, total=total)


@router.get("/{run_id}", response_model=RunRead)
async def get_run(run_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    run = await run_service.get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run no encontrado")
    return run


@router.delete("/{run_id}", response_model=RunRead)
async def cancel_run(run_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    """Cancela un run en curso (cambia status a 'cancelled')."""
    run = await run_service.cancel_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run no encontrado")
    return run


@router.get("/{run_id}/logs", response_model=list[RunLogRead])
async def get_run_logs(
    run_id: uuid.UUID,
    step: Optional[str] = Query(None),
    level: Optional[str] = Query(None),
    session: AsyncSession = Depends(get_session),
):
    run = await run_service.get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run no encontrado")
    logs = await run_service.get_run_logs(session, run_id, step=step, level=level)
    return logs


@router.get("/{run_id}/excel")
async def download_excel(run_id: uuid.UUID, session: AsyncSession = Depends(get_session)):
    """Descarga el archivo Excel generado para este run."""
    run = await run_service.get_run(session, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run no encontrado")
    if not run.excel_path or not os.path.exists(run.excel_path):
        raise HTTPException(status_code=404, detail="Excel no disponible aún")
    filename = os.path.basename(run.excel_path)
    return FileResponse(
        path=run.excel_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
