"""Run user-authored formulas under limits the formula cannot escape.

Calculation formulas are arbitrary Python supplied by template authors. The
namespace they execute in is already restricted (no builtins, no dunder
access, no imports), which bounds what they can *reach* — but nothing bounded
how long they could *run*. A formula such as `while True: i = i + 1` therefore
consumed a core indefinitely, and because the endpoint awaited it inline on
the event loop, the whole service stopped answering anyone.

Three limits, layered because each covers a case the others cannot:

* **Subprocess.** Python cannot interrupt a thread stuck in a tight loop, so
  the only way to reclaim a runaway is to kill a process. This also keeps the
  work off the event loop.
* **RLIMIT_CPU.** The kernel raises SIGXCPU once the child has burned its CPU
  budget, so a runaway dies even with nothing watching it.
* **nice.** While the child does run it yields to every other process, so a
  legitimate but heavy formula cannot starve the API serving other users.

A wall-clock deadline backstops all three for a child that stalls without
consuming CPU (a blocked syscall, say), which RLIMIT_CPU would never catch.
"""

import multiprocessing as mp
import os
import queue as queue_mod
import resource
import signal
from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import HTTPException
from opentelemetry import trace

from app.config import calc_sandbox_settings

tracer = trace.get_tracer(__name__)

T = TypeVar("T")

# multiprocessing must not inherit the parent's state (open DB connections, the
# running event loop); "spawn" starts a clean interpreter.
_ctx = mp.get_context("spawn")


def _child(func: Callable[..., Any], args: tuple, out: Any) -> None:
    limits = calc_sandbox_settings
    # Soft limit raises SIGXCPU; the hard limit one second later guarantees
    # termination even if something were to trap the signal.
    resource.setrlimit(
        resource.RLIMIT_CPU, (limits.cpu_seconds, limits.cpu_seconds + 1)
    )
    if limits.nice:
        os.nice(limits.nice)
    try:
        out.put(("ok", func(*args)))
    except BaseException as exc:  # noqa: BLE001 - reported to the parent verbatim
        # Pickling can fail for exotic exceptions; fall back to the text so the
        # parent always learns why rather than seeing a bare exit code.
        try:
            out.put(("error", exc))
        except Exception:  # noqa: BLE001
            out.put(("error", RuntimeError(f"{type(exc).__name__}: {exc}")))


def run_bounded(func: Callable[..., T], *args: Any) -> T:
    """Call `func(*args)` in a CPU-limited subprocess and return its result.

    `func` and `args` must be picklable — with the "spawn" start method `func`
    is sent by module path, so it has to be importable at module level.

    Raises HTTPException(422) if the formula exhausted its CPU or wall-clock
    budget; any exception `func` itself raised is re-raised unchanged, so
    callers keep their existing error handling.
    """
    limits = calc_sandbox_settings
    out = _ctx.Queue()
    proc = _ctx.Process(target=_child, args=(func, args, out), daemon=True)

    with tracer.start_as_current_span("sandbox.run_bounded") as span:
        span.set_attribute("sandbox.cpu_seconds", limits.cpu_seconds)
        span.set_attribute("sandbox.wall_seconds", limits.wall_seconds)
        proc.start()
        try:
            # Read before joining: a large result would otherwise fill the pipe
            # and deadlock the child on put() while the parent waits on join().
            status, payload = out.get(timeout=limits.wall_seconds)
        except queue_mod.Empty:
            span.set_attribute("sandbox.outcome", _outcome(proc))
            raise _limit_error(proc, limits) from None
        finally:
            if proc.is_alive():
                proc.kill()
            proc.join()

        span.set_attribute("sandbox.outcome", status)
        if status == "error":
            raise payload
        return payload


def _outcome(proc: Any) -> str:
    if proc.is_alive():
        return "wall_timeout"
    return "cpu_exceeded" if _killed_by_cpu(proc) else "died"


def _killed_by_cpu(proc: Any) -> bool:
    return proc.exitcode is not None and proc.exitcode == -signal.SIGXCPU


def _limit_error(proc: Any, limits: Any) -> HTTPException:
    # join() in the caller's finally has not run yet; give the child a moment to
    # be reaped so exitcode is meaningful.
    proc.join(0.1)
    if _killed_by_cpu(proc):
        return HTTPException(
            422,
            f"Calculation exceeded its {limits.cpu_seconds}s CPU limit — "
            "check for a formula that loops without terminating.",
        )
    if proc.is_alive():
        return HTTPException(
            422,
            f"Calculation exceeded its {limits.wall_seconds}s time limit.",
        )
    return HTTPException(500, "Calculation worker exited without a result.")
