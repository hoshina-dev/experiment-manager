"""CRUD router for experiments, mounted at /api/experiments."""

from typing import Annotated

import sqlite3
from fastapi import APIRouter, Depends, HTTPException

import app.services.experiment_service as service
from app.database import get_connection
from app.models import ExperimentCreate, ExperimentDetail, ExperimentsListResponse

router = APIRouter(prefix="/api/experiments", tags=["experiments"])

ConnDep = Annotated[sqlite3.Connection, Depends(get_connection)]


@router.post("", response_model=ExperimentDetail, status_code=201)
def create_experiment(body: ExperimentCreate, conn: ConnDep) -> ExperimentDetail:
    """Create an experiment from a sample + selected analyses.

    Snapshots the full analysis templates at creation time so the form sent
    to the lab is preserved even if templates change later.
    """
    result = service.create_experiment(conn, body)
    if result is None:
        raise HTTPException(404, f'Sample "{body.sample_id}" not found')
    return result


@router.get("", response_model=ExperimentsListResponse)
def list_experiments(conn: ConnDep) -> ExperimentsListResponse:
    """Return a summary list of all experiments, newest first."""
    return service.list_experiments(conn)


@router.get("/{exp_id}", response_model=ExperimentDetail)
def get_experiment(exp_id: str, conn: ConnDep) -> ExperimentDetail:
    """Return the full experiment detail including the form snapshot."""
    result = service.get_experiment(conn, exp_id)
    if result is None:
        raise HTTPException(404, f'Experiment "{exp_id}" not found')
    return result


@router.put("/{exp_id}", response_model=ExperimentDetail)
def update_experiment(exp_id: str, body: ExperimentCreate, conn: ConnDep) -> ExperimentDetail:
    """Replace the requested analyses for an experiment and regenerate the form snapshot.

    The sample_id cannot change — only requested_analyses is updated.
    """
    result = service.update_experiment(conn, exp_id, body)
    if result is None:
        raise HTTPException(404, f'Experiment "{exp_id}" not found')
    return result


@router.delete("/{exp_id}", status_code=204)
def delete_experiment(exp_id: str, conn: ConnDep) -> None:
    """Delete an experiment by ID."""
    if not service.delete_experiment(conn, exp_id):
        raise HTTPException(404, f'Experiment "{exp_id}" not found')
