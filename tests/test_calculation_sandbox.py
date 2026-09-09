"""A formula must never be able to hold the service hostage.

Before the sandbox, `while True: i = i + 1` in a calculation ran inline on the
event loop, so one template author could stop experiment-manager answering
anyone — every page in the web app that reads this service froze for every
user until the process was killed by hand.
"""

import asyncio
import threading
import time

import pytest
from fastapi import HTTPException

from app.config import calc_sandbox_settings
from app.services import sandbox
from app.services.calculation_service import _eval_calculations

RUNAWAY = {"spin": "i = 0\nwhile True:\n    i = i + 1\nresult = i"}
CHEAP = {"ok": "result = round(mean([1.0, 2.0, 6.0]) * 2, 3)"}


def test_runaway_formula_is_killed_and_reported():
    """The kernel reclaims a formula that never terminates."""
    started = time.perf_counter()
    with pytest.raises(HTTPException) as excinfo:
        sandbox.run_bounded(_eval_calculations, {}, RUNAWAY)
    elapsed = time.perf_counter() - started

    assert excinfo.value.status_code == 422
    assert "CPU limit" in excinfo.value.detail
    # Bounded by the CPU budget plus process start-up — nowhere near the
    # forever it used to run for.
    assert elapsed < 10, f"took {elapsed:.1f}s — the limit did not fire"


def test_runaway_is_reported_at_its_cpu_limit_not_its_wall_limit():
    """A killed child must be noticed at once, not waited out.

    Blocking on the queue for the full wall deadline made every runaway cost
    5s even though the kernel had reclaimed it at 2s — the user waited on a
    deadline that had already stopped mattering.
    """
    started = time.perf_counter()
    with pytest.raises(HTTPException):
        sandbox.run_bounded(_eval_calculations, {}, RUNAWAY)
    elapsed = time.perf_counter() - started

    wall = calc_sandbox_settings.wall_seconds
    assert elapsed < wall, (
        f"took {elapsed:.2f}s, i.e. the full {wall}s wall budget — "
        "the parent is not noticing the child's death"
    )


def test_concurrent_calculations_are_capped():
    """Spamming calculate must not spawn a worker per click.

    The per-formula CPU limit bounds one calculation; without a concurrency
    cap it bounds nothing in aggregate, and a handful of clicks occupies every
    core.
    """
    limit = calc_sandbox_settings.max_concurrent
    outcomes: list[str] = []

    def attempt() -> None:
        try:
            sandbox.run_bounded(_eval_calculations, {}, RUNAWAY)
            outcomes.append("ok")
        except HTTPException as exc:
            outcomes.append(str(exc.status_code))

    threads = [threading.Thread(target=attempt) for _ in range(limit + 3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(30)

    assert (
        "429" in outcomes
    ), f"no request was refused ({outcomes}) — the cap is not being enforced"


def test_normal_formula_still_evaluates():
    """The sandbox must not change results for well-behaved formulas."""
    assert sandbox.run_bounded(_eval_calculations, {}, CHEAP) == {"ok": 6.0}


def test_formula_errors_propagate_unchanged():
    """A bad formula still raises the service's own error, not a sandbox one."""
    with pytest.raises(HTTPException) as excinfo:
        sandbox.run_bounded(_eval_calculations, {}, {"bad": "result = 1/0"})
    assert excinfo.value.status_code == 422
    assert "Division by zero" in excinfo.value.detail


async def test_event_loop_stays_free_while_a_formula_runs_away():
    """The whole point: other work proceeds while a runaway is being killed.

    Previously the runaway held the event loop, so this counter would not have
    advanced at all — and the formula never finished, so it never would have.
    """
    ticks = 0

    async def heartbeat() -> None:
        nonlocal ticks
        while True:
            await asyncio.sleep(0.05)
            ticks += 1

    beat = asyncio.create_task(heartbeat())
    try:
        with pytest.raises(HTTPException):
            await asyncio.to_thread(
                sandbox.run_bounded, _eval_calculations, {}, RUNAWAY
            )
    finally:
        beat.cancel()

    assert ticks > 5, f"event loop advanced only {ticks} ticks — it was blocked"
