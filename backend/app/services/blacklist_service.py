"""Lógica de negocio para Blacklist."""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.blacklist import Blacklist
from app.schemas.blacklist import BlacklistCreate


async def create_entry(session: AsyncSession, data: BlacklistCreate) -> Blacklist:
    entry = Blacklist(tipo=data.tipo, valor=data.valor, razon=data.razon)
    session.add(entry)
    await session.commit()
    await session.refresh(entry)
    return entry


async def list_entries(
    session: AsyncSession,
    tipo: Optional[str] = None,
    offset: int = 0,
    limit: int = 100,
) -> tuple[list[Blacklist], int]:
    q = select(Blacklist)
    if tipo:
        q = q.where(Blacklist.tipo == tipo)

    count_q = select(func.count()).select_from(q.subquery())
    count_result = await session.execute(count_q)
    total = count_result.scalar_one()

    q = q.order_by(Blacklist.created_at.desc()).offset(offset).limit(limit)
    result = await session.execute(q)
    return list(result.scalars().all()), total


async def delete_entry(session: AsyncSession, entry_id: uuid.UUID) -> bool:
    entry = await session.get(Blacklist, entry_id)
    if not entry:
        return False
    await session.delete(entry)
    await session.commit()
    return True
