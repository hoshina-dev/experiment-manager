"""Business logic for experiments, with OTEL spans on every operation."""

import sqlite3
import uuid

import app.repositories.experiment_repository as experiment_repo
import app.repositories.sample_repository as sample_repo
from app.models import ExperimentCreate, ExperimentDetail, ExperimentsListResponse
from opentelemetry import trace

tracer = trace.get_tracer(__name__)


def create_experiment(conn: sqlite3.Connection, body: ExperimentCreate) -> ExperimentDetail | None:
    with tracer.start_as_current_span("experiment_service.create") as span:
        span.set_attribute("sample.id", body.sample_id)

        if sample_repo.get_sample(body.sample_id) is None:
            return None

        form_snapshot = [
            t for aid in body.requested_analyses
            if (t := sample_repo.get_analysis(body.sample_id, aid)) is not None
        ]

        exp_id = str(uuid.uuid4())
        span.set_attribute("experiment.id", exp_id)

        summary = experiment_repo.create(conn, exp_id, body.sample_id, body.requested_analyses, form_snapshot)
        return ExperimentDetail(
            exp_id=summary.exp_id,
            sample_id=summary.sample_id,
            requested_analyses=summary.requested_analyses,
            form=form_snapshot,
            created_at=summary.created_at,
        )


def list_experiments(conn: sqlite3.Connection) -> ExperimentsListResponse:
    with tracer.start_as_current_span("experiment_service.list"):
        return ExperimentsListResponse(experiments=experiment_repo.list_all(conn))


def get_experiment(conn: sqlite3.Connection, exp_id: str) -> ExperimentDetail | None:
    with tracer.start_as_current_span("experiment_service.get") as span:
        span.set_attribute("experiment.id", exp_id)
        return experiment_repo.get(conn, exp_id)


def update_experiment(
    conn: sqlite3.Connection, exp_id: str, body: ExperimentCreate
) -> ExperimentDetail | None:
    with tracer.start_as_current_span("experiment_service.update") as span:
        span.set_attribute("experiment.id", exp_id)

        existing = experiment_repo.get(conn, exp_id)
        if existing is None:
            return None

        form_snapshot = [
            t for aid in body.requested_analyses
            if (t := sample_repo.get_analysis(existing.sample_id, aid)) is not None
        ]

        summary = experiment_repo.update(conn, exp_id, body.requested_analyses, form_snapshot)
        if summary is None:
            return None
        return ExperimentDetail(
            exp_id=summary.exp_id,
            sample_id=summary.sample_id,
            requested_analyses=summary.requested_analyses,
            form=form_snapshot,
            created_at=summary.created_at,
        )


def delete_experiment(conn: sqlite3.Connection, exp_id: str) -> bool:
    with tracer.start_as_current_span("experiment_service.delete") as span:
        span.set_attribute("experiment.id", exp_id)
        return experiment_repo.delete(conn, exp_id)
