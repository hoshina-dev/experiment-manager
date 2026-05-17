# AGENTS.md — Experiment Manager

This file tells AI coding agents how to work in this repository.
Read it before writing any code.

---

## What this service does

Experiment Manager is a **read-only form-template service**.
It stores analysis templates for lab experiments and serves them as structured JSON so a frontend can render a checklist and a worker form.

Key concepts:

| Term | Meaning |
|---|---|
| **Sample** | A type of material being analysed (e.g. `tomato`, `coal`, `environment_water`) |
| **Analysis** | A specific test that can be run on a sample (e.g. `moisture`, `ph`) |
| **AnalysisTemplate** | The JSON payload for one analysis: `workerForm`, `calculations`, `template` |
| **Form** | A composed response containing one or more AnalysisTemplates for a client's request |

The client (frontend) selects which analyses to request via `POST /api/samples/{sample_id}/analyses/form`.
The service returns the matching templates; it **never** tells the client which analyses are available to pick — that is the client's responsibility via `GET .../analyses`.

---

## Architecture

```
main.py                            # FastAPI app factory + OTEL init
data/                              # Mock data — mirrors the future SQL schema
  samples.json                     # List of all sample types
  {sample_id}/
    {analysis_id}.json             # One file per analysis template
app/
  config.py                        # Pydantic Settings (env vars)
  models.py                        # All Pydantic request/response models
  observability/
    telemetry.py                   # OTEL TracerProvider setup
  routers/
    samples.py                     # HTTP layer — thin, no business logic
  services/
    sample_service.py              # Business logic — every public fn has an OTEL span
  repositories/
    sample_repository.py           # Data access — reads JSON files from data/
tests/
  test_samples.py
```

Layer rules (enforce strictly):
- **Routers** only call services. No direct repo access, no business logic.
- **Services** only call repositories. They own OTEL spans and 404-logic.
- **Repositories** only read files. No HTTP concerns, no span creation.

---

## Endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/samples` | List all sample types |
| `GET` | `/api/samples/{sample_id}/analyses` | List available analyses for a sample |
| `POST` | `/api/samples/{sample_id}/analyses/form` | Return composed templates for requested analyses |

Request body for the POST:
```json
{ "requested_analyses": ["moisture", "sulfur"] }
```

Unknown analysis IDs in the request are **silently ignored** (not an error).

---

## Analysis template JSON schema

Every file under `data/{sample_id}/` must follow this shape:

```json
{
  "id": "snake_case_string",
  "label": "Human readable name",
  "description": "Optional one-liner",
  "workerForm": {
    "title": "Optional form title",
    "description": "Optional",
    "questions": [
      {
        "id": "field_name",
        "label": "Display label",
        "required": true,
        "type": "number | text | select-number"
      }
    ]
  },
  "calculations": {
    "result_var": "js-style expression referencing question ids"
  },
  "template": "Output string with {{result_var}} placeholders"
}
```

Rules:
- **No `userForm` field** — the client decides which analyses to request via POST body.
- `calculations` expressions use JavaScript syntax (evaluated by the frontend).
- `template` uses `{{variable}}` syntax where variables come from `calculations` keys.
- `id` must be unique within a sample directory and must match the filename (without `.json`).

---

## Conventions — required for every change

### New analysis template
1. Add a JSON file to `data/{sample_id}/` following the schema above.
2. No code changes needed — the repository auto-discovers files via glob.
3. Add at least one test asserting the new analysis ID appears in `GET .../analyses`.

### New endpoint
1. Add the route to the appropriate router (or create a new router file).
2. Add a service function with an OTEL span wrapping every logical operation:
   ```python
   with tracer.start_as_current_span("service_name.operation_name") as span:
       span.set_attribute("key", value)
   ```
3. Add a repository function if new data access is needed.
4. Write tests covering: happy path, 404/error cases, response shape.
5. Tests live in `tests/` and use `fastapi.testclient.TestClient` (sync, no asyncio needed).

### New sample type
1. Add an entry to `data/samples.json`.
2. Create `data/{sample_id}/` with at least one analysis JSON file.
3. Add tests for the new sample.

### OTEL span naming convention
```
{module_short_name}.{operation}
# examples:
sample_service.get_samples
sample_service.build_form
```
Set relevant attributes on the span (e.g. `sample.id`, `requested_analyses`).

---

## Running the project

```bash
# Install dependencies
uv sync

# Start dev server (hot reload)
make serve

# Run tests
make test

# Export requirements.txt (for Docker / CI)
make requirements
```

Environment variables (see `.env.example`):

| Variable | Default | Description |
|---|---|---|
| `APP_CORS_ORIGIN` | `http://localhost:3000` | Allowed CORS origin |
| `APP_OTEL_ENDPOINT` | _(none)_ | OTLP/HTTP endpoint; omit to log spans to stdout |

---

## Code style

- Formatter: **black** (`uv run black .`)
- Import sort: **isort** (`uv run isort .`)
- No inline comments unless the WHY is non-obvious.
- No docstrings on trivial functions.
- Pydantic models go in `app/models.py`; do not scatter them across files.
