import math
import uuid

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ExperimentDetail
from app.repositories import experiment_repository as experiment_repo
from app.services.experiment_service import _row_to_detail

# ---------------------------------------------------------------------------
# Input extraction
# ---------------------------------------------------------------------------

def _question_value(q: dict) -> object | None:
    if q.get("value") is not None:
        return q["value"]
    config = q.get("config") or {}
    if isinstance(config, dict) and config.get("default") is not None:
        return config["default"]
    return q.get("default")


def _extract_inputs(state: dict) -> dict[str, object]:
    worker_form = state.get("workerForm") or {}
    questions = worker_form.get("questions", []) if isinstance(worker_form, dict) else []
    inputs: dict[str, object] = {}
    for q in questions:
        q_id = q.get("id")
        if not q_id:
            continue
        if q.get("type") == "repeatable-group":
            group_value = _question_value(q)
            if isinstance(group_value, dict):
                for child_id, child_value in group_value.items():
                    if child_value is not None:
                        inputs[child_id] = child_value
            continue
        value = _question_value(q)
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
        if "__" in expr:
            raise HTTPException(422, f"Invalid expression in '{name}': dunder access not allowed")
        try:
            # restricted namespace to prevent access to built-ins and globals; only allow specified functions and inputs
            value = eval(expr, {"__builtins__": {}}, namespace)  # noqa: S307
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
