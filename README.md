# Experiment Manager

A FastAPI service that stores and serves **lab analysis templates** for experiment management. Clients request which analyses they want for a sample; the service returns the composed JSON form containing worker forms, calculation expressions, and output templates.

## Overview

Each **sample type** (e.g. tomato, coal, environment water) has a set of **analysis templates**. A template contains:
- `workerForm` — the fields a lab worker fills in
- `calculations` — named expressions (JS syntax, evaluated by the frontend)
- `template` — output string with `{{variable}}` placeholders

The service is read-only — it serves templates, not experiment results.

## Tech stack

| Layer | Library |
|---|---|
| Web framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Validation | [Pydantic v2](https://docs.pydantic.dev/) |
| Config | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| Server | [Uvicorn](https://www.uvicorn.org/) |
| Observability | [OpenTelemetry](https://opentelemetry.io/) |
| Python | ≥ 3.12 |

## Project structure

```
main.py                        # App factory (CORS, OTEL, routers, lifespan)
data/                          # Mock catalogue data (JSON) — mirrors future SQL schema
  samples.json
  {sample_id}/
    {analysis_id}.json
app/
  config.py                    # Settings from env / .env
  database.py                  # SQLite connection factory + schema bootstrap
  models.py                    # Pydantic models (request + response)
  observability/
    telemetry.py               # OTEL TracerProvider setup
  routers/
    samples.py                 # /api/samples (catalogue, read-only)
    experiments.py             # /api/experiments (CRUD)
  services/
    sample_service.py          # Catalogue business logic + OTEL spans
    experiment_service.py      # Experiment business logic + OTEL spans
  repositories/
    sample_repository.py       # Reads JSON files from data/
    experiment_repository.py   # SQLite CRUD for experiments
tests/
  conftest.py                  # Shared client fixture + test env overrides
  test_samples.py
  test_experiments.py
```

## Getting started

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
```

| Variable | Default | Description |
|---|---|---|
| `APP_CORS_ORIGIN` | `http://localhost:3000` | Allowed CORS origin |
| `APP_OTEL_ENDPOINT` | _(none)_ | OTLP/HTTP trace endpoint; omit to print spans to stdout |
| `APP_DB_PATH` | `experiments.db` | Path to the SQLite file for experiment storage |

### 3. Run the server

```bash
make serve
```

API docs:

- Swagger UI: [http://localhost:3000/docs](http://localhost:3000/docs)
- Scalar UI: [http://localhost:3000/scalar](http://localhost:3000/scalar)

## API

**Catalogue (read-only)**

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/samples` | List all sample types |
| `GET` | `/api/samples/{sample_id}/analyses` | List available analyses for a sample (checklist) |

**Experiments (CRUD)**

| Method | Path | Description |
|---|---|---|
| `POST` | `/api/experiments` | Create an experiment — snapshots selected templates, returns `exp_id` + full form |
| `GET` | `/api/experiments` | List all experiments (summary, no form) |
| `GET` | `/api/experiments/{exp_id}` | Get full experiment detail including form snapshot |
| `PUT` | `/api/experiments/{exp_id}` | Update requested analyses and regenerate form snapshot |
| `DELETE` | `/api/experiments/{exp_id}` | Delete an experiment |

POST / PUT body:
```json
{ "sample_id": "coal", "requested_analyses": ["calorific", "proximate"] }
```

Unknown analysis IDs are silently ignored. `sample_id` cannot change on PUT.

## Development

```bash
make test       # run pytest
make lint       # black + isort check
make format     # black + isort fix
```
