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
main.py                        # App factory (CORS, OTEL, routers)
data/                          # Mock data (JSON) — mirrors future SQL schema
  samples.json
  {sample_id}/
    {analysis_id}.json
app/
  config.py                    # Settings from env / .env
  models.py                    # Pydantic models (request + response)
  observability/
    telemetry.py               # OTEL TracerProvider setup
  routers/
    samples.py                 # HTTP layer — /api/samples
  services/
    sample_service.py          # Business logic + OTEL spans
  repositories/
    sample_repository.py       # Data access (reads JSON files from data/)
tests/
  test_samples.py
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

### 3. Run the server

```bash
make serve
```

Interactive docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/samples` | List all sample types |
| `GET` | `/api/samples/{sample_id}/analyses` | List available analyses for a sample |
| `POST` | `/api/samples/{sample_id}/analyses/form` | Return composed analysis templates |

POST body:
```json
{ "requested_analyses": ["moisture", "sulfur"] }
```

Unknown analysis IDs in the request are silently ignored.

## Development

```bash
make test       # run pytest
make lint       # black + isort check
make format     # black + isort fix
```
