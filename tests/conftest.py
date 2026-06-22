import os
import uuid
from collections.abc import AsyncGenerator

os.environ["OTEL_ENDPOINT"] = ""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (AsyncSession, async_sessionmaker,
                                    create_async_engine)

from app.config import settings
from app.database import get_db
from app.db_models import Base, ExperimentTemplate, SampleType
from main import app

# Fixed IDs shared across all tests — must match seed_catalogue fixture below
COAL_ID = uuid.UUID("a1b2c3d4-0002-0002-0002-000000000002")
TOMATO_ID = uuid.UUID("a1b2c3d4-0001-0001-0001-000000000001")
PROXIMATE_TEMPLATE_ID = uuid.UUID("b2c3d4e5-0001-0001-0001-000000000001")
CALORIFIC_TEMPLATE_ID = uuid.UUID("b2c3d4e5-0002-0002-0002-000000000002")
DIVISOR_TEMPLATE_ID = uuid.UUID("b2c3d4e5-0003-0003-0003-000000000003")


@pytest.fixture(scope="session")
def require_test_db() -> None:
    if not settings.test_data_source_name:
        pytest.skip("TEST_DATA_SOURCE_NAME not set in .env — skipping tests")


@pytest.fixture(scope="session")
async def test_engine(require_test_db):
    url = settings.test_database_url
    assert url, "TEST_DATA_SOURCE_NAME not set"
    engine = create_async_engine(url, echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest.fixture(scope="session")
async def seed_catalogue(test_engine):
    """Insert sample types and templates once for the whole test session."""
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with factory() as session:
        session.add_all(
            [
                SampleType(id=COAL_ID, name="Coal", description="Coal samples"),
                SampleType(id=TOMATO_ID, name="Tomato", description="Tomato samples"),
            ]
        )
        await session.flush()
        session.add_all(
            [
                ExperimentTemplate(
                    id=PROXIMATE_TEMPLATE_ID,
                    lineage_id=PROXIMATE_TEMPLATE_ID,
                    sample_type_id=COAL_ID,
                    name="Proximate Analysis",
                    description="Determine moisture, ash, volatile matter, and fixed carbon",
                    version=1,
                    is_current=True,
                    template={
                        "clientForm": {"name": "Client", "questions": []},
                        "labForm": {"name": "Proximate Form", "questions": []},
                        "calculations": {
                            "result": {
                                "formula": "values['value'] * 100",
                                "result": "",
                            }
                        },
                    },
                ),
                ExperimentTemplate(
                    id=CALORIFIC_TEMPLATE_ID,
                    lineage_id=CALORIFIC_TEMPLATE_ID,
                    sample_type_id=COAL_ID,
                    name="Calorific Value",
                    description="Determine gross calorific value",
                    version=1,
                    is_current=True,
                    template={
                        "clientForm": {"name": "Client", "questions": []},
                        "labForm": {"name": "Calorific Form", "questions": []},
                        "calculations": {
                            "gcv": {
                                "formula": "values['value'] * 4.1868",
                                "result": "",
                            }
                        },
                    },
                ),
                ExperimentTemplate(
                    id=DIVISOR_TEMPLATE_ID,
                    lineage_id=DIVISOR_TEMPLATE_ID,
                    sample_type_id=COAL_ID,
                    name="Divisor Check",
                    description="Template whose only calculation divides by a worker-supplied value",
                    version=1,
                    is_current=True,
                    template={
                        "clientForm": {"name": "Client", "questions": []},
                        "labForm": {"name": "Form", "questions": []},
                        "calculations": {
                            "bad": {
                                "formula": "1 / values['value']",
                                "result": "",
                            }
                        },
                    },
                ),
            ]
        )
        await session.commit()


@pytest.fixture
async def client(test_engine, seed_catalogue) -> AsyncGenerator[AsyncClient, None]:
    """Per-test AsyncClient. All DB writes are rolled back after each test."""
    async with test_engine.connect() as conn:
        await conn.begin()

        session_factory = async_sessionmaker(
            conn,
            class_=AsyncSession,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        async def _override_get_db():
            async with session_factory() as session:
                yield session

        app.dependency_overrides[get_db] = _override_get_db

        async with AsyncClient(
            transport=ASGITransport(app=app), base_url="http://test"
        ) as ac:
            yield ac

        app.dependency_overrides.pop(get_db, None)
        await conn.rollback()
