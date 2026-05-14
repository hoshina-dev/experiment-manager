# Experiment Manager — PoC

A lightweight FastAPI proof-of-concept that stores and serves **experiment form configurations** backed by a local SQLite database.

## Overview

Forms capture the full definition of an experiment: a user-facing form, a worker-facing form, a set of named calculation expressions, and a template string. The API lets a front-end create, retrieve, update, and delete these configurations with no external database required.

## Tech stack

| Layer | Library |
|---|---|
| Web framework | [FastAPI](https://fastapi.tiangolo.com/) |
| Validation | [Pydantic v2](https://docs.pydantic.dev/) |
| Config | [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/) |
| Server | [Uvicorn](https://www.uvicorn.org/) |
| Database | SQLite (stdlib `sqlite3`) |
| Python | ≥ 3.12 |

## Project structure

```
experiment-manager-poc/
├── app/
│   ├── config.py      # Settings loaded from env / .env
│   ├── database.py    # Connection factory + schema bootstrap
│   ├── models.py      # Pydantic models
│   └── routers/
│       └── forms.py   # CRUD endpoints at /api/forms
├── main.py            # App factory (CORS, lifespan, routers)
├── pyproject.toml
└── .env.example
```

## Getting started

### 1. Install dependencies

```bash
uv sync
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env if you need a different DB path or CORS origin
```

| Variable | Default | Description |
|---|---|---|
| `APP_DB_PATH` | `data.db` | Path to the SQLite file |
| `APP_CORS_ORIGIN` | `http://localhost:3000` | Single allowed CORS origin |

### 3. Run the server

```bash
make serve          # uv run uvicorn main:app --reload --port 8000
```

The interactive docs are available at [http://localhost:8000/docs](http://localhost:8000/docs).

## API

All endpoints are under `/api/forms`.

| Method | Path | Description |
|---|---|---|
| `GET` | `/api/forms` | List all forms (id, title, description) |
| `POST` | `/api/forms` | Create a new form — returns `{"id": "..."}` |
| `GET` | `/api/forms/{id}` | Fetch the full payload for a single form |
| `PUT` | `/api/forms/{id}` | Upsert (create or fully replace) a form |
| `DELETE` | `/api/forms/{id}` | Delete a form |

### Form payload shape

```json
{
  "id": "my-experiment",
  "title": "My Experiment",
  "description": "Optional description",
  "userForm": { "field": "value" },
  "workerForm": { "field": "value" },
  "calculations": { "result": "userForm.x + workerForm.y" },
  "template": "Result: {{result}}"
}
```

## Development

```bash
make clean          # remove data.db
```

Formatting uses **black** and **isort** (both in the `dev` dependency group).
