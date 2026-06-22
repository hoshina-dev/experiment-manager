"""Proves get_current_template_by_lineage(lock=True) takes a real Postgres
row lock — this is what closes the race between editing a template in place
and creating an experiment against it concurrently (see
app/services/sample_service.py::update_experiment_template and
app/services/experiment_service.py::create_experiment, both of which read
the template via this function before deciding what to write)."""

import pytest
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.repositories import sample_repository as repo
from tests.conftest import COAL_ID, PROXIMATE_TEMPLATE_ID


async def test_locked_read_blocks_a_concurrent_locked_read_on_the_same_row(
    test_engine, seed_catalogue
):
    factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async with factory() as session_a:
        await session_a.begin()
        await repo.get_current_template_by_lineage(
            session_a, COAL_ID, PROXIMATE_TEMPLATE_ID, lock=True
        )

        async with factory() as session_b:
            await session_b.begin()
            await session_b.execute(text("SET LOCAL lock_timeout = '200ms'"))
            try:
                with pytest.raises(OperationalError, match="lock"):
                    await repo.get_current_template_by_lineage(
                        session_b, COAL_ID, PROXIMATE_TEMPLATE_ID, lock=True
                    )
            finally:
                await session_b.rollback()

        await session_a.rollback()


async def test_unlocked_read_does_not_block_a_concurrent_locked_read(
    test_engine, seed_catalogue
):
    """Sanity check: the default (lock=False) path used by plain GETs must
    not start serializing against everything else."""
    factory = async_sessionmaker(test_engine, expire_on_commit=False)

    async with factory() as session_a:
        await session_a.begin()
        await repo.get_current_template_by_lineage(
            session_a, COAL_ID, PROXIMATE_TEMPLATE_ID, lock=False
        )

        async with factory() as session_b:
            await session_b.begin()
            await session_b.execute(text("SET LOCAL lock_timeout = '200ms'"))
            row = await repo.get_current_template_by_lineage(
                session_b, COAL_ID, PROXIMATE_TEMPLATE_ID, lock=False
            )
            assert row is not None
            await session_b.rollback()

        await session_a.rollback()


import pytest  # noqa: E402
