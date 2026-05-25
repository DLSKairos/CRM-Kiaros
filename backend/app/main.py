from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import select, func

from app.database import async_engine, get_session
import app.models  # noqa: F401 — registra todos los modelos en SQLModel.metadata

from app.routers import runs, companies, contacts, messages, pipeline, blacklist, sse


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await async_engine.dispose()


app = FastAPI(
    title="SEÑAL Prospección API",
    version="0.2.0",
    description="Pipeline de prospección B2B para SEÑAL — Kairos DLS Group",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(runs.router)
app.include_router(sse.router)
app.include_router(companies.router)
app.include_router(contacts.router)
app.include_router(messages.router)
app.include_router(pipeline.router)
app.include_router(blacklist.router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "senal-prospeccion-api", "version": "0.2.0"}


@app.get("/stats")
async def stats():
    """Métricas globales para el dashboard."""
    from app.models.run import Run
    from app.models.company import Company
    from app.models.contact import Contact
    from app.models.message import Message
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        total_runs = (await session.execute(select(func.count()).select_from(Run))).scalar_one()
        completed_runs = (await session.execute(
            select(func.count()).select_from(Run).where(Run.status == "completed")
        )).scalar_one()
        total_companies = (await session.execute(select(func.count()).select_from(Company))).scalar_one()
        calientes = (await session.execute(
            select(func.count()).select_from(Company).where(Company.clasificacion == "caliente")
        )).scalar_one()
        tibios = (await session.execute(
            select(func.count()).select_from(Company).where(Company.clasificacion == "tibio")
        )).scalar_one()
        total_contacts = (await session.execute(select(func.count()).select_from(Contact))).scalar_one()
        contacts_with_email = (await session.execute(
            select(func.count()).select_from(Contact).where(Contact.email.is_not(None))
        )).scalar_one()
        total_messages = (await session.execute(select(func.count()).select_from(Message))).scalar_one()
        messages_sent = (await session.execute(
            select(func.count()).select_from(Message).where(Message.estado_envio == "enviado")
        )).scalar_one()

    return {
        "runs": {"total": total_runs, "completed": completed_runs},
        "companies": {"total": total_companies, "calientes": calientes, "tibios": tibios},
        "contacts": {"total": total_contacts, "with_email": contacts_with_email},
        "messages": {"total": total_messages, "sent": messages_sent},
    }
