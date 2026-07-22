"""Unit tests for report orchestration at the service boundary."""

import asyncio
import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from fastapi import HTTPException

from app.services import experiment_service

pytestmark = pytest.mark.unit


def _experiment_row(exp_id: uuid.UUID, *, report_status: str | None = None):
    template_id = uuid.uuid4()
    return SimpleNamespace(
        id=exp_id,
        report_status=report_status,
        state={
            "id": str(exp_id),
            "template_id": str(template_id),
            "name": "Proximate Analysis",
        },
    )


async def test_request_report_enqueues_snapshot_and_persists_pending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = uuid.uuid4()
    row = _experiment_row(exp_id)
    session = SimpleNamespace(commit=AsyncMock())
    queue: asyncio.Queue = asyncio.Queue(maxsize=1)
    get = AsyncMock(return_value=row)
    get_components = AsyncMock(return_value=[{"type": "text", "text": "Report"}])
    update_status = AsyncMock()
    monkeypatch.setattr(experiment_service.experiment_repo, "get", get)
    monkeypatch.setattr(
        experiment_service.experiment_repo, "get_pdf_components", get_components
    )
    monkeypatch.setattr(
        experiment_service.experiment_repo, "update_report_status", update_status
    )

    await experiment_service.request_report(session, exp_id, queue)

    job = queue.get_nowait()
    assert job.exp_id == exp_id
    assert job.experiment_data is row.state
    assert job.template_name == "Proximate Analysis"
    update_status.assert_awaited_once_with(session, exp_id, "pending")
    session.commit.assert_awaited_once_with()


async def test_request_report_full_queue_does_not_mark_pending(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = uuid.uuid4()
    session = SimpleNamespace(commit=AsyncMock())
    queue: asyncio.Queue = asyncio.Queue(maxsize=1)
    queue.put_nowait(object())
    update_status = AsyncMock()
    monkeypatch.setattr(
        experiment_service.experiment_repo,
        "get",
        AsyncMock(return_value=_experiment_row(exp_id)),
    )
    monkeypatch.setattr(
        experiment_service.experiment_repo,
        "get_pdf_components",
        AsyncMock(return_value=[{"type": "text", "text": "Report"}]),
    )
    monkeypatch.setattr(
        experiment_service.experiment_repo, "update_report_status", update_status
    )

    with pytest.raises(HTTPException) as exc_info:
        await experiment_service.request_report(session, exp_id, queue)

    assert exc_info.value.status_code == 503
    update_status.assert_not_awaited()
    session.commit.assert_not_awaited()


@pytest.mark.parametrize("status", ["pending", "processing"])
async def test_request_report_rejects_duplicate_in_flight_job(
    monkeypatch: pytest.MonkeyPatch, status: str
) -> None:
    exp_id = uuid.uuid4()
    monkeypatch.setattr(
        experiment_service.experiment_repo,
        "get",
        AsyncMock(return_value=_experiment_row(exp_id, report_status=status)),
    )

    with pytest.raises(HTTPException) as exc_info:
        await experiment_service.request_report(
            SimpleNamespace(), exp_id, asyncio.Queue()
        )

    assert exc_info.value.status_code == 409
    assert status in exc_info.value.detail


async def test_report_download_uses_stored_key_and_safe_filename(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    exp_id = uuid.uuid4()
    row = _experiment_row(exp_id)
    row.report_r2_key = f"pdfs/{exp_id}.pdf"
    get = AsyncMock(return_value=row)
    presign = Mock(return_value="https://objects.example/report.pdf")
    monkeypatch.setattr(experiment_service.experiment_repo, "get", get)
    monkeypatch.setattr(experiment_service, "presign_download", presign)

    result = await experiment_service.get_report_download_url(
        SimpleNamespace(), exp_id, SimpleNamespace()
    )

    assert result.url == "https://objects.example/report.pdf"
    assert result.expires_in == 900
    presign.assert_called_once()
    assert presign.call_args.args[2] == "Proximate Analysis.pdf"
