import uuid
from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Company(SQLModel, table=True):
    __tablename__ = "companies"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    run_id: uuid.UUID = Field(foreign_key="runs.id")
    external_id: str = Field(index=True)  # 'E001' asignado por el agente
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Datos del Researcher
    nombre_empresa: str
    nit: Optional[str] = Field(default=None)
    sector: str = Field(index=True)
    subsector: Optional[str] = Field(default=None)
    ciudad: str
    web: Optional[str] = Field(default=None)
    linkedin_empresa: Optional[str] = Field(default=None)
    tamano_estimado: Optional[str] = Field(default=None)
    tamano_min_num: Optional[int] = Field(default=None)
    tamano_max_num: Optional[int] = Field(default=None)
    fuente: Optional[str] = Field(default=None)
    url_fuente: Optional[str] = Field(default=None)
    notas_researcher: Optional[str] = Field(default=None)

    # Datos del Enricher
    email_generico_empresa: Optional[str] = Field(default=None)
    telefono_empresa: Optional[str] = Field(default=None)
    contexto_adicional: Optional[str] = Field(default=None)
    enriched_at: Optional[datetime] = Field(default=None)

    # Datos del Scorer
    score: Optional[float] = Field(default=None, index=True)
    clasificacion: Optional[str] = Field(default=None, index=True)
    plan_sugerido: Optional[str] = Field(default=None)
    justificacion_score: Optional[str] = Field(default=None)
    score_sector: Optional[float] = Field(default=None)
    score_campo: Optional[float] = Field(default=None)
    score_tamano: Optional[float] = Field(default=None)
    score_contacto: Optional[float] = Field(default=None)
    score_bonus: Optional[float] = Field(default=None)
    penalizacion_enterprise: bool = Field(default=False)
    incluir_en_pipeline: bool = Field(default=True)
    scored_at: Optional[datetime] = Field(default=None)

    # Pipeline / CRM liviano
    pipeline_stage: str = Field(default="prospecto", index=True)
    pipeline_updated_at: Optional[datetime] = Field(default=None)
    responsable_comercial: Optional[str] = Field(default=None)
    notas_comercial: Optional[str] = Field(default=None)
    proxima_accion: Optional[str] = Field(default=None)
    fecha_primer_contacto: Optional[date] = Field(default=None)
