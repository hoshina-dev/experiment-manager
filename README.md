# Experiment Manager

A FastAPI service for tracking lab experiment tickets. It stores analysis templates per sample type, manages experiment state, and generates PDF reports stored in S3-compatible object storage.

## Tech stack

| Layer | Library |
|---|---|
| Web framework | FastAPI |
| Validation | Pydantic v2 |
| Config | pydantic-settings |
| ORM | SQLAlchemy (async) |
| Driver | psycopg (psycopg3) |
| Server | Uvicorn |
| PDF generation | ReportLab |
| Object storage | boto3 (S3-compatible / Cloudflare R2) |
| Observability | OpenTelemetry |
| Python | ≥ 3.12 |

## Getting started

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in `DATA_SOURCE_NAME` (Postgres DSN) and the `S3_*` variables (required — the server will not start without a reachable S3/R2 bucket).

| Variable | Required | Description |
|---|---|---|
| `DATA_SOURCE_NAME` | Yes | `host=... user=... password=... dbname=... port=... sslmode=...` |
| `TEST_DATA_SOURCE_NAME` | Tests only | Separate blank DB for the test suite |
| `CORS_ORIGINS` | No | Comma-separated origins (default `http://localhost:3000`) |
| `OTEL_ENDPOINT` | No | OTLP/HTTP trace endpoint; omit to disable |
| `S3_ENDPOINT` | Yes | e.g. `http://localhost:9000` (MinIO) or Cloudflare R2 URL |
| `S3_BUCKET` | Yes | Bucket for generated PDFs |
| `S3_ACCESS_KEY` | Yes | |
| `S3_SECRET_KEY` | Yes | |
| `S3_REGION` | No | Default `auto` |
| `REPORT_WORKER_MAX_THREADS` | No | CPU processes for PDF generation (default `2`) |
| `REPORT_WORKER_QUEUE_MAX_SIZE` | No | Max queued jobs before 503 (default `50`) |

### 3. Apply schema and seed data

```bash
psql $DATABASE_URL -f migrations/001_initial_schema.up.sql
psql $DATABASE_URL -f sql_mock/900_seed_samples.up.sql
psql $DATABASE_URL -f sql_mock/901_seed_experiment_templates.up.sql
psql $DATABASE_URL -f sql_mock/902_seed_heat_capacity_template.up.sql
psql $DATABASE_URL -f sql_mock/903_seed_charcoal_template.up.sql
```

### 4. Run the server

```bash
uv run uvicorn main:app --reload --port 3000
```

Interactive docs: http://localhost:3000/docs

### 5. Run tests

```bash
uv run pytest -v
```

Requires `TEST_DATA_SOURCE_NAME` in `.env`. The test suite creates its own schema and rolls back after each test.

## API

### Sample types

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/samples` | Create a sample type |
| `GET` | `/api/samples` | List all sample types |
| `GET` | `/api/samples/{sample_id}` | Get one |
| `PUT` | `/api/samples/{sample_id}` | Update name/description |
| `DELETE` | `/api/samples/{sample_id}` | Soft delete |

### Analysis templates (nested under sample)

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/samples/{sample_id}/experiments` | Create a template |
| `GET` | `/api/samples/{sample_id}/experiments` | List templates for a sample |
| `GET` | `/api/samples/{sample_id}/experiments/{template_id}` | Get one template |
| `PUT` | `/api/samples/{sample_id}/experiments/{template_id}` | Update template |
| `DELETE` | `/api/samples/{sample_id}/experiments/{template_id}` | Soft delete |

### Experiments

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/experiments` | Create an experiment — initialises state from the template |
| `GET` | `/api/experiments` | List experiments (summary) |
| `GET` | `/api/experiments/{exp_id}` | Full experiment detail |
| `PUT` | `/api/experiments/{exp_id}` | Update experiment state (worker fills in measured values) |
| `DELETE` | `/api/experiments/{exp_id}` | Soft delete |

### PDF reports

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/experiments/{exp_id}/report/generate` | Enqueue PDF generation → 202 `{ "status": "pending" }` |
| `GET` | `/api/experiments/{exp_id}/report/download` | Get presigned download URL → `{ "url": "...", "expires_in": 900 }` |

## Data model

An experiment's state is a flat JSON blob stored in Postgres. At creation it mirrors the template:

```json
{
  "id": "exp-uuid",
  "sample_id": "uuid",
  "template_id": "uuid",
  "title": "Heat Capacity Analysis",
  "description": "...",
  "workerForm": { "title": "...", "questions": [ ... ] },
  "calculations": { "delta_T": "temperature_final - temperature_initial" },
  "template": "ΔT = {{delta_T}} °C"
}
```

On `PUT` the worker sends the same blob back with `"value"` filled into each question. `id`, `sample_id`, and `template_id` are immutable — the service overwrites any values the client sends for those fields.

`GET /api/experiments/{exp_id}` returns this blob merged with report tracking fields: `report_status`, `report_r2_key`, `report_generated_at`, `created_at`.

## Code style

```bash
uv run black .
uv run isort .
```
