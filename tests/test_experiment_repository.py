"""Tests for app/repositories/experiment_repository.py report-status writers."""

import uuid

from sqlalchemy.ext.asyncio import async_sessionmaker

from app.repositories import experiment_repository as repo


async def test_update_report_failure_clears_stale_report_r2_key(
    test_engine, seed_catalogue
):
    """A failed regeneration must not leave report/download still serving
    the PDF from a *previous* successful generation — that PDF reflects
    whatever data/template was true before, not now. Clearing the key makes
    `report_status: "failed"` and "no report available" agree instead of
    contradicting each other.
    """
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    exp_id = uuid.uuid4()

    async with factory() as session:
        await session.begin()
        await repo.create(session, exp_id, {"id": str(exp_id), "name": "T"})
        await repo.update_report_success(session, exp_id, "pdfs/old-key.pdf")

        row = await repo.get(session, exp_id)
        assert row.report_r2_key == "pdfs/old-key.pdf"

        await repo.update_report_failure(session, exp_id, "boom")

        row = await repo.get(session, exp_id)
        assert row.report_status == "failed"
        assert row.report_error == "boom"
        assert row.report_r2_key is None
        await session.rollback()


async def test_update_report_success_sets_key_status_and_timestamp(
    test_engine, seed_catalogue
):
    factory = async_sessionmaker(test_engine, expire_on_commit=False)
    exp_id = uuid.uuid4()

    async with factory() as session:
        await session.begin()
        await repo.create(session, exp_id, {"id": str(exp_id), "name": "T"})
        await repo.update_report_success(session, exp_id, "pdfs/new-key.pdf")

        row = await repo.get(session, exp_id)
        assert row.report_status == "success"
        assert row.report_r2_key == "pdfs/new-key.pdf"
        assert row.report_generated_at is not None
        assert row.report_error is None
        await session.rollback()
