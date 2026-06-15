import math
import re
import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ExperimentDetail
from app.repositories import experiment_repository as experiment_repo
from app.services.experiment_service import _row_to_detail

# ---------------------------------------------------------------------------
# JS → Python expression translation
# ---------------------------------------------------------------------------

_RULES: list[tuple[re.Pattern, str]] = [
    # JS Math methods that map to Python builtins (not math module)
    (re.compile(r"\bMath\.round\b"), "round"),
    (re.compile(r"\bMath\.abs\b"),   "abs"),
    (re.compile(r"\bMath\.min\b"),   "min"),
    (re.compile(r"\bMath\.max\b"),   "max"),
    # Constants with casing differences
    (re.compile(r"\bMath\.PI\b"),    "math.pi"),
    (re.compile(r"\bMath\.E\b"),     "math.e"),
    # Catch-all: Math.anything → math.anything (sqrt, floor, ceil, log, sin, cos, ...)
    (re.compile(r"\bMath\."),        "math."),
    # JS operators and literals
    (re.compile(r"==="),             "=="),
    (re.compile(r"!=="),             "!="),
    (re.compile(r"\bnull\b"),        "None"),
    (re.compile(r"\bundefined\b"),   "None"),
    (re.compile(r"\btrue\b"),        "True"),
    (re.compile(r"\bfalse\b"),       "False"),
]

_TERNARY = re.compile(r"(.+?)\s*\?\s*(.+?)\s*:\s*(.+)")


def _translate(expr: str) -> str:
    for pattern, replacement in _RULES:
        expr = pattern.sub(replacement, expr)
    m = _TERNARY.fullmatch(expr.strip())
    if m:
        cond, if_true, if_false = m.group(1), m.group(2), m.group(3)
        expr = f"({if_true}) if ({cond}) else ({if_false})"
    return expr


# ---------------------------------------------------------------------------
# Input extraction
# ---------------------------------------------------------------------------

def _extract_inputs(state: dict) -> dict[str, object]:
    worker_form = state.get("workerForm") or {}
    questions = worker_form.get("questions", []) if isinstance(worker_form, dict) else []
    inputs: dict[str, object] = {}
    for q in questions:
        q_id = q.get("id")
        if q_id:
            value = q.get("value", q.get("default"))
            if value is not None:
                inputs[q_id] = value
    return inputs


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------

_SAFE_BUILTINS = {"round": round, "abs": abs, "min": min, "max": max, "math": math}


def _eval_calculations(
    inputs: dict[str, object], calculations: dict[str, str]
) -> dict[str, object]:
    namespace: dict[str, object] = {**_SAFE_BUILTINS, **inputs}
    results: dict[str, object] = {}

    for name, expr in calculations.items():
        py_expr = _translate(expr)
        if "__" in py_expr:
            raise HTTPException(422, f"Invalid expression in '{name}': dunder access not allowed")
        try:
            # restricted namespace to prevent access to built-ins and globals; only allow specified functions and inputs
            value = eval(py_expr, {"__builtins__": {}}, namespace)  # noqa: S307
        except ZeroDivisionError:
            raise HTTPException(422, f"Division by zero in '{name}'")
        except NameError as exc:
            raise HTTPException(422, f"Undefined variable in '{name}': {exc}")
        except Exception as exc:
            raise HTTPException(422, f"Calculation error in '{name}': {exc}")

        if isinstance(value, float) and not math.isfinite(value):
            raise HTTPException(422, f"Non-finite result in '{name}' (got {value})")

        namespace[name] = value
        results[name] = value

    return results


# ---------------------------------------------------------------------------
# Service function
# ---------------------------------------------------------------------------

async def calculate(session: AsyncSession, exp_id: uuid.UUID) -> ExperimentDetail:
    row = await experiment_repo.get(session, exp_id)
    if row is None:
        raise HTTPException(404, f'Experiment "{exp_id}" not found')

    inputs = _extract_inputs(row.state)
    calculations: dict[str, str] = row.state.get("calculations") or {}

    calc_result = _eval_calculations(inputs, calculations)

    new_state = {**row.state, "calc_result": calc_result}
    row = await experiment_repo.update(session, exp_id, new_state)
    await session.commit()

    return _row_to_detail(row)
