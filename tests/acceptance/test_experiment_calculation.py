"""Cucumber steps for the ticket-to-calculation acceptance journey."""

import asyncio
import uuid
from collections.abc import Generator
from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pytest_bdd import given, parsers, scenarios, then, when
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.config import settings
from app.database import get_db
from main import app
from tests.conftest import COAL_ID, PROXIMATE_TEMPLATE_ID

scenarios("features/experiment_calculation.feature")

pytestmark = pytest.mark.acceptance


@dataclass
class ApiWorld:
    client: TestClient
    exp_id: uuid.UUID = field(default_factory=uuid.uuid4)
    created_context: dict[str, Any] | None = None


@pytest.fixture
def api_world(seed_catalogue) -> Generator[ApiWorld, None, None]:
    assert settings.test_database_url
    acceptance_engine = create_async_engine(
        settings.test_database_url, echo=False, poolclass=NullPool
    )
    session_factory = async_sessionmaker(acceptance_engine, expire_on_commit=False)

    async def _override_get_db():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = _override_get_db
    client = TestClient(app)
    try:
        yield ApiWorld(client=client)
    finally:
        client.close()
        app.dependency_overrides.pop(get_db, None)
        asyncio.run(acceptance_engine.dispose())


@given("a ticket selects the current Proximate Analysis template for Coal")
def ticket_selects_template(api_world: ApiWorld) -> None:
    assert api_world.exp_id


@when("Ticketing Service creates the experiment")
def create_experiment(api_world: ApiWorld) -> None:
    response = api_world.client.post(
        "/api/experiments",
        json={
            "exp_id": str(api_world.exp_id),
            "sample_id": str(COAL_ID),
            "lineage_id": str(PROXIMATE_TEMPLATE_ID),
        },
    )
    assert response.status_code == 201, response.text
    api_world.created_context = response.json()


@then("the API returns the canonical experiment context")
def canonical_context_is_returned(api_world: ApiWorld) -> None:
    assert api_world.created_context is not None
    assert api_world.created_context["id"] == str(api_world.exp_id)
    assert api_world.created_context["sample_id"] == str(COAL_ID)
    assert api_world.created_context["template_id"] == str(PROXIMATE_TEMPLATE_ID)
    assert api_world.created_context["name"] == "Proximate Analysis"


@when(parsers.parse("the lab worker submits a measurement value of {value:g}"))
def submit_measurement(api_world: ApiWorld, value: float) -> None:
    assert api_world.created_context is not None
    response = api_world.client.put(
        f"/api/experiments/{api_world.exp_id}",
        json={
            "clientForm": api_world.created_context["clientForm"],
            "labForm": api_world.created_context["labForm"],
            "calculations": api_world.created_context["calculations"],
            "values": {"value": value},
        },
    )
    assert response.status_code == 200, response.text


@when("the lab worker requests the calculation")
def request_calculation(api_world: ApiWorld) -> None:
    response = api_world.client.post(f"/api/experiments/{api_world.exp_id}/calculate")
    assert response.status_code == 200, response.text


@then(parsers.parse("the public experiment context reports a result of {result:g}"))
def result_is_persisted(api_world: ApiWorld, result: float) -> None:
    response = api_world.client.get(f"/api/experiments/{api_world.exp_id}")
    assert response.status_code == 200, response.text
    context = response.json()
    assert context["calculations"]["result"]["result"] == result
    assert context["template_id"] == str(PROXIMATE_TEMPLATE_ID)
