"""Background report worker — consumes ReportJobs from an asyncio.Queue.

PDF generation runs in a ProcessPoolExecutor (bypasses GIL for CPU-bound
ReportLab work). DB updates happen in the async event loop after the
subprocess returns, using fresh sessions to avoid cross-boundary sharing.
The worker never dies on a failed job — it logs the error, marks the
experiment as failed, and moves on.
"""

import asyncio
import logging
import uuid
from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import async_sessionmaker

import app.repositories.experiment_repository as experiment_repo
from app.pdf import generate_pdf
from app.pdf.r2_client import upload_pdf

logger = logging.getLogger(__name__)


@dataclass
class ReportJob:
    exp_id: uuid.UUID
    experiment_data: dict       # state.snapshot — all fields needed by the engine
    pdf_components: list        # from pdf_templates.components at snapshot time
    template_name: str          # used for the R2 filename


def _generate_and_upload(job: ReportJob, r2_key: str, cfg) -> None:
    """Synchronous worker — runs inside a subprocess via ProcessPoolExecutor."""
    pdf_bytes = generate_pdf(job.experiment_data, job.pdf_components)
    upload_pdf(pdf_bytes, r2_key, cfg)


async def report_worker(
    queue: asyncio.Queue,
    executor: ProcessPoolExecutor,
    db_factory: async_sessionmaker,
    r2_cfg,
) -> None:
    loop = asyncio.get_running_loop()

    while True:
        job: ReportJob = await queue.get()
        r2_key = f"pdfs/{job.exp_id}.pdf"

        try:
            async with db_factory() as session:
                await experiment_repo.update_report_status(session, job.exp_id, "processing")
                await session.commit()

            await loop.run_in_executor(executor, _generate_and_upload, job, r2_key, r2_cfg)

            async with db_factory() as session:
                await experiment_repo.update_report_success(session, job.exp_id, r2_key)
                await session.commit()

        except Exception:
            logger.exception("Report generation failed for exp_id=%s", job.exp_id)
            try:
                async with db_factory() as session:
                    await experiment_repo.update_report_failure(
                        session, job.exp_id, f"Generation failed — see server logs"
                    )
                    await session.commit()
            except Exception:
                logger.exception("Failed to record report failure for exp_id=%s", job.exp_id)

        finally:
            queue.task_done()
