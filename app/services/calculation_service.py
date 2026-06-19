import math
import uuid
from typing import Any

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.form_schema import (CALC_BUILTINS, apply_calculation_results,
                             calculation_formulas, collect_values)
from app.models import ExperimentDetail
from app.repositories import experiment_repository as experiment_repo
from app.services.experiment_service import _row_to_detail


def _eval_calculations(
    values: dict[str, Any], formulas: dict[str, str]
) -> dict[str, Any]:
    namespace: dict[str, Any] = {**CALC_BUILTINS, "math": math, "values": values}
    results: dict[str, Any] = {}

    for name, expr in formulas.items():
        if "__" in expr:
            raise HTTPException(
                422, f"Invalid expression in '{name}': dunder access not allowed"
            )
        try:
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


async def calculate(session: AsyncSession, exp_id: uuid.UUID) -> ExperimentDetail:
    row = await experiment_repo.get(session, exp_id)
    if row is None:
        raise HTTPException(404, f'Experiment "{exp_id}" not found')

    values = collect_values(row.state)
    formulas = calculation_formulas(row.state.get("calculations"))
    results = _eval_calculations(values, formulas)

    calculations = apply_calculation_results(row.state.get("calculations"), results)
    new_state = {**row.state, "values": values, "calculations": calculations}
    new_state.pop("calc_result", None)

    row = await experiment_repo.update(session, exp_id, new_state)
    await session.commit()

    return _row_to_detail(row)
