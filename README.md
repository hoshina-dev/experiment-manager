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

Fill in `DATA_SOURCE_NAME` (Postgres DSN) and the `S3_*` variables (required — the server will not start without a reachable S3/R2 bucket). `S3_PUBLIC_URL` is optional and can point at CloudFront or another public CDN for customer downloads.

| Variable | Required | Description |
|---|---|---|
| `DATA_SOURCE_NAME` | Yes | `host=... user=... password=... dbname=... port=... sslmode=...` |
| `TEST_DATA_SOURCE_NAME` | Tests only | Separate blank DB for the test suite |
| `CORS_ORIGINS` | No | Comma-separated origins (default `http://localhost:3000`) |
| `OTEL_ENABLED` | No | Set to `true` to export traces and metrics |
| `OTEL_SERVICE_NAME` | No | Service name reported to OpenTelemetry (default `experiment-manager`) |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | No | OTLP/gRPC endpoint (default `http://localhost:4317` when OTEL is enabled) |
| `S3_ENDPOINT` | Yes | e.g. `http://localhost:9000` (MinIO) or Cloudflare R2 URL |
| `S3_BUCKET` | Yes | Bucket for generated PDFs |
| `S3_ACCESS_KEY` | Yes | |
| `S3_SECRET_KEY` | Yes | |
| `S3_REGION` | No | Default `auto` |
| `S3_PUBLIC_URL` | No | Optional public base URL for CloudFront/CDN delivery |
| `REPORT_WORKER_MAX_THREADS` | No | CPU processes for PDF generation (default `2`) |
| `REPORT_WORKER_QUEUE_MAX_SIZE` | No | Max queued jobs before 503 (default `50`) |

### 3. Apply schema and seed data

```bash
psql $DATABASE_URL -f migrations/001_initial_schema.up.sql
psql $DATABASE_URL -f migrations/002_partial_unique_indexes.up.sql
psql $DATABASE_URL -f migrations/003_report_initial_schema.up.sql
psql $DATABASE_URL -f migrations/004_experiment_report_fields.up.sql
psql $DATABASE_URL -f migrations/005_scd2_experiment_templates.up.sql
psql $DATABASE_URL -f migrations/006_experiment_templates_lineage_id_default.up.sql
psql $DATABASE_URL -f migrations/007_drop_stale_template_name_index.up.sql
psql $DATABASE_URL -f sql_mock/900_seed_samples.up.sql
psql $DATABASE_URL -f sql_mock/901_seed_experiment_templates.up.sql
psql $DATABASE_URL -f sql_mock/902_seed_coal_heat_capacity_experiment_template.up.sql
psql $DATABASE_URL -f sql_mock/903_seed_coal_calorific_value_experiment_template.up.sql
psql $DATABASE_URL -f sql_mock/904_seed_coal_heat_capacity_pdf_template.up.sql
psql $DATABASE_URL -f sql_mock/905_seed_coal_calorific_value_pdf_template.up.sql
psql $DATABASE_URL -f sql_mock/906_seed_coal_heat_capacity_experiment.up.sql
psql $DATABASE_URL -f sql_mock/907_seed_coal_calorific_value_experiment.up.sql
psql $DATABASE_URL -f sql_mock/908_seed_tomato_analysis_experiment_template.up.sql
psql $DATABASE_URL -f sql_mock/909_seed_tomato_analysis_pdf_template.up.sql
```

Template JSON in `sql_mock/` follows the form-poc schema-bundle: `clientForm`, `labForm`, `calculations` (with `{ formula, result? }`), nested question `config`. Experiment snapshots add top-level `values` and metadata (`name`, `description` from DB columns).

### 4. Run the server

```bash
uv run uvicorn main:app --reload --port 3000
```

API docs:

- Swagger UI: [http://localhost:3000/docs](http://localhost:3000/docs)
- Scalar UI: [http://localhost:3000/scalar](http://localhost:3000/scalar)

### Observability stack

```bash
make observability-up
make observability-load
```

This starts Postgres, MinIO, the experiment-manager API, an OTel Collector,
Jaeger, Prometheus, and Grafana. The app exports OTLP/gRPC to the collector,
with traces visible at [http://localhost:16686](http://localhost:16686) and
Prometheus at [http://localhost:9090](http://localhost:9090). The k6 load
target creates synthetic experiment traffic against the running stack.

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

## Localization

PDF reports default to the **Noto Sans** font (`app/fonts/`, registered in
`app/pdf/fonts.py`), which covers Latin Extended, Greek, and Cyrillic in a
single embedded font. This means report text in any EU language — including
ones with diacritics (Polish, Czech, Romanian, Lithuanian...), Greek, or
Bulgarian Cyrillic — renders correctly without per-template font juggling.
Templates can still opt into ReportLab's built-in `Helvetica`, `Times-Roman`,
or `Courier` for ASCII-only content (see `docs/pdf-report-engine.md`).

This covers **rendering** multilingual text, not full UI/string
translation. There is currently no locale storage, no translated string
resources, and no locale-aware date/number formatting — building that out
(if ever needed) is a separate, larger effort tracked as future work, not
implemented here.

## Data model

An experiment's state is a flat JSON blob stored in Postgres. At creation it mirrors the template:

```json
{
  "id": "exp-uuid",
  "sample_id": "uuid",
  "template_id": "uuid",
  "name": "Heat Capacity Analysis",
  "description": "...",
  "clientForm": { "name": "...", "questions": [ ... ] },
  "labForm": { "name": "...", "questions": [ ... ] },
  "calculations": { "delta_T": { "formula": "values['temperature_final'] - values['temperature_initial']" } },
  "values": { "temperature_final": 30.17, "temperature_initial": 24.82 }
}
```

On `PUT` the worker sends `clientForm`, `labForm`, `calculations`, and `values`. Frozen metadata (`id`, `sample_id`, `template_id`, `lineage_id`, `name`, `description`) is preserved server-side.

`GET /api/experiments/{exp_id}` returns this blob merged with report tracking fields: `report_status`, `report_r2_key`, `report_generated_at`, `created_at`.

## Code style

```bash
uv run black .
uv run isort .
```
