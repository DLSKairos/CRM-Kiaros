# SEÑAL — Pipeline de Prospección B2B

> "Tu operación en movimiento, siempre"

## 1. Propósito del Proyecto

Construir una pipeline de prospección comercial automatizada para **SEÑAL**, un SaaS colombiano de permisos de trabajo y formularios operacionales de **Kairos DLS Group S.A.S.**

El sistema usa agentes especializados de Claude Code que:
1. Buscan empresas target en fuentes gratuitas (web, directorios colombianos)
2. Enriquecen los datos con contactos y detalles operacionales
3. Califican cada lead con un score de fit
4. Generan mensajes personalizados por canal y cargo
5. Exportan todo a un Excel listo para que el equipo comercial opere

**Output final:** archivo Excel `.xlsx` con 4 pestañas, listo para uso inmediato por comerciales.

---

## 2. ICP — Perfil de Cliente Ideal de SEÑAL

### Producto que se vende
SaaS B2B para digitalizar permisos de trabajo, formularios operacionales, inventarios y cualquier proceso que hoy se hace en papel en actividades de campo.

### Planes
| Plan | Precio | Usuarios |
|------|--------|----------|
| Starter | desde $2.000.000 COP/mes | 0–50 usuarios |
| Growth | intermedio | 51–150 usuarios |
| Enterprise | precio a negociar | +300 usuarios, multisedes |

### Sectores target (en orden de prioridad)
1. **Construcción** — obras civiles, edificaciones, infraestructura
2. **Minería** — carbón, oro, materiales de construcción
3. **Hidrocarburos / Oil & Gas** — exploración, producción, transporte
4. **Manufactura** — plantas industriales con operaciones de campo
5. **Conducción / Transporte** — flotas, logística, última milla
6. **Utilities** — energía, agua, gas, telecomunicaciones
7. **Cualquier sector** con operaciones de campo que aún use papel

### Tamaño mínimo de empresa
- **20+ empleados operativos en campo** (capaces de pagar ≥ $2.000.000 COP/mes)
- Preferible: 50–500 empleados para deals Starter/Growth
- Empresas grandes (500+): deal Enterprise, ciclo de venta más largo

### Geografía inicial
- **Bogotá D.C.** y **Cundinamarca** — prioridad absoluta
- Expansión futura: Medellín, Barranquilla, resto Colombia

### Señales de fit (pain points que resuelve SEÑAL)
- Usan papel, Excel o WhatsApp para permisos de trabajo y checklist
- Tienen obligaciones SST/HSEQ (normativa colombiana: Resolución 0312, Decreto 1072)
- Han tenido accidentes laborales o multas por documentación deficiente
- Operan en múltiples sedes o con personal disperso en campo
- Tienen procesos de auditoría frecuentes (ISO 45001, BASC, RUC)

### Cargos a contactar (por prioridad)
| Prioridad | Cargo | Rol en la compra |
|-----------|-------|-----------------|
| 1 | HSE Manager / Director SST / Coordinador HSEQ | Usuario principal + influenciador |
| 2 | Jefe de Operaciones / Director de Operaciones | Sponsor operacional |
| 3 | Gerente General | Decisor en empresas pequeñas |
| 4 | CTO / Director de Tecnología | Decisor técnico en medianas/grandes |
| 5 | Gerente Administrativo | Aprobador de presupuesto |

### Fuentes de prospección (solo gratuitas)
- **RUES** (rues.confecamaras.co) — registro empresas colombianas
- **Supersociedades** (supersociedades.gov.co) — estados financieros
- **Camacol** — directorio sector construcción
- **Andesco** — directorio utilities
- **ACP** (Asociación Colombiana del Petróleo) — directorio oil & gas
- **LinkedIn** — búsqueda de empresas y contactos
- Web general — sitios corporativos, noticias del sector

---

## 3. Arquitectura de Agentes

```
señal-prospecting-orchestrator
├── señal-lead-researcher
├── señal-lead-enricher
├── señal-lead-scorer
├── señal-message-writer
└── señal-crm-exporter
```

### `señal-prospecting-orchestrator`
**Responsabilidad:** coordinar el flujo completo. Recibe parámetros (sector, ciudad, cantidad de leads) y orquesta los demás agentes en secuencia. Consolida resultados y dispara el exportador al final.

**Inputs:** sector(es) target, geografía, número de leads deseados  
**Output:** estructura de datos consolidada lista para exportar

---

### `señal-lead-researcher`
**Responsabilidad:** buscar empresas target en fuentes gratuitas.

**Acciones:**
- Buscar en RUES, Supersociedades, Camacol, Andesco, ACP via WebSearch/WebFetch
- Buscar en LinkedIn empresas por sector + ubicación
- Deduplicar empresas encontradas por NIT o nombre
- Retornar lista cruda de empresas con datos básicos

**Output por empresa:** nombre, NIT (si disponible), sector, ciudad, web, LinkedIn URL

---

### `señal-lead-enricher`
**Responsabilidad:** enriquecer cada empresa con datos de contacto y contexto operacional.

**Acciones:**
- Visitar el sitio web de la empresa (WebFetch) para extraer emails, teléfonos, nombres de directivos
- Buscar en LinkedIn perfiles de los cargos prioritarios del ICP
- Buscar noticias recientes de la empresa (proyectos, expansión, incidentes SST)
- Estimar tamaño (empleados) desde LinkedIn o fuentes secundarias

**Output por empresa:** contactos con nombre/cargo/email/LinkedIn, contexto relevante

---

### `señal-lead-scorer`
**Responsabilidad:** asignar un score de 1–10 a cada lead según fit con el ICP.

**Criterios de scoring:**
| Criterio | Peso | Descripción |
|----------|------|-------------|
| Sector | 30% | Construcción/minería/O&G = máximo; otros = parcial |
| Operaciones de campo | 25% | Evidencia de obras/plantas/flotas activas |
| Tamaño | 25% | 50–500 empleados campo = máximo; <10 en campo = 0 |
| Contacto encontrado | 20% | HSE/Ops con email = máximo; sin contacto = 0 |
| Bonus | +var | ISO 45001, RUC, BASC, noticias SST, expansión activa |

**Threshold:** score < 3 → descartar; 3–5 → frío; 6–7 → tibio; 8–10 → caliente

---

### `señal-message-writer`
**Responsabilidad:** generar mensajes personalizados por empresa, contacto y canal.

**Canales:** LinkedIn (nota de conexión ≤ 300 chars), email (asunto + cuerpo), WhatsApp (mensaje corto)

**Reglas de redacción:**
- Mencionar el sector específico de la empresa
- Referenciar el pain point más probable según contexto encontrado
- Tono consultivo, no vendedor — hacer una pregunta abierta
- No mencionar precio en primer contacto
- CTA claro y único por mensaje

**Output:** 1–3 mensajes por contacto (uno por canal disponible)

---

### `señal-crm-exporter`
**Responsabilidad:** tomar la estructura consolidada y escribir el archivo Excel final.

**Acciones:**
- Crear archivo `.xlsx` con openpyxl
- Generar las 4 pestañas con formato, encabezados y anchos de columna correctos
- Aplicar color coding por score (rojo/amarillo/verde)
- Guardar en `/output/` con timestamp en el nombre

---

## 4. Estructura del Output Excel

### Pestaña 1: Empresas
| Columna | Descripción |
|---------|-------------|
| ID | Identificador interno |
| Nombre empresa | Razón social |
| NIT | Si disponible |
| Sector | Sector industrial |
| Tamaño estimado | Rango de empleados |
| Ciudad | Ciudad principal |
| Web | URL sitio corporativo |
| LinkedIn empresa | URL perfil LinkedIn |
| Fuente | Dónde fue encontrada |
| Score | 1–10 |
| Clasificación | Caliente / Tibio / Frío |
| Contexto | Notas relevantes del enriquecimiento |

### Pestaña 2: Contactos
| Columna | Descripción |
|---------|-------------|
| ID contacto | Identificador interno |
| ID empresa | FK a pestaña Empresas |
| Nombre completo | |
| Cargo | Cargo exacto encontrado |
| Prioridad cargo | 1–5 según ICP |
| Email | Si disponible |
| LinkedIn | URL perfil |
| Teléfono | Si disponible |
| Fuente | Dónde fue encontrado |

### Pestaña 3: Mensajes
| Columna | Descripción |
|---------|-------------|
| ID contacto | FK a pestaña Contactos |
| Empresa | Nombre empresa |
| Contacto | Nombre contacto |
| Canal | LinkedIn / Email / WhatsApp |
| Asunto | Solo para email |
| Mensaje | Texto completo personalizado |
| Estado envío | Pendiente / Enviado / Respondió |

### Pestaña 4: Pipeline
| Columna | Descripción |
|---------|-------------|
| ID empresa | FK a pestaña Empresas |
| Empresa | Nombre empresa |
| Contacto principal | |
| Score | |
| Etapa | Prospecto / Contactado / Demo / Negociación / Cerrado / Descartado |
| Fecha primer contacto | Para que comercial llene |
| Próxima acción | Para que comercial llene |
| Notas comercial | Para que comercial llene |
| Responsable comercial | Para que comercial llene |

---

## 5. Stack y Herramientas

| Componente | Tecnología |
|------------|-----------|
| Lenguaje | Python 3.11+ |
| Excel export | `openpyxl` |
| Búsqueda web | `WebSearch` (herramienta Claude Code) |
| Scraping web | `WebFetch` (herramienta Claude Code) |
| Orquestación | Claude Code Agent SDK |
| Output | `/output/prospectos_SEÑAL_YYYYMMDD_HHMMSS.xlsx` |

### Dependencias Python
```
openpyxl>=3.1.0
```

No se requieren APIs de pago. Todo el enriquecimiento usa fuentes públicas gratuitas.

---

## 6. Convenciones del Proyecto

### Estructura de carpetas
```
ventas SEÑAL/
├── CLAUDE.md                  # Este archivo
├── agents/                    # Un archivo por agente
│   ├── orchestrator.py
│   ├── researcher.py
│   ├── enricher.py
│   ├── scorer.py
│   ├── message_writer.py
│   └── crm_exporter.py
├── models/                    # Dataclasses compartidas
│   └── lead.py                # Company, Contact, Message, PipelineEntry
├── output/                    # Excel generados (ignorar en git)
└── README.md
```

### Modelos de datos
Usar `dataclasses` de Python para representar `Company`, `Contact`, `Message` y `PipelineEntry`. Pasar objetos tipados entre agentes, no diccionarios libres.

### Scoring
- Score se calcula siempre antes de escribir mensajes
- Leads con score < 3 no pasan al message_writer ni al Excel final
- El score es un decimal 1–10 (ej: 8.5), con un decimal máximo

### Mensajes
- Máximo 300 caracteres para LinkedIn (nota de conexión)
- Máximo 150 palabras para email
- Máximo 80 palabras para WhatsApp
- Siempre en español colombiano (voseo solo si la empresa es informal)
- Nunca mencionar precio en primer contacto

### Fuentes
- Priorizar RUES y Supersociedades para datos legales/financieros
- LinkedIn solo para contactos y validación de tamaño
- No hacer scraping agresivo — respetar robots.txt
- Si un dato no se encuentra, dejar celda vacía (no inventar)

### Output Excel
- Nombre de archivo: `prospectos_SEÑAL_YYYYMMDD_HHMMSS.xlsx`
- Guardar siempre en `/output/`
- Filas con score caliente (≥8) en verde claro (`#D9EAD3`)
- Filas con score tibio (6–7.9) en amarillo claro (`#FFF2CC`)
- Filas con score frío (3–5.9) sin color de fondo
- Encabezados en negrita con fondo gris (`#CCCCCC`)

### Git
- No commitear archivos de `/output/`
- No commitear credenciales ni cookies de sesión

---

## 7. Stack Técnico de la App Web

| Capa | Tecnología |
|------|-----------|
| Frontend | Next.js + shadcn/ui |
| Backend | FastAPI + Python |
| ORM + modelos | SQLModel |
| Base de datos | PostgreSQL 16 |
| Background jobs | Celery + Redis 7 |
| Notificaciones | Resend (email) + Slack webhook |
| Agentes | Anthropic SDK (`claude-sonnet-4-6`) |
| Infraestructura local | Docker Compose |

---

## 8. Arquitectura de Datos — PostgreSQL

### Tabla `runs`
Cada ejecución del pipeline. Campos clave: `id`, `sector`, `ciudad`, `cantidad_target`, `status` (pending/running/completed/failed/cancelled), `current_step`, `progress_pct`, `total_found`, `total_calientes`, `excel_path`, `celery_task_id`.

### Tabla `companies`
Empresa encontrada + enriquecida + scoreada + estado pipeline CRM.
- **Researcher:** `nombre_empresa`, `nit`, `sector`, `ciudad`, `web`, `linkedin_empresa`, `tamano_estimado`, `fuente`
- **Enricher:** `email_generico_empresa`, `telefono_empresa`, `contexto_adicional`
- **Scorer:** `score`, `clasificacion`, `plan_sugerido`, `justificacion_score`, `score_sector/campo/tamano/contacto/bonus`
- **Pipeline CRM:** `pipeline_stage` (prospecto/contactado/demo/negociación/cerrado/descartado), `notas_comercial`, `proxima_accion`, `fecha_primer_contacto`

### Tabla `contacts`
Contactos por empresa. Campos: `company_id`, `nombre`, `cargo`, `cargo_prioridad` (1–5), `email`, `confianza_email` (alta/media/baja), `linkedin`, `accion_sugerida`.

### Tabla `messages`
Mensajes generados. Campos: `contact_id`, `company_id`, `canal` (email/linkedin/whatsapp), `asunto`, `mensaje`, `estado_envio` (pendiente/enviado/respondió/rebotó/descartado).

### Tabla `blacklist`
Opt-outs y exclusiones. Campos: `tipo` (empresa/contacto/dominio), `valor`, `razon`.

### Tabla `run_logs`
Logs estructurados por paso para debugging en UI. Campos: `run_id`, `step`, `level` (info/warning/error), `message`, `payload` (JSONB).

---

## 9. Arquitectura de Software

### Backend (FastAPI)
```
backend/
├── app/
│   ├── main.py                  # FastAPI app v0.2.0 + CORS + /health + /stats + todos los routers
│   ├── config.py                # pydantic-settings (incluye resend_to_email)
│   ├── database.py              # engines async (FastAPI) + sync (Celery)
│   ├── models/                  # SQLModel — fuente de verdad del esquema
│   │   ├── run.py / company.py / contact.py / message.py / blacklist.py / run_log.py
│   ├── schemas/                 # Pydantic request/response (IMPLEMENTADO)
│   │   ├── run.py / company.py / contact.py / message.py / blacklist.py
│   ├── routers/                 # HTTP endpoints por entidad (IMPLEMENTADO)
│   │   ├── runs.py / companies.py / contacts.py / messages.py / pipeline.py / blacklist.py / sse.py
│   ├── services/                # Lógica de negocio sin HTTP (IMPLEMENTADO)
│   │   ├── run_service.py / company_service.py / contact_service.py / message_service.py / blacklist_service.py
│   ├── agents/                  # Los 5 agentes Claude como clases Python (IMPLEMENTADO)
│   │   ├── base.py              # AgentBase: Anthropic SDK + retry + JSON parser
│   │   ├── researcher.py / enricher.py / scorer.py / message_writer.py / crm_exporter.py
│   ├── utils/                   # Utilidades transversales (IMPLEMENTADO)
│   │   └── notifications.py     # Slack webhook + Resend email
│   └── tasks/
│       ├── celery_app.py        # Celery instance + Redis broker
│       └── pipeline.py          # run_prospecting_pipeline(run_id) — pipeline completo
```

### Frontend (Next.js)
```
frontend/
├── src/
│   ├── app/
│   │   ├── dashboard/           # métricas y stats
│   │   ├── runs/                # historial + progreso SSE en tiempo real
│   │   ├── prospects/           # tabla de empresas con filtros
│   │   ├── pipeline/            # kanban drag & drop
│   │   └── messages/            # mensajes por canal
│   ├── components/              # shadcn/ui + componentes por sección
│   ├── lib/api/                 # fetch tipado al backend
│   ├── lib/hooks/               # TanStack Query + use-run-sse.ts (EventSource)
│   └── types/                   # tipos espejo del backend
```

### Flujo de capas
```
POST /runs
  → routers/runs.py
  → services/run_service.py  (crea Run en DB)
  → tasks/pipeline.py  (encola en Celery via Redis)
    → agents/researcher → enricher → scorer → message_writer → crm_exporter
    (cada step publica evento en Redis pub/sub)
  → routers/sse.py  (stream SSE al browser)
  → utils/notifications.py  (Slack + Resend al terminar)
```

### Decisiones técnicas
- **Pipeline = una sola Celery task** con checkpoints (no una task por agente)
- **SSE** para tiempo real (unidireccional, más simple que WebSockets)
- **Dos engines de DB**: asyncpg para FastAPI, psycopg2 para Celery workers
- **Redis pub/sub** como canal entre worker y SSE endpoint
- **Agentes como clases Python** heredando de `AgentBase` — los `.md` de `.claude/agents/` son los prompts

---

## 10. Plan de Implementación

### ✅ Fase 1 — Infraestructura base (COMPLETADA)
- [x] `docker-compose.yml` con postgres + redis + backend + worker
- [x] `.env` con credenciales configuradas
- [x] `.gitignore` y `.env.example`
- [x] `backend/pyproject.toml` con todas las dependencias
- [x] `backend/Dockerfile` + `entrypoint.sh` (corre `alembic upgrade head` al arrancar)
- [x] `backend/alembic.ini` + `backend/alembic/env.py`
- [x] `backend/app/config.py` — pydantic-settings
- [x] `backend/app/database.py` — engines async + sync
- [x] `backend/app/main.py` — FastAPI + CORS + `/health`
- [x] Modelos SQLModel: `Run`, `Company`, `Contact`, `Message`, `Blacklist`, `RunLog`
- [x] `backend/app/tasks/celery_app.py` + `pipeline.py` (stub)

### ✅ Fase 2 — Agentes como código Python (COMPLETADA)
- [x] `agents/base.py` — AgentBase con Anthropic SDK, retry (3 intentos backoff), JSON parser, web_search (DuckDuckGo) + web_fetch (httpx)
- [x] `agents/researcher.py` — LeadResearcher con prompt de `.claude/agents/señal-lead-researcher.md`
- [x] `agents/enricher.py` — LeadEnricher
- [x] `agents/scorer.py` — LeadScorer
- [x] `agents/message_writer.py` — MessageWriter
- [x] `agents/crm_exporter.py` — CRMExporter puro openpyxl (sin LLM): 4 pestañas, color coding, Pipeline ordenado por score
- [x] `agents/__init__.py` — exports de todos los agentes
- [x] `alembic/script.py.mako` — template Mako que faltaba
- [x] Migración Alembic `246e9c9b6842_initial_schema` generada y aplicada — 6 tablas en PostgreSQL

**Notas de implementación:**
- `web_search` usa DuckDuckGo HTML (`html.duckduckgo.com/html/`) — sin API key, gratuito
- `web_fetch` usa httpx con User-Agent de Chrome — sin API key
- `AgentBase._agentic_loop` maneja el ciclo tool_use → end_turn completo
- `CRMExporter` no es un agente LLM; genera el Excel directamente en Python
- Los prompts de sistema viven en cada archivo `.py` como strings (no en los `.md` de `.claude/agents/`)
- **Requiere:** `ANTHROPIC_API_KEY` en `.env` para que los agentes funcionen

### ✅ Fase 3 — Pipeline Celery completo (COMPLETADA)
- [x] `tasks/pipeline.py` — orquesta los 5 agentes secuencialmente con checkpoints en DB
- [x] Checkpoints en DB en cada step (`runs.current_step`, `runs.progress_pct`) — pasos: 5% → 20% → 40% → 60% → 80% → 100%
- [x] Redis pub/sub — publica eventos SSE desde el worker en cada transición de step
- [x] `routers/sse.py` — endpoint `GET /runs/{id}/stream` con heartbeat cada 20s y timeout de 10 min
- [x] `utils/notifications.py` — Slack webhook + Resend email al terminar run (opcionales, fire-and-forget)

**Notas de implementación:**
- El pipeline persiste empresas, contactos y mensajes en DB después de cada agente
- Empresas con `incluir_en_pipeline=False` (score < 3) se excluyen del message_writer y del Excel
- Si un agente falla, el run queda en `status=failed` con `error_message` detallado
- `utils/notifications.py` requiere `RESEND_API_KEY` + `RESEND_TO_EMAIL` y/o `SLACK_WEBHOOK_URL` en `.env`

### ✅ Fase 4 — API REST completa (COMPLETADA)
- [x] `schemas/` — Pydantic schemas para Run, Company, Contact, Message, Blacklist (request + response)
- [x] `services/` — lógica de negocio desacoplada de HTTP: `run_service`, `company_service`, `contact_service`, `message_service`, `blacklist_service`
- [x] `routers/runs.py` — `POST /runs`, `GET /runs`, `GET /runs/{id}`, `DELETE /runs/{id}` (cancela), `GET /runs/{id}/logs`, `GET /runs/{id}/excel`
- [x] `routers/companies.py` — `GET /companies` con filtros (run_id, sector, clasificación, score_min/max, pipeline_stage), `GET /companies/{id}`, `PATCH /companies/{id}/pipeline`
- [x] `routers/contacts.py` — `GET /contacts` filtrable por company_id, run_id, cargo_prioridad, has_email
- [x] `routers/messages.py` — `GET /messages` filtrable, `PATCH /messages/{id}/status`
- [x] `routers/pipeline.py` — `GET /pipeline/kanban` — empresas agrupadas por etapa para kanban
- [x] `routers/blacklist.py` — CRUD completo: `POST`, `GET`, `DELETE /blacklist/{id}`
- [x] `GET /stats` — métricas globales para dashboard (runs, companies, contacts, messages)
- [x] `main.py` actualizado — versión 0.2.0, todos los routers registrados

**Endpoints disponibles (16 total):**
```
POST   /runs                          # Crear run + encolar Celery
GET    /runs                          # Listar runs (paginado)
GET    /runs/{id}                     # Estado de un run
DELETE /runs/{id}                     # Cancelar run
GET    /runs/{id}/logs                # Logs por step/level
GET    /runs/{id}/excel               # Descargar Excel
GET    /runs/{id}/stream              # SSE tiempo real
GET    /companies                     # Listar con filtros
GET    /companies/{id}                # Detalle empresa
PATCH  /companies/{id}/pipeline       # Actualizar etapa CRM
GET    /contacts                      # Listar contactos
GET    /messages                      # Listar mensajes
PATCH  /messages/{id}/status          # Marcar enviado/respondió
GET    /pipeline/kanban               # Kanban agrupado por etapa
GET    /blacklist  /  POST  /  DELETE # CRUD blacklist
GET    /stats                         # Métricas dashboard
```

### ⬜ Fase 5 — Frontend Next.js
- [ ] Setup Next.js + shadcn/ui + Tailwind + TanStack Query
- [ ] Layout: sidebar + header
- [ ] `/dashboard` — stats cards + recent runs + top leads
- [ ] `/runs` — tabla + formulario nuevo run + progreso SSE en tiempo real
- [ ] `/prospects` — tabla filtrable con score-badge
- [ ] `/pipeline` — kanban drag & drop (dnd-kit)
- [ ] `/messages` — tabla con copy/paste + cambio de estado

---

## 11. Variables de Entorno Requeridas

```bash
POSTGRES_PASSWORD=        # contraseña del contenedor PostgreSQL
ANTHROPIC_API_KEY=        # console.anthropic.com — requerido desde Fase 2
RESEND_API_KEY=           # resend.com — requerido en Fase 3
SLACK_WEBHOOK_URL=        # api.slack.com/messaging/webhooks — requerido en Fase 3
NEXT_PUBLIC_API_URL=      # http://localhost:8000 en desarrollo
```

## 12. Comandos Útiles

```bash
# Levantar todo
docker compose up --build

# Solo levantar (sin rebuild)
docker compose up

# Ver logs de un servicio
docker compose logs -f backend
docker compose logs -f worker

# Generar migración Alembic (después de cambiar modelos)
docker compose exec backend alembic revision --autogenerate -m "descripcion"

# Aplicar migraciones
docker compose exec backend alembic upgrade head

# Verificar que el backend responde
curl http://localhost:8000/health
```
