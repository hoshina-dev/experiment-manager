"""CRUD router for experiments, mounted at /api/experiments."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

import app.services.experiment_service as service
from app.database import get_db
from app.models import (ExperimentCreate, ExperimentDetail,
                        ExperimentsListResponse, ExperimentUpdate)

router = APIRouter(prefix="/api/experiments", tags=["experiments"])

DbDep = Annotated[AsyncSession, Depends(get_db)]


@router.post("", response_model=ExperimentDetail, status_code=201)
async def create_experiment(body: ExperimentCreate, db: DbDep) -> ExperimentDetail:
    return await service.create_experiment(db, body)


@router.get("", response_model=ExperimentsListResponse)
async def list_experiments(db: DbDep) -> ExperimentsListResponse:
    return await service.list_experiments(db)


@router.get("/{exp_id}", response_model=ExperimentDetail)
async def get_experiment(exp_id: uuid.UUID, db: DbDep) -> ExperimentDetail:
    result = await service.get_experiment(db, exp_id)
    if result is None:
        raise HTTPException(404, f'Experiment "{exp_id}" not found')
    return result


@router.put("/{exp_id}", response_model=ExperimentDetail)
async def update_experiment(
    exp_id: uuid.UUID, body: ExperimentUpdate, db: DbDep
) -> ExperimentDetail:
    result = await service.update_experiment(db, exp_id, body)
    if result is None:
        raise HTTPException(404, f'Experiment "{exp_id}" not found')
    return result


@router.delete("/{exp_id}", status_code=204)
async def delete_experiment(exp_id: uuid.UUID, db: DbDep) -> None:
    if not await service.delete_experiment(db, exp_id):
        raise HTTPException(404, f'Experiment "{exp_id}" not found')
