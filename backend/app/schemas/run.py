import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class RunCreate(BaseModel):
    sector: str = Field(..., min_length=2, max_length=100, description="Sector industrial a prospectar")
    ciudad: str = Field(default="Bogotá D.C.", max_length=100)
    cantidad_target: int = Field(default=20, ge=5, le=100, description="Número de empresas a buscar")
    tamano_min: Optional[int] = Field(default=None, ge=10)
    tamano_max: Optional[int] = Field(default=None, le=10000)


class RunRead(BaseModel):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime]
    finished_at: Optional[datetime]
    sector: str
    ciudad: str
    cantidad_target: int
    tamano_min: Optional[int]
    tamano_max: Optional[int]
    status: str
    current_step: Optional[str]
    progress_pct: int
    error_message: Optional[str]
    total_found: int
    total_scored: int
    total_calientes: int
    total_tibios: int
    total_frios: int
    total_descartados: int
    excel_path: Optional[str]
    celery_task_id: Optional[str]

    model_config = {"from_attributes": True}


class RunList(BaseModel):
    items: list[RunRead]
    total: int


class RunLogRead(BaseModel):
    id: Optional[int]
    run_id: uuid.UUID
    created_at: datetime
    step: str
    level: str
    message: str
    payload: Optional[dict | list]

    model_config = {"from_attributes": True}
