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
- `web_search` usa **Tavily** (`api.tavily.com`) como primario + **DuckDuckGo HTML** como fallback automático si Tavily falla — requiere `TAVILY_API_KEY` en `.env`
- `web_fetch` usa httpx con User-Agent de Chrome — sin API key
- `AgentBase._agentic_loop` maneja el ciclo tool_use → end_turn completo
- `CRMExporter` no es un agente LLM; genera el Excel directamente en Python
- Los prompts de sistema viven en cada archivo `.py` como strings (no en los `.md` de `.claude/agents/`)
- **Requiere:** `ANTHROPIC_API_KEY` o `GROQ_API_KEY` según `AI_PROVIDER` en `.env`

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

## 11. Bugs Críticos Detectados en Producción — Plan de Corrección

> Observados el 2026-05-25 monitoreando un run real en vivo desde el frontend.
> Todos los bugs están en el agente `researcher` y en el loop de Groq en `base.py`.
> **Prioridad: corregir antes de cualquier run de prospección real.**

### Bug 1 — URLs hardcodeadas en el prompt del researcher son 404

**Archivo:** `backend/app/agents/researcher.py` (sección "Directorios sectoriales")

**Síntomas observados:**
- `acp.com.co/afiliados` → 404
- `andesco.org.co/empresas-asociadas` → 404
- `camacol.co/directorio/constructoras` → 404
- `infraestructura.org.co/directorio/constructoras` → 404
- Solo funcionaron: `camacol.co/nosotros/afiliados` y `infraestructura.org.co` (homepage)

**Causa:** Las URLs están escritas a mano en el prompt y los sitios las cambiaron o nunca existieron con esas rutas.

**Fix:** Eliminar todas las URLs hardcodeadas del prompt. Reemplazarlas por **queries de DuckDuckGo** que el agente ejecuta con `web_search`. El modelo descubrirá las URLs reales a partir de los resultados de búsqueda.

```
# Antes (prompt actual — frágil)
web_fetch("https://acp.com.co/afiliados")

# Después (robusto)
web_search("ACP asociacion colombiana petroleo directorio empresas afiliadas site:acp.com.co")
# → el modelo visita la URL real que encuentre en los resultados
```

---

### Bug 2 — El researcher nunca usa DuckDuckGo (su fuente principal)

**Archivo:** `backend/app/agents/researcher.py`

**Síntomas observados:** En todo el run (12+ tool calls), cero llamados a `web_search`/DuckDuckGo. El modelo `llama-3.1-8b-instant` ignoró la instrucción "tu fuente principal" y fue directo a las URLs hardcodeadas.

**Causa:** El modelo 8B no tiene suficiente capacidad de seguir instrucciones con jerarquía compleja. Al ver URLs explícitas en el prompt las usa primero, ignorando la prioridad declarada.

**Fix (dos partes):**

1. **Cambiar modelo del researcher** de `llama-3.1-8b-instant` a `llama-3.3-70b-versatile`. El 70B sigue instrucciones con mucha más fidelidad.

   ```python
   # researcher.py
   groq_model = "llama-3.3-70b-versatile"  # era: llama-3.1-8b-instant
   ```

2. **Restructurar el prompt** para que la sección de DuckDuckGo sea la única instrucción de acción, y los directorios sean opcionales solo si los encuentra vía búsqueda:

   ```
   ## Proceso obligatorio
   1. Usa SIEMPRE web_search como primer paso para cada empresa que busques
   2. Solo visita con web_fetch URLs que encontraste en los resultados del web_search
   3. Nunca intentes URLs que no aparecieron en una búsqueda previa
   ```

---

### Bug 3 — `max_tool_calls` no detiene el loop (el modelo ignora el mensaje de "para")

**Archivo:** `backend/app/agents/base.py`, método `_loop_groq`

**Síntomas observados:** Al llegar al call 12, el código agrega el mensaje `"Devuelve AHORA el JSON..."` pero hace `continue` y vuelve al top del while. Groq retornó otro `tool_calls`, el modelo ignoró la instrucción, y el loop continuó indefinidamente.

**Causa:** El guardia no rompe el loop — solo añade un mensaje que un modelo 8B ignora. El código actual:

```python
if tool_calls_count >= self.max_tool_calls:
    messages.append({...stop message...})
continue  # ← sigue en el loop aunque el modelo haga más tool_calls
```

**Fix:** Después del límite, forzar al menos un intento de respuesta final; si el modelo devuelve otro `tool_calls`, extraer el JSON del contexto acumulado o lanzar excepción controlada:

```python
if tool_calls_count >= self.max_tool_calls:
    # Forzar 1 sola llamada final sin tools disponibles
    response_final = client.post(..., json={..., "tool_choice": "none"})
    return _extract_json(response_final.json()["choices"][0]["message"]["content"])
```

---

### Bug 4 — 413 Payload Too Large de Groq destruye el contexto y reinicia las búsquedas

**Archivo:** `backend/app/agents/base.py`, métodos `_groq_post` y `_trim_groq_context`

**Síntomas observados:** A las 18:29 — 6 errores 413 consecutivos. El `_trim_groq_context` recortó los tool results al 50%, logró un 200 OK, pero el modelo **perdió la memoria de qué URLs ya visitó** y reinició las mismas búsquedas desde cero.

**Causa:** `_trim_groq_context` trunca el texto de los resultados sin eliminar mensajes. El modelo ve mensajes de "visité esta URL" con contenido cortado y no entiende que ya terminó esa búsqueda.

**Fix (tres partes):**

1. **Reducir `_groq_max_chars_search` y `_groq_max_chars_fetch`** preventivamente para no llegar al 413:
   ```python
   _groq_max_chars_search: int = 1500  # era: 2000
   _groq_max_chars_fetch: int = 2000   # era: 2500
   ```

2. **Mejorar `_trim_groq_context`** para eliminar tool results completos (no solo truncar) cuando el contexto es demasiado grande:
   ```python
   # Eliminar los tool results más viejos (no truncar) hasta caber en el límite
   ```

3. **Reducir `max_tool_calls` del researcher a 8** (era 12). Con 8 calls y páginas más cortas, el contexto nunca llega al 413.

---

### Bug 5 — El modelo repite exactamente las mismas URLs fallidas en bucle

**Archivo:** `backend/app/agents/researcher.py` (prompt)

**Síntomas observados:** `camacol.co/directorio/constructoras` fue intentado 3 veces con 404 en cada intento. El modelo no aprende de los 404s dentro de la misma sesión.

**Causa:** El modelo 8B no tiene suficiente capacidad de razonamiento para inferir que si una URL dio 404, sus variantes en el mismo dominio también fallarán.

**Fix:** Agregar en el prompt:
```
## Regla crítica sobre errores 404
Si una URL devuelve error 404 o "not found", NO intentes otras rutas en el mismo dominio.
En su lugar, haz un web_search para encontrar la URL correcta del sitio.
Ejemplo: si "acp.com.co/afiliados" da 404, busca: web_search("ACP Colombia directorio empresas afiliadas")
```

---

### ✅ Fase 6 — Corrección de bugs del Researcher + Loop Groq (COMPLETADA)

**Archivos modificados:**
- `backend/app/agents/researcher.py` — prompt + modelo
- `backend/app/agents/base.py` — `_loop_groq`, `_groq_post`, `_trim_groq_context`, `_groq_max_chars_*`

**Checklist:**
- [x] **researcher.py:** Cambiar `groq_model` a `llama-3.3-70b-versatile`
- [x] **researcher.py:** Eliminar todas las URLs hardcodeadas del prompt
- [x] **researcher.py:** Restructurar prompt para forzar `web_search` como primer paso obligatorio
- [x] **researcher.py:** Agregar regla "si 404, no pruebes rutas del mismo dominio, usa web_search"
- [x] **researcher.py:** Reducir `max_tool_calls` a `8` (override en la subclase)
- [x] **base.py:** Corregir el guardia `max_tool_calls` — usar `tool_choice: none` para forzar respuesta final
- [x] **base.py:** Reducir `_groq_max_chars_search = 800` y `_groq_max_chars_fetch = 1000`
- [x] **base.py:** Mejorar `_trim_groq_context` — paso 1 trunca contenido a 300 chars, paso 2 elimina pares assistant+tool más viejos si sigue grande
- [x] **base.py:** Agregar `parallel_tool_calls: False` — evita que el modelo haga 20+ búsquedas paralelas por turno
- [x] **base.py:** Implementar fallback `_web_search_duckduckgo` — si Tavily falla, usa DuckDuckGo HTML automáticamente
- [x] **docker-compose.yml:** Agregar `TAVILY_API_KEY` en environment de backend y worker
- [x] Runs de prueba realizados — researcher usa Tavily correctamente, sin 413 en cascada

---

---

## 12. Bugs Detectados en Monitoreo Live — 2026-05-25 (segunda sesión)

> Observados monitoreando runs reales en vivo. Todos corregidos en la misma sesión.

### Bug A — `TAVILY_API_KEY` no llegaba al contenedor Docker

**Archivos:** `docker-compose.yml`

**Síntomas:** Cada llamada a `web_search` devolvía HTTP 401 Unauthorized de `api.tavily.com`. El modelo Groq recibía el error y respondía en texto libre: *"Lo siento, no puedo proporcionar resultados"* → `_extract_json` fallaba → pipeline fallaba tras 5 reintentos.

**Causa:** `TAVILY_API_KEY` existía en `.env` pero el bloque `environment:` del worker y el backend en `docker-compose.yml` no la declaraba. Docker Compose solo pasa variables que están explícitamente listadas en `environment:`.

**Fix:** Agregar `TAVILY_API_KEY: ${TAVILY_API_KEY:-}` en la sección `environment` de ambos servicios (`backend` y `worker`) en `docker-compose.yml`. Recrear los contenedores con `docker compose up -d --no-build backend worker`.

---

### Bug B — Sin fallback si Tavily falla

**Archivo:** `backend/app/agents/base.py`, función `_web_search`

**Síntomas:** Cualquier falla de Tavily (401, 429, timeout) dejaba al agente sin capacidad de búsqueda.

**Fix:** Implementar fallback automático Tavily → DuckDuckGo HTML:
```python
def _web_search(query, max_chars):
    if settings.tavily_api_key:
        try:
            return _web_search_tavily(query, max_chars)  # intento primario
        except Exception:
            pass
    return _web_search_duckduckgo(query, max_chars)  # fallback gratuito
```
`_web_search_duckduckgo` hace POST a `html.duckduckgo.com/html/` sin API key y extrae títulos + URLs + snippets con regex.

---

### Bug C — `parallel_tool_calls` causaba 181+ búsquedas Tavily por run

**Archivo:** `backend/app/agents/base.py`, método `_groq_post`

**Síntomas observados:** Un run consumió 181 llamadas a Tavily (free tier = 1000/mes → 5 runs máximo). El ratio fue 181 Tavily : 16 Groq = ~11 búsquedas paralelas por turno Groq.

**Causa:** `llama-3.3-70b-versatile` con `tool_choice: auto` solicita 10-20 tool calls **en paralelo** en una sola respuesta. El código ejecutaba todos antes de revisar el límite `max_tool_calls`. Con 5 reintentos del outer loop, se acumulaban 150-200 búsquedas.

**Impacto secundario:** 181 tool results × 800 chars = ~145,000 chars de contexto → 413 Payload Too Large inevitable.

**Fix:** Agregar `parallel_tool_calls: False` en el payload de Groq:
```python
payload["parallel_tool_calls"] = False  # una herramienta por turno
```
Con esto, el modelo llama **una herramienta a la vez**, espera el resultado y decide si necesita otra. Máximo `max_tool_calls` búsquedas por run.

---

### Bug D — `_trim_groq_context` no reducía suficiente el payload

**Archivo:** `backend/app/agents/base.py`, método `_trim_groq_context`

**Síntomas:** 20+ errores 413 consecutivos (Groq). El trim eliminaba mensajes enteros pero el payload seguía sobre el límite. El run fallaba después de 5 reintentos × 6 intentos de trim = 30 errores 413.

**Causa:** La versión anterior eliminaba el 40% más viejo de los tool result messages. Si quedan pocos mensajes pero con contenido largo (1000 chars c/u), el payload sigue siendo enorme.

**Fix en dos pasos:**
1. **Paso 1 — truncar contenido:** Recorta el `content` de **todos** los tool results a máximo 300 chars. Esto reduce drásticamente el tamaño sin eliminar mensajes (el modelo recuerda qué buscó).
2. **Paso 2 — eliminar si sigue grande:** Si el total estimado sigue > 40,000 chars, elimina el 50% más viejo de los pares assistant+tool.

Además se redujeron los límites preventivos: `_groq_max_chars_search: 1500 → 800` y `_groq_max_chars_fetch: 2000 → 1000`.

---

### Bug E — Barra de progreso SSE siempre en 0%

**Archivos:** `backend/app/routers/sse.py`, `frontend/src/lib/hooks/use-run-sse.ts`, `frontend/src/components/runs/run-progress-row.tsx`

**Síntomas:** La barra de progreso se quedaba en 0% durante toda la ejecución. El backend avanzaba (5% → 20% → 40%...) pero el frontend no lo reflejaba.

**Causa — dos desconexiones en cadena:**

1. **`sse.py` no enviaba el campo `event:` SSE.** Enviaba:
   ```
   data: {"event": "step_start", "data": {...}}
   ```
   Pero el frontend usaba `addEventListener('run_update', ...)` que requiere:
   ```
   event: run_update
   data: {...}
   ```
   Sin el campo `event:`, el navegador nunca dispara los listeners nombrados.

2. **Formato de datos incorrecto.** El frontend esperaba un objeto `Run` completo, pero el backend enviaba `{event, data: {step, progress, message}}`.

**Fix en tres archivos:**

- **`sse.py`:** Mapear el evento interno al tipo SSE correcto y emitir el campo `event:`:
  ```python
  sse_event = {"completed": "run_completed", "failed": "run_failed"}.get(internal_event, "run_update")
  yield f"event: {sse_event}\ndata: {data}\n\n"
  ```

- **`use-run-sse.ts`:** Cambiar `onUpdate` de `(run: Run)` a `(update: SseRunUpdate)` y parsear el formato real:
  ```typescript
  onUpdate({ id: runId, progress_pct: d.progress, current_step: d.message, status: 'running' })
  ```

- **`run-progress-row.tsx`:** Hacer merge del update parcial con el estado local del run (no reemplazo completo):
  ```typescript
  setRun(prev => ({ ...prev, ...update }))
  ```

---

## 13. Variables de Entorno Requeridas

```bash
POSTGRES_PASSWORD=        # contraseña del contenedor PostgreSQL
AI_PROVIDER=              # "anthropic" (pago) o "groq" (gratuito)
ANTHROPIC_API_KEY=        # console.anthropic.com — requerido si AI_PROVIDER=anthropic
GROQ_API_KEY=             # console.groq.com — requerido si AI_PROVIDER=groq (gratis)
TAVILY_API_KEY=           # tavily.com — requerido para web_search (1000 búsquedas/mes gratis)
RESEND_API_KEY=           # resend.com — opcional, para notificaciones email
RESEND_TO_EMAIL=          # email destino de notificaciones
SLACK_WEBHOOK_URL=        # opcional, para notificaciones Slack
NEXT_PUBLIC_API_URL=      # http://localhost:8000 en desarrollo
```

> **Importante:** Todas las variables deben estar en `.env` **Y** declaradas en la sección `environment:` del servicio correspondiente en `docker-compose.yml`. Si solo están en `.env` sin el `environment:`, el contenedor no las recibe.

## 14. Comandos Útiles

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
