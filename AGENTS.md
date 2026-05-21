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
| **ExperimentTemplate** | A specific analysis that can be run on a sample type — contains `workerForm`, `calculations`, and output `template`. `userForm` is optional. |
| **Experiment** | One instance of an analysis in progress. `id` is supplied by the Ticketing Service (1 exp_id per analysis selected). Stores a full snapshot of the template at creation time. The worker embeds measured values directly into the state blob via PUT. |

---

## Architecture

```
main.py                                  # FastAPI app factory + OTEL init + lifespan
migrations/
  001_initial_schema.up.sql              # Run manually — creates all tables
  001_initial_schema.down.sql            # Tear down
sql_mock/
  900_seed_samples.up.sql                # Seed sample types (dev only)
  901_seed_experiment_templates.up.sql   # Seed analysis templates (dev only)
app/
  config.py                              # Pydantic Settings — reads from .env
  database.py                            # Async SQLAlchemy engine + get_db dependency
  db_models.py                           # ORM models (SampleType, ExperimentTemplate, Experiment)
  models.py                              # Pydantic request/response models
  observability/
    telemetry.py                         # OpenTelemetry TracerProvider setup
  routers/
    samples.py                           # /api/samples — SampleType + ExperimentTemplate CRUD
    experiments.py                       # /api/experiments — Experiment CRUD
  services/
    sample_service.py                    # Business logic for samples and templates
    experiment_service.py                # Business logic for experiments
  repositories/
    sample_repository.py                 # Async DB access for sample_types and experiment_templates
    experiment_repository.py             # Async DB access for experiments
tests/
  conftest.py                            # Async fixtures — test engine, seed catalogue, per-test rollback client
  test_samples.py
  test_experiments.py
```

Layer rules (enforce strictly):
- **Routers** call services only. No direct repo or DB access, no business logic.
- **Services** call repositories only. They own OTEL spans, commit/rollback, and 404-logic.
- **Repositories** access the DB only. No HTTP concerns, no span creation, no commits — `flush()` only.

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

**Analysis templates (nested under sample)**

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/samples/{sample_id}/analyses` | Create a template |
| `GET` | `/api/samples/{sample_id}/analyses` | List templates for a sample |
| `GET` | `/api/samples/{sample_id}/analyses/{template_id}` | Get one template |
| `PUT` | `/api/samples/{sample_id}/analyses/{template_id}` | Update template |
| `DELETE` | `/api/samples/{sample_id}/analyses/{template_id}` | Soft delete |

**Experiments**

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/experiments` | Create experiment — snapshots full template into `state` |
| `GET` | `/api/experiments` | List experiments (summary — no state detail) |
| `GET` | `/api/experiments/{exp_id}` | Full detail including the complete `state` blob |
| `PUT` | `/api/experiments/{exp_id}` | Replace `state` with worker-filled blob — send the whole JSON back with `value` added to each question |
| `DELETE` | `/api/experiments/{exp_id}` | Soft delete |

POST body:
```json
{ "exp_id": "uuid-from-ticketing-service", "sample_id": "uuid", "template_id": "uuid" }
```

PUT body — send the full state blob back with `"value"` added to each question:
```json
{
  "state": {
    "id": "uuid", "name": "Calorific Value (GCV)", "template": "GCV = {{gcv_cal_g}} ...",
    "workerForm": {
      "questions": [
        { "id": "sample_mass", "type": "number", "default": 1.0, "value": 1.023, ... }
      ]
    },
    "calculations": { ... }
  }
}
```

Returns 409 if `exp_id` already exists.

---

## Data model notes

### Experiment state (JSONB)
`experiments.state` stores:
```json
{
  "sample_id": "uuid",
  "template_id": "uuid",
  "state": {
    "id": "uuid",
    "name": "Proximate Analysis",
    "description": "...",
    "workerForm": { ... },
    "calculations": { ... },
    "template": "Output string with {{placeholders}}"
  }
}
```
`state.state` is the full template snapshot at creation time. On PUT the worker sends back the same blob with `"value"` added to each question — the whole `state` key is replaced, `sample_id` and `template_id` are preserved.

### ExperimentTemplate JSONB schema
`experiment_templates.template` stores:
```json
{
  "userForm": { "title": "...", "description": "...", "questions": [ ... ] },
  "workerForm": { "title": "...", "description": "...", "questions": [ ... ] },
  "calculations": { "result_var": "js-style expression" },
  "template": "Output string with {{result_var}} placeholders"
}
```

`userForm` is optional. `calculations` uses JavaScript syntax (evaluated by the frontend). `template` uses `{{variable}}` placeholders where variables come from `calculations` keys.

Number questions support extra display fields passed through via `FormQuestion(extra="allow")`: `min`, `max`, `step`, `default`. The frontend uses these to render the input; the worker fills in `value` when submitting results.

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
1. Add route to the appropriate router.
2. Add a service function with an OTEL span wrapping every logical operation:
   ```python
   with tracer.start_as_current_span("service_name.operation") as span:
       span.set_attribute("relevant.id", str(value))
   ```
3. Add a repository function if new DB access is needed. Repos `flush()` only — services `commit()`.
4. Add tests covering: happy path, 404, response shape.

### New ExperimentTemplate
1. Insert via `POST /api/samples/{sample_id}/analyses` or add to `sql_mock/901_seed_experiment_templates.up.sql`.
2. The JSONB must include `workerForm`, `calculations`, and `template`. `userForm` is optional.
3. Add tests asserting the template appears in `GET .../analyses`.

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

---

## Database

Migrations are run **manually** — no Alembic.

```bash
# Apply schema
psql $DATABASE_URL -f migrations/001_initial_schema.up.sql

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
| `OTEL_ENDPOINT` | No | OTLP/HTTP endpoint e.g. `http://localhost:4318/v1/traces`; omit to disable |

---

## Code style

- Formatter: **black** (`uv run black .`)
- Import sort: **isort** (`uv run isort .`)
- No inline comments unless the WHY is non-obvious.
- No docstrings on trivial functions.
- Pydantic request/response models → `app/models.py`
- SQLAlchemy ORM models → `app/db_models.py`
- Do not mix Pydantic and SQLAlchemy imports in the same file.
