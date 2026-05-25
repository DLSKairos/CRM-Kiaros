import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, SQLModel


class RunLog(SQLModel, table=True):
    __tablename__ = "run_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    run_id: uuid.UUID = Field(foreign_key="runs.id", index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    step: str  # researcher / enricher / scorer / message_writer / crm_exporter
    level: str  # info / warning / error
    message: str
    payload: Optional[Any] = Field(default=None, sa_column=Column(JSON))
