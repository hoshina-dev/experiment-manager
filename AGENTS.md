# AGENTS.md — Experiment Manager

This file tells AI coding agents how to work in this repository.
Read it before writing any code.

---

## What this service does

Experiment Manager is a **lab experiment tracking service**.
It stores analysis templates for lab experiments, serves them as structured JSON, and tracks the state of each experiment ticket assigned by the Ticketing Service.

Key concepts:

| Term | Meaning |
|---|---|
| **SampleType** | A category of material being analysed (e.g. Coal, Tomato, Environment Water) |
| **Experiment template** | A specific analysis that can be run on a sample type — contains `clientForm`, `labForm`, and `calculations`. Template `name`/`description` live in DB columns, not inside the JSONB blob. |
| **Experiment context** | The full JSON blob stored per experiment instance (`experiments.state`). Created from the experiment template at experiment creation time; updated by the worker via PUT. Always refer to this as "experiment context", never "experiment state" or "experiment JSON". |
| **Experiment** | One instance of an analysis in progress. `id` is supplied by the Ticketing Service (1 exp_id per analysis selected). Stores the experiment context at creation time. The worker embeds measured values directly into the context via PUT. |

---

## Architecture

```
main.py                                  # FastAPI app factory + OTEL init + lifespan (queue, executor, startup recovery)
migrations/
  001_initial_schema.up.sql              # Run manually — creates all tables
  001_initial_schema.down.sql            # Tear down
sql_mock/
  900_seed_samples.up.sql                # Seed sample types (dev only)
  901_seed_experiment_templates.up.sql   # Seed analysis templates (dev only)
  902_seed_heat_capacity_template.up.sql # Heat Capacity Analysis template under Coal
  903_seed_charcoal_template.up.sql      # PDF component layout for Heat Capacity Analysis
app/
  config.py                              # Pydantic Settings — reads from .env (Settings, R2Settings, ReportWorkerSettings)
  database.py                            # Async SQLAlchemy engine + get_db dependency
  db_models.py                           # ORM models (SampleType, ExperimentTemplate, Experiment, PdfTemplate)
  models.py                              # Pydantic request/response models
  report_worker.py                       # ReportJob dataclass + async report_worker coroutine (ProcessPoolExecutor)
  observability/
    telemetry.py                         # OpenTelemetry TracerProvider setup
  pdf/
    __init__.py                          # Re-exports generate_pdf
    components.py                        # PDF component dataclasses + component_from_dict
    context.py                           # flatten_context — builds template variable map from experiment context
    engine.py                            # TemplateEngine: parse, validate, build_context
    parser.py                            # interpolate_template, extract_fields
    renderer.py                          # generate_pdf entry point + render_pdf
    r2_client.py                         # upload_pdf, presign_download, check_connection (boto3)
  routers/
    samples.py                           # /api/samples — SampleType + ExperimentTemplate CRUD
    experiments.py                       # /api/experiments — Experiment CRUD + calculate
    reports.py                           # /api/experiments/{id}/report/generate|download
  services/
    sample_service.py                    # Business logic for samples and templates
    experiment_service.py                # Business logic for experiments + report enqueue
    calculation_service.py               # Safe Python eval, calculate()
  repositories/
    sample_repository.py                 # Async DB access for sample_types and experiment_templates
    experiment_repository.py             # Async DB access for experiments + report status updates
tests/
  conftest.py                            # Async fixtures — test engine, seed catalogue, per-test rollback client
  test_samples.py
  test_experiments.py
  test_calculation_service.py            # Unit tests for _extract_inputs, _eval_calculations
  test_calculate_endpoint.py             # Integration tests for POST /calculate
```

Layer rules (enforce strictly):
- **Routers** call services only. No direct repo or DB access, no business logic, no `HTTPException`. One line per handler: `return await service.foo(...)`.
- **Services** call repositories only. They own OTEL spans, commit/rollback, and **all error raising**. If a repo returns `None` or an operation fails, the service raises `HTTPException`. Never return `None` from a service function — raise instead.
- **Repositories** access the DB only. Return `None` for not-found. Raise only SQLAlchemy exceptions (`IntegrityError` etc.). No `HTTPException`, no span creation, no commits — `flush()` only.

Error-handling convention:
```python
# ✅ correct — HTTPException raised in service
async def get_sample(session, sample_id) -> SampleSummary:
    row = await repo.get_sample_type(session, sample_id)
    if row is None:
        raise HTTPException(404, f'Sample "{sample_id}" not found')
    return SampleSummary(...)

# ✅ correct — router is a dumb pass-through, no HTTPException import
@router.get("/{sample_id}")
async def get_sample(sample_id: uuid.UUID, db: DbDep) -> SampleSummary:
    return await service.get_sample(db, sample_id)

# ❌ wrong — router raising HTTPException
@router.get("/{sample_id}")
async def get_sample(sample_id: uuid.UUID, db: DbDep) -> SampleSummary:
    result = await service.get_sample(db, sample_id)
    if result is None:
        raise HTTPException(404, "not found")   # ← move this to the service
    return result
```

---

## Endpoints

**Sample types**

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/samples` | Create a sample type |
| `GET` | `/api/samples` | List all sample types |
| `GET` | `/api/samples/{sample_id}` | Get one sample type |
| `PUT` | `/api/samples/{sample_id}` | Update name/description |
| `DELETE` | `/api/samples/{sample_id}` | Soft delete |

**Experiment templates (nested under sample)**

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/samples/{sample_id}/experiments` | Create a template (v1, starts its own lineage) |
| `GET` | `/api/samples/{sample_id}/experiments` | List current versions only (`is_current=true`) |
| `GET` | `/api/samples/{sample_id}/experiments/{template_id}` | Get a specific version by id |
| `PUT` | `/api/samples/{sample_id}/experiments/{lineage_id}` | Edit template — mutates in place if no experiments exist yet; otherwise creates a new SCD2 version row |
| `GET` | `/api/samples/{sample_id}/experiments/{lineage_id}/history` | All versions for a lineage, newest first |
| `DELETE` | `/api/samples/{sample_id}/experiments/{template_id}` | Soft delete a specific version |

**PDF templates (nested under a specific template version)**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/samples/{sample_id}/experiments/{template_id}/pdf` | Get PDF components for a specific version |
| `PUT` | `/api/samples/{sample_id}/experiments/{lineage_id}/pdf` | Create or replace PDF components — in-place if no experiments reference the current version; otherwise creates a new SCD2 version row with the new layout |
| `DELETE` | `/api/samples/{sample_id}/experiments/{template_id}/pdf` | Hard delete the PDF layout from a specific version |

**Experiments**

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/experiments` | Create experiment — initialises experiment context from the experiment template |
| `GET` | `/api/experiments` | List experiments (summary only) |
| `GET` | `/api/experiments/{exp_id}` | Full experiment context |
| `PUT` | `/api/experiments/{exp_id}` | Replace experiment context — send the whole JSON back with `value` added to each question |
| `DELETE` | `/api/experiments/{exp_id}` | Soft delete |
| `POST` | `/api/experiments/{exp_id}/calculate` | Evaluate `calculations` formulas against `values` → writes `result` on each calculation → returns updated context |

**Reports**

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/experiments/{exp_id}/report/generate` | Enqueue PDF generation → 202 `{ status: "pending" }` |
| `GET` | `/api/experiments/{exp_id}/report/download` | Get presigned download URL → `{ url, expires_in: 900 }` |

POST `/api/experiments` body:
```json
{ "exp_id": "uuid-from-ticketing-service", "sample_id": "uuid", "lineage_id": "uuid" }
```
`lineage_id` identifies the experiment template concept; the server resolves it to the current version id and freezes it into the experiment context.

PUT body — send clientForm, labForm, calculations, and values:
```json
{
  "clientForm": { "name": "...", "questions": [ ... ] },
  "labForm": { "name": "...", "questions": [ ... ] },
  "calculations": { "gcv_cal_g": { "formula": "round((values['water_equivalent'] * values['temp_rise']) / values['sample_mass'])" } },
  "values": { "sample_mass": 1.023, "temp_rise": 2.5 }
}
```

Returns 409 if `exp_id` already exists.

---

## Data model notes

### Experiment context (JSONB)
`experiments.state` stores the **experiment context**. At creation it is initialised from the experiment template and looks like:
```json
{
  "id":           "exp-uuid",
  "sample_id":    "uuid",
  "template_id":  "uuid",
  "lineage_id":   "uuid",
  "name":         "Proximate Analysis",
  "description":  "...",
  "clientForm":   { "name": "...", "questions": [ ... ] },
  "labForm":      { "name": "...", "questions": [ ... ] },
  "calculations": { "result_var": { "formula": "...", "result": 42.0 } },
  "values":       { "sample_mass": 1.023 }
}
```

Field notes:
- `id`, `sample_id`, `template_id`, `lineage_id`, `name`, `description` — frozen at creation; cannot be changed via PUT.
- `values` — collected answers keyed by question id; filled in by the worker via PUT.
- `calculations` — `{ formula, result? }` objects. Formulas use `values['question_id']`. Evaluated server-side by `POST /calculate`, which writes `result`.
- Question options nest under `config`; answers never live on question objects.

On PUT the worker sends back `clientForm`, `labForm`, `calculations`, and `values`. The service merges these with the authoritative frozen fields from the existing context.

`GET /api/experiments/{exp_id}` returns `**context` merged with the DB-level report columns (`report_status`, `report_r2_key`, `report_generated_at`, `created_at`).

### Experiment template JSONB schema
`experiment_templates.template` stores:
```json
{
  "clientForm":   { "name": "...", "description": "...", "questions": [ ... ] },
  "labForm":      { "name": "...", "description": "...", "questions": [ ... ] },
  "calculations": { "result_var": { "formula": "Python expression" } }
}
```

Template `name`/`description` are DB columns only — not duplicated inside the JSONB blob. Aligned with `form-poc/schema-bundle/experiment-template.schema.json`.

### Calculation engine (`app/services/calculation_service.py`)
- `collect_values(context)` — merges `values` with `config.default` from clientForm/labForm questions.
- `_eval_calculations(values, formulas)` — evaluates each formula in order in a restricted namespace (`round`, `abs`, `min`, `max`, `sum`, `len`, `mean`, `median`, `stdev`, `math`, plus `values` dict). Later expressions can reference earlier results.
- `calculate(session, exp_id)` — orchestrates: load experiment → collect values → eval → write `calculations[].result` → commit → return updated experiment context.

### Conflict (409) responses
- `POST /api/samples` — duplicate sample name
- `PUT /api/samples/{id}` — renaming to an already-taken name
- `POST /api/samples/{id}/analyses` — duplicate analysis name within a sample
- `POST /api/experiments` — `exp_id` already exists

### Soft deletes
All three tables have `deleted_at TIMESTAMPTZ`. All queries filter `WHERE deleted_at IS NULL`. Never hard delete.

### updated_at
Maintained by the SQLAlchemy ORM via `onupdate=_now` — no DB triggers needed.

---

## Conventions — required for every change

### New endpoint
1. Add route to the appropriate router — one line: `return await service.foo(...)`. No `HTTPException` in routers.
2. Add a service function that owns all error logic (`raise HTTPException`) and wraps every logical operation in an OTEL span:
   ```python
   with tracer.start_as_current_span("service_name.operation") as span:
       span.set_attribute("relevant.id", str(value))
   ```
3. Add a repository function if new DB access is needed. Repos return `None` for not-found, `flush()` only — services `commit()`.
4. Add tests covering: happy path, 404, response shape.

### New experiment template
1. Insert via `POST /api/samples/{sample_id}/experiments` or add a new seed file under `sql_mock/`.
2. The JSONB must include `clientForm`, `labForm`, and `calculations`. Question options nest under `config`.
3. Do **not** edit past seed files — add a new numbered seed file instead.
4. Add tests asserting the template appears in `GET .../experiments`.

### New sample type
1. Insert via `POST /api/samples` or add to `sql_mock/900_seed_samples.up.sql`.
2. Add corresponding templates.
3. Add tests.

### OTEL span naming convention
```
{service_module}.{operation}

sample_service.get_samples
sample_service.create_analysis
experiment_service.create
experiment_service.update
```
Always set `sample.id` and/or `exp_id` as span attributes where applicable.

### Test conventions
- All tests are `async def` — `asyncio_mode = "auto"` is set in `pyproject.toml`.
- Use the `client` fixture from `conftest.py` — wraps each test in a transaction that rolls back.
- Tests require `TEST_DATA_SOURCE_NAME` in `.env`. If absent, all tests skip automatically.
- Catalogue seed data is inserted once per session by `seed_catalogue`. Use the fixed IDs from `conftest.py` (`COAL_ID`, `PROXIMATE_TEMPLATE_ID`, etc.) in tests that need existing data.
- Never manually commit test data — the rollback fixture handles cleanup.
- Unit tests for pure functions (e.g. `calculation_service`) do not need the `client` fixture — import and call directly.

---

## Database

Migrations are run **manually** — no Alembic.

```bash
# Apply schema
psql $DATABASE_URL -f migrations/001_initial_schema.up.sql
psql $DATABASE_URL -f migrations/002_partial_unique_indexes.up.sql
psql $DATABASE_URL -f migrations/003_report_initial_schema.up.sql
psql $DATABASE_URL -f migrations/004_experiment_report_fields.up.sql
psql $DATABASE_URL -f migrations/005_scd2_experiment_templates.up.sql
psql $DATABASE_URL -f migrations/006_experiment_templates_lineage_id_default.up.sql
psql $DATABASE_URL -f migrations/007_drop_stale_template_name_index.up.sql

# Seed dev data
psql $DATABASE_URL -f sql_mock/900_seed_samples.up.sql
psql $DATABASE_URL -f sql_mock/901_seed_experiment_templates.up.sql

# Tear down
psql $DATABASE_URL -f migrations/001_initial_schema.down.sql
```

---

## Running the project

```bash
# Install dependencies
uv sync

# Start dev server
uv run uvicorn main:app --reload --port 3000

# Run tests (requires TEST_DATA_SOURCE_NAME in .env)
uv run pytest -v

# Format
uv run black . && uv run isort .
```

Environment variables (see `.env.example`):

| Variable | Required | Description |
|---|---|---|
| `DATA_SOURCE_NAME` | Yes | Postgres DSN: `host=... user=... password=... dbname=... port=... sslmode=...` |
| `TEST_DATA_SOURCE_NAME` | For tests | Separate test DB — blank DB is fine, schema created by test suite |
| `CORS_ORIGINS` | No | Comma-separated allowed origins (default `http://localhost:3000`) |
| `OTEL_ENABLED` | No | Set to `true` to export traces and metrics |
| `OTEL_SERVICE_NAME` | No | Service name reported to OpenTelemetry (default `experiment-manager`) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | No | OTLP/gRPC endpoint e.g. `http://localhost:4317` |
| `S3_ENDPOINT` | Yes | R2/S3-compatible endpoint e.g. `http://localhost:9000` |
| `S3_BUCKET` | Yes | Bucket name for storing generated PDFs |
| `S3_ACCESS_KEY` | Yes | S3 access key |
| `S3_SECRET_KEY` | Yes | S3 secret key |
| `S3_REGION` | No | Region (default `auto` for Cloudflare R2) |
| `REPORT_WORKER_MAX_THREADS` | No | ProcessPoolExecutor workers (default `2`) |
| `REPORT_WORKER_QUEUE_MAX_SIZE` | No | Max queued report jobs before 503 (default `50`) |

---

## Code style

- Formatter: **black** (`uv run black .`)
- Import sort: **isort** (`uv run isort .`)
- No inline comments unless the WHY is non-obvious.
- No docstrings on trivial functions.
- Pydantic request/response models → `app/models.py`
- SQLAlchemy ORM models → `app/db_models.py`
- Do not mix Pydantic and SQLAlchemy imports in the same file.
