"""
Pipeline principal de prospección — Celery task.

Orquesta secuencialmente: researcher → enricher → scorer → message_writer → crm_exporter
Persiste checkpoints en DB y publica eventos Redis pub/sub para SSE.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

import redis

from app.agents.crm_exporter import CRMExporter
from app.agents.enricher import LeadEnricher
from app.agents.message_writer import MessageWriter
from app.agents.researcher import LeadResearcher
from app.agents.scorer import LeadScorer
from app.config import settings
from app.database import SyncSessionLocal
from app.models.company import Company
from app.models.contact import Contact
from app.models.message import Message
from app.models.run import Run
from app.models.run_log import RunLog
from app.tasks.celery_app import celery_app

_redis = redis.from_url(settings.redis_url, decode_responses=True)


def _publish(run_id: str, event: str, data: dict) -> None:
    """Publica un evento SSE en el canal Redis del run."""
    payload = json.dumps({"event": event, "data": data})
    _redis.publish(f"run:{run_id}", payload)


def _log(session, run_id: uuid.UUID, step: str, level: str, message: str, payload=None) -> None:
    log = RunLog(run_id=run_id, step=step, level=level, message=message, payload=payload)
    session.add(log)
    session.commit()


def _update_run(session, run: Run, **kwargs) -> None:
    for key, val in kwargs.items():
        setattr(run, key, val)
    run.updated_at = datetime.utcnow()
    session.add(run)
    session.commit()


def _is_cancelled(session, run_uuid: uuid.UUID) -> bool:
    """Verifica si el run fue cancelado desde la DB (lectura fresca, no cacheada)."""
    session.expire_all()
    run = session.get(Run, run_uuid)
    return run is not None and run.status == "cancelled"


# ── Persistencia de datos de agentes en DB ─────────────────────────────────────

def _save_companies(session, run_id: uuid.UUID, empresas: list[dict], enriched_map: dict) -> dict[str, uuid.UUID]:
    """Persiste empresas en DB. Devuelve mapa external_id → UUID de DB."""
    id_map: dict[str, uuid.UUID] = {}
    for emp in empresas:
        eid = emp.get("id_empresa", "")
        enriched = enriched_map.get(eid, {})
        company = Company(
            run_id=run_id,
            external_id=eid,
            nombre_empresa=emp.get("nombre_empresa") or "",
            nit=emp.get("nit"),
            sector=emp.get("sector") or "",
            subsector=emp.get("subsector"),
            ciudad=emp.get("ciudad") or "",
            web=emp.get("web"),
            linkedin_empresa=emp.get("linkedin_empresa"),
            tamano_estimado=emp.get("tamano_estimado"),
            fuente=emp.get("fuente"),
            url_fuente=emp.get("url_fuente"),
            notas_researcher=emp.get("notas"),
            email_generico_empresa=enriched.get("email_generico_empresa"),
            telefono_empresa=enriched.get("telefono_empresa"),
            contexto_adicional=enriched.get("contexto_adicional"),
            enriched_at=datetime.utcnow() if enriched else None,
        )
        session.add(company)
        session.flush()
        id_map[eid] = company.id
    session.commit()
    return id_map


def _save_scores(session, companies_map: dict[str, uuid.UUID], scores: list[dict]) -> None:
    """Aplica scores a las empresas ya persistidas."""
    for s in scores:
        eid = s.get("id_empresa")
        db_id = companies_map.get(eid)
        if not db_id:
            continue
        company = session.get(Company, db_id)
        if not company:
            continue
        pts = s.get("puntos_por_criterio", {})
        company.score = s.get("score")
        company.clasificacion = s.get("clasificacion")
        company.plan_sugerido = s.get("plan_sugerido")
        company.justificacion_score = s.get("justificacion")
        company.score_sector = pts.get("sector")
        company.score_campo = pts.get("operaciones_campo")
        company.score_tamano = pts.get("tamano")
        company.score_contacto = pts.get("contacto")
        company.score_bonus = pts.get("bonus")
        company.penalizacion_enterprise = s.get("penalizacion_enterprise", False)
        company.incluir_en_pipeline = s.get("incluir_en_pipeline", True)
        company.scored_at = datetime.utcnow()
        company.updated_at = datetime.utcnow()
        session.add(company)
    session.commit()


def _save_contacts(
    session,
    run_id: uuid.UUID,
    companies_map: dict[str, uuid.UUID],
    enriched_companies: list[dict],
) -> dict[str, uuid.UUID]:
    """Persiste contactos. Devuelve mapa external_id_contacto → UUID de DB."""
    contact_map: dict[str, uuid.UUID] = {}
    for emp in enriched_companies:
        eid = emp.get("id_empresa", "")
        company_db_id = companies_map.get(eid)
        if not company_db_id:
            continue
        for c in emp.get("contactos", []):
            cid = c.get("id_contacto", "")
            contact = Contact(
                company_id=company_db_id,
                run_id=run_id,
                external_id=cid,
                nombre=c.get("nombre") or "",
                cargo=c.get("cargo") or "",
                cargo_prioridad=c.get("cargo_prioridad") or 5,
                email=c.get("email"),
                confianza_email=c.get("confianza_email"),
                linkedin=c.get("linkedin"),
                telefono=c.get("telefono"),
                fuente=c.get("fuente"),
            )
            session.add(contact)
            session.flush()
            contact_map[cid] = contact.id
    session.commit()
    return contact_map


def _save_messages(
    session,
    run_id: uuid.UUID,
    companies_map: dict[str, uuid.UUID],
    contact_map: dict[str, uuid.UUID],
    mensajes: list[dict],
) -> None:
    """Persiste mensajes generados."""
    for m in mensajes:
        cid_ext = m.get("id_contacto", "")
        eid_ext = m.get("id_empresa", "")
        contact_db_id = contact_map.get(cid_ext)
        company_db_id = companies_map.get(eid_ext)
        if not contact_db_id or not company_db_id:
            continue
        canales = m.get("mensajes", {})
        for canal_key, canal_data in canales.items():
            if canal_key == "email":
                msg = Message(
                    contact_id=contact_db_id,
                    company_id=company_db_id,
                    run_id=run_id,
                    canal="email",
                    asunto=canal_data.get("asunto"),
                    mensaje=canal_data.get("cuerpo", ""),
                )
            elif canal_key == "linkedin":
                msg = Message(
                    contact_id=contact_db_id,
                    company_id=company_db_id,
                    run_id=run_id,
                    canal="linkedin",
                    mensaje=canal_data.get("mensaje", ""),
                )
            elif canal_key == "whatsapp":
                msg = Message(
                    contact_id=contact_db_id,
                    company_id=company_db_id,
                    run_id=run_id,
                    canal="whatsapp",
                    mensaje=canal_data.get("mensaje", ""),
                )
            else:
                continue
            session.add(msg)
    session.commit()


# ── Task principal ─────────────────────────────────────────────────────────────

@celery_app.task(bind=True, name="tasks.run_pipeline")
def run_prospecting_pipeline(self, run_id: str) -> dict:
    """
    Pipeline completo de prospección para un Run.
    Steps: researcher (20%) → enricher (40%) → scorer (60%) → message_writer (80%) → crm_exporter (100%)
    """
    run_uuid = uuid.UUID(run_id)
    session = SyncSessionLocal()

    try:
        run = session.get(Run, run_uuid)
        if not run:
            return {"error": f"Run {run_id} no encontrado"}

        # Marcar como running
        _update_run(session, run, status="running", started_at=datetime.utcnow(), current_step="researcher", progress_pct=5)
        _publish(run_id, "step_start", {"step": "researcher", "progress": 5, "message": "Buscando empresas en fuentes web..."})

        # ── STEP 1: Researcher ─────────────────────────────────────────────────
        _log(session, run_uuid, "researcher", "info", f"Iniciando búsqueda: {run.sector} en {run.ciudad}")
        if _is_cancelled(session, run_uuid):
            _log(session, run_uuid, "pipeline", "info", "Run cancelado por el usuario")
            _publish(run_id, "cancelled", {"message": "Run cancelado por el usuario"})
            return {"status": "cancelled", "run_id": run_id}
        try:
            researcher = LeadResearcher()
            research_result = researcher.research(
                sector=run.sector,
                ciudad=run.ciudad,
                cantidad_objetivo=run.cantidad_target,
            )
            empresas_raw = research_result.get("empresas", [])
        except Exception as exc:
            _log(session, run_uuid, "researcher", "error", str(exc))
            _update_run(session, run, status="failed", error_message=f"Researcher falló: {exc}", finished_at=datetime.utcnow())
            _publish(run_id, "failed", {"step": "researcher", "error": str(exc)})
            return {"error": str(exc)}

        _update_run(session, run, current_step="researcher_done", progress_pct=20, total_found=len(empresas_raw))
        _publish(run_id, "step_done", {"step": "researcher", "progress": 20, "found": len(empresas_raw), "message": f"Encontradas {len(empresas_raw)} empresas"})
        _log(session, run_uuid, "researcher", "info", f"Encontradas {len(empresas_raw)} empresas", {"total": len(empresas_raw)})

        # ── STEP 2: Enricher ───────────────────────────────────────────────────
        _update_run(session, run, current_step="enricher", progress_pct=25)
        _publish(run_id, "step_start", {"step": "enricher", "progress": 25, "message": "Buscando contactos y contexto..."})
        _log(session, run_uuid, "enricher", "info", "Iniciando enriquecimiento")

        if _is_cancelled(session, run_uuid):
            _log(session, run_uuid, "pipeline", "info", "Run cancelado por el usuario")
            _publish(run_id, "cancelled", {"message": "Run cancelado por el usuario"})
            return {"status": "cancelled", "run_id": run_id}
        try:
            enricher = LeadEnricher()
            enrich_result = enricher.enrich(empresas_raw)
            empresas_enriquecidas = enrich_result.get("empresas_enriquecidas", [])
        except Exception as exc:
            _log(session, run_uuid, "enricher", "error", str(exc))
            _update_run(session, run, status="failed", error_message=f"Enricher falló: {exc}", finished_at=datetime.utcnow())
            _publish(run_id, "failed", {"step": "enricher", "error": str(exc)})
            return {"error": str(exc)}

        # Construir mapa enriquecido por id_empresa
        enriched_map: dict[str, dict] = {}
        for emp_e in empresas_enriquecidas:
            eid = emp_e.get("id_empresa", "")
            enriched_map[eid] = emp_e

        # Merge: añadir contactos y contexto a empresas_raw
        for emp in empresas_raw:
            eid = emp.get("id_empresa", "")
            if eid in enriched_map:
                e = enriched_map[eid]
                emp["contactos"] = e.get("contactos", [])
                emp["email_generico_empresa"] = e.get("email_generico_empresa")
                emp["telefono_empresa"] = e.get("telefono_empresa")
                emp["contexto_adicional"] = e.get("contexto_adicional")

        total_contacts = sum(len(emp.get("contactos", [])) for emp in empresas_raw)
        _update_run(session, run, current_step="enricher_done", progress_pct=40)
        _publish(run_id, "step_done", {"step": "enricher", "progress": 40, "contacts_found": total_contacts, "message": f"Enriquecidas {len(empresas_enriquecidas)} empresas, {total_contacts} contactos"})
        _log(session, run_uuid, "enricher", "info", f"{total_contacts} contactos encontrados")

        # ── STEP 3: Scorer ─────────────────────────────────────────────────────
        _update_run(session, run, current_step="scorer", progress_pct=45)
        _publish(run_id, "step_start", {"step": "scorer", "progress": 45, "message": "Calificando leads..."})
        _log(session, run_uuid, "scorer", "info", "Iniciando scoring")

        if _is_cancelled(session, run_uuid):
            _log(session, run_uuid, "pipeline", "info", "Run cancelado por el usuario")
            _publish(run_id, "cancelled", {"message": "Run cancelado por el usuario"})
            return {"status": "cancelled", "run_id": run_id}
        try:
            scorer = LeadScorer()
            score_result = scorer.score(empresas_raw)
            leads_calificados = score_result.get("leads_calificados", [])
        except Exception as exc:
            _log(session, run_uuid, "scorer", "error", str(exc))
            _update_run(session, run, status="failed", error_message=f"Scorer falló: {exc}", finished_at=datetime.utcnow())
            _publish(run_id, "failed", {"step": "scorer", "error": str(exc)})
            return {"error": str(exc)}

        resumen_scorer = score_result.get("resumen", {})
        total_calientes = resumen_scorer.get("calientes", 0)
        total_tibios = resumen_scorer.get("tibios", 0)
        total_frios = resumen_scorer.get("frios", 0)
        total_descartados = resumen_scorer.get("descartados", 0)
        total_scored = len(leads_calificados)

        # Filtrar para message_writer solo leads con incluir_en_pipeline=True
        leads_para_mensajes = [
            lead for lead in leads_calificados if lead.get("incluir_en_pipeline", True)
        ]

        _update_run(
            session, run,
            current_step="scorer_done", progress_pct=60,
            total_scored=total_scored,
            total_calientes=total_calientes,
            total_tibios=total_tibios,
            total_frios=total_frios,
            total_descartados=total_descartados,
        )
        _publish(run_id, "step_done", {
            "step": "scorer", "progress": 60,
            "calientes": total_calientes, "tibios": total_tibios, "frios": total_frios,
            "message": f"{total_calientes} calientes, {total_tibios} tibios, {total_frios} fríos"
        })
        _log(session, run_uuid, "scorer", "info", f"Scoring: {total_calientes}C/{total_tibios}T/{total_frios}F/{total_descartados}D")

        # ── Persistir en DB (empresas + contactos + scores) ────────────────────
        companies_map = _save_companies(session, run_uuid, empresas_raw, enriched_map)
        _save_scores(session, companies_map, leads_calificados)
        contact_map = _save_contacts(session, run_uuid, companies_map, empresas_raw)

        # ── STEP 4: MessageWriter ──────────────────────────────────────────────
        _update_run(session, run, current_step="message_writer", progress_pct=65)
        _publish(run_id, "step_start", {"step": "message_writer", "progress": 65, "message": "Generando mensajes personalizados..."})
        _log(session, run_uuid, "message_writer", "info", f"Generando mensajes para {len(leads_para_mensajes)} leads")

        # Construir payload para message_writer: scores + empresas_raw enriquecidas
        scores_map = {s["id_empresa"]: s for s in leads_calificados}
        leads_con_contexto = []
        for emp in empresas_raw:
            eid = emp.get("id_empresa", "")
            score_info = scores_map.get(eid, {})
            if not score_info.get("incluir_en_pipeline", True):
                continue
            leads_con_contexto.append({**emp, **score_info})

        mensajes_list: list[dict] = []
        if leads_con_contexto:
            if _is_cancelled(session, run_uuid):
                _log(session, run_uuid, "pipeline", "info", "Run cancelado por el usuario")
                _publish(run_id, "cancelled", {"message": "Run cancelado por el usuario"})
                return {"status": "cancelled", "run_id": run_id}
            try:
                writer = MessageWriter()
                write_result = writer.write(leads_con_contexto)
                mensajes_list = write_result.get("mensajes", [])
            except Exception as exc:
                _log(session, run_uuid, "message_writer", "error", str(exc))
                _update_run(session, run, status="failed", error_message=f"MessageWriter falló: {exc}", finished_at=datetime.utcnow())
                _publish(run_id, "failed", {"step": "message_writer", "error": str(exc)})
                return {"error": str(exc)}

        _save_messages(session, run_uuid, companies_map, contact_map, mensajes_list)

        _update_run(session, run, current_step="message_writer_done", progress_pct=80)
        _publish(run_id, "step_done", {"step": "message_writer", "progress": 80, "messages": len(mensajes_list), "message": f"{len(mensajes_list)} mensajes generados"})
        _log(session, run_uuid, "message_writer", "info", f"{len(mensajes_list)} mensajes generados")

        # ── STEP 5: CRM Exporter ───────────────────────────────────────────────
        _update_run(session, run, current_step="crm_exporter", progress_pct=85)
        _publish(run_id, "step_start", {"step": "crm_exporter", "progress": 85, "message": "Generando Excel..."})
        _log(session, run_uuid, "crm_exporter", "info", "Generando Excel")

        if _is_cancelled(session, run_uuid):
            _log(session, run_uuid, "pipeline", "info", "Run cancelado por el usuario")
            _publish(run_id, "cancelled", {"message": "Run cancelado por el usuario"})
            return {"status": "cancelled", "run_id": run_id}
        try:
            exporter = CRMExporter(output_dir=settings.output_dir)
            excel_path = exporter.export(
                companies=empresas_raw,
                scores=leads_calificados,
                messages=mensajes_list,
            )
        except Exception as exc:
            _log(session, run_uuid, "crm_exporter", "error", str(exc))
            _update_run(session, run, status="failed", error_message=f"CRMExporter falló: {exc}", finished_at=datetime.utcnow())
            _publish(run_id, "failed", {"step": "crm_exporter", "error": str(exc)})
            return {"error": str(exc)}

        # ── Finalizar ──────────────────────────────────────────────────────────
        _update_run(
            session, run,
            status="completed",
            current_step="done",
            progress_pct=100,
            excel_path=excel_path,
            finished_at=datetime.utcnow(),
        )
        _publish(run_id, "completed", {
            "progress": 100,
            "excel_path": excel_path,
            "total_found": len(empresas_raw),
            "calientes": total_calientes,
            "tibios": total_tibios,
            "frios": total_frios,
            "message": "Pipeline completado exitosamente",
        })
        _log(session, run_uuid, "crm_exporter", "info", f"Excel generado: {excel_path}")

        # Notificaciones async (fire-and-forget)
        try:
            from app.utils.notifications import notify_run_completed
            notify_run_completed(
                run_id=run_id,
                sector=run.sector,
                ciudad=run.ciudad,
                calientes=total_calientes,
                tibios=total_tibios,
                frios=total_frios,
                excel_path=excel_path,
            )
        except Exception:
            pass

        return {
            "run_id": run_id,
            "status": "completed",
            "total_found": len(empresas_raw),
            "calientes": total_calientes,
            "tibios": total_tibios,
            "frios": total_frios,
            "excel_path": excel_path,
        }

    except Exception as exc:
        try:
            run = session.get(Run, run_uuid)
            if run:
                _update_run(session, run, status="failed", error_message=str(exc), finished_at=datetime.utcnow())
            _publish(run_id, "failed", {"error": str(exc)})
        except Exception:
            pass
        raise
    finally:
        session.close()
