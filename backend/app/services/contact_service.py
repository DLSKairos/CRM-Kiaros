"""Lógica de negocio para Contacts."""

import uuid
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.models.contact import Contact
from app.schemas.contact import ContactCreate


async def create_contact(session: AsyncSession, data: ContactCreate) -> Contact:
    import uuid as _uuid

    contact = Contact(
        external_id=f"M-{_uuid.uuid4().hex[:8].upper()}",
        fuente="manual",
        run_id=None,
        company_id=data.company_id,
        nombre=data.nombre,
        cargo=data.cargo,
        cargo_prioridad=data.cargo_prioridad,
        email=data.email,
        linkedin=data.linkedin,
        telefono=data.telefono,
    )
    session.add(contact)
    await session.commit()
    await session.refresh(contact)
    return contact


async def list_contacts(
    session: AsyncSession,
    company_id: Optional[uuid.UUID] = None,
    run_id: Optional[uuid.UUID] = None,
    cargo_prioridad: Optional[int] = None,
    has_email: Optional[bool] = None,
    offset: int = 0,
    limit: int = 200,
) -> tuple[list[Contact], int]:
    q = select(Contact)
    if company_id:
        q = q.where(Contact.company_id == company_id)
    if run_id:
        q = q.where(Contact.run_id == run_id)
    if cargo_prioridad is not None:
        q = q.where(Contact.cargo_prioridad == cargo_prioridad)
    if has_email is True:
        q = q.where(Contact.email.is_not(None))
    elif has_email is False:
        q = q.where(Contact.email.is_(None))

    count_q = select(func.count()).select_from(q.subquery())
    count_result = await session.execute(count_q)
    total = count_result.scalar_one()

    q = q.order_by(Contact.cargo_prioridad, Contact.nombre).offset(offset).limit(limit)
    result = await session.execute(q)
    return list(result.scalars().all()), total
