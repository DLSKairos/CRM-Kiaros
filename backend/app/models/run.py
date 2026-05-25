import uuid
from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Run(SQLModel, table=True):
    __tablename__ = "runs"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = Field(default=None)
    finished_at: Optional[datetime] = Field(default=None)

    # Parámetros de entrada
    sector: str
    ciudad: str = Field(default="Bogotá D.C.")
    cantidad_target: int = Field(default=20)
    tamano_min: Optional[int] = Field(default=None)
    tamano_max: Optional[int] = Field(default=None)

    # Estado del pipeline
    status: str = Field(default="pending")
    current_step: Optional[str] = Field(default=None)
    progress_pct: int = Field(default=0)
    error_message: Optional[str] = Field(default=None)

    # Resultados
    total_found: int = Field(default=0)
    total_scored: int = Field(default=0)
    total_calientes: int = Field(default=0)
    total_tibios: int = Field(default=0)
    total_frios: int = Field(default=0)
    total_descartados: int = Field(default=0)
    excel_path: Optional[str] = Field(default=None)
    celery_task_id: Optional[str] = Field(default=None)
