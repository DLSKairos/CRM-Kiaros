import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class CompanyCreate(BaseModel):
    nombre_empresa: str
    sector: str
    ciudad: str
    nit: Optional[str] = None
    web: Optional[str] = None
    linkedin_empresa: Optional[str] = None
    tamano_estimado: Optional[str] = None
    email_generico_empresa: Optional[str] = None
    telefono_empresa: Optional[str] = None
    contexto_adicional: Optional[str] = None
    pipeline_stage: str = "prospecto"
    responsable_comercial: Optional[str] = None
    notas_comercial: Optional[str] = None
    score: Optional[float] = None


class CompanyRead(BaseModel):
    id: uuid.UUID
    run_id: Optional[uuid.UUID]
    external_id: str
    created_at: datetime
    nombre_empresa: str
    nit: Optional[str]
    sector: str
    subsector: Optional[str]
    ciudad: str
    web: Optional[str]
    linkedin_empresa: Optional[str]
    tamano_estimado: Optional[str]
    fuente: Optional[str]
    email_generico_empresa: Optional[str]
    telefono_empresa: Optional[str]
    contexto_adicional: Optional[str]
    score: Optional[float]
    clasificacion: Optional[str]
    plan_sugerido: Optional[str]
    justificacion_score: Optional[str]
    penalizacion_enterprise: bool
    incluir_en_pipeline: bool
    pipeline_stage: str
    responsable_comercial: Optional[str]
    notas_comercial: Optional[str]
    proxima_accion: Optional[str]
    fecha_primer_contacto: Optional[date]

    model_config = {"from_attributes": True}


class CompanyList(BaseModel):
    items: list[CompanyRead]
    total: int


class CompanyPipelineUpdate(BaseModel):
    pipeline_stage: Optional[str] = None
    responsable_comercial: Optional[str] = None
    notas_comercial: Optional[str] = None
    proxima_accion: Optional[str] = None
    fecha_primer_contacto: Optional[date] = None
