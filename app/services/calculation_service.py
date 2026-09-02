import ast
import math
import uuid
from typing import Any

from fastapi import HTTPException
from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncSession

from app import form_schema
from app.models import (CalculationDryRunRequest, CalculationDryRunResponse,
                        CalculationError, CalculationOutcome, ExperimentDetail)
from app.repositories import experiment_repository as experiment_repo
from app.services.experiment_service import _row_to_detail

tracer = trace.get_tracer(__name__)


def _referenced_names(expr: str) -> set[str]:
    """Identifier names a formula references — used only to find which
    *other calculations* it depends on, not to evaluate anything."""
    try:
        tree = ast.parse(expr, mode="exec")
    except SyntaxError:
        return set()  # let the evaluator surface the real syntax error later
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def _referenced_value_keys(expr: str) -> set[str]:
    """Question ids a formula reads as `values['some_id']`. Used to tell an
    author which answers a formula expects but never received — a typo'd
    question id is otherwise only visible as a bare KeyError."""
    try:
        tree = ast.parse(expr, mode="exec")
    except SyntaxError:
        return set()
    return {
        node.slice.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Subscript)
        and isinstance(node.value, ast.Name)
        and node.value.id == "values"
        and isinstance(node.slice, ast.Constant)
        and isinstance(node.slice.value, str)
    }


def _resolve_order(formulas: dict[str, str]) -> tuple[list[str], list[str]]:
    """Order calculation names so each is evaluated after every other
    calculation it references — independent of declaration order, since
    nothing upstream (JSONB columns, Python dict order, a future rewrite in
    a language with unordered maps) is guaranteed to preserve the order
    formulas happened to be declared/stored in.

    Returns the resolvable names in evaluation order plus the names that
    could never be resolved (a dependency cycle, and anything downstream of
    one). Callers decide whether that is fatal.
    """
    names = set(formulas)
    deps = {
        name: _referenced_names(expr) & names - {name}
        for name, expr in formulas.items()
    }

    order: list[str] = []
    resolved: set[str] = set()
    remaining = dict(deps)

    while remaining:
        ready = sorted(name for name, unmet in remaining.items() if unmet <= resolved)
        if not ready:
            break
        for name in ready:
            order.append(name)
            resolved.add(name)
            del remaining[name]

    return order, sorted(remaining)


def _dependency_order(formulas: dict[str, str]) -> list[str]:
    order, unresolved = _resolve_order(formulas)
    if unresolved:
        cycle = ", ".join(unresolved)
        raise HTTPException(422, f"Circular dependency among calculations: {cycle}")
    return order


def _coerce_numeric(value: Any) -> Any:
    """Parse a numeric-looking string into a number so arithmetic formulas
    work regardless of how the value arrived. `answerValue` in
    experiment.schema.json legitimately allows a string for any key (a
    "number" question answered through a form that round-trips everything
    as text, for instance), so the calculation engine — not the schema —
    is responsible for this. Non-numeric strings, and anything that isn't
    a string or list, pass through unchanged.
    """
    if isinstance(value, list):
        return [_coerce_numeric(item) for item in value]
    if isinstance(value, str):
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value
    return value


def _eval_formula(expr: str, namespace: dict[str, Any]) -> Any:
    """Evaluate a formula that may be a single expression or multi-line code.

    Leading statements run with exec; the final statement, if it is an
    expression, is evaluated and returned (so plain single-expression formulas
    behave exactly as before). Multi-line code that does not end in an
    expression must assign its output to a `result` variable.
    """
    restricted = {"__builtins__": {}}
    tree = ast.parse(expr, mode="exec")
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        final = tree.body.pop()
        if tree.body:
            exec(
                compile(tree, "<formula>", "exec"), restricted, namespace
            )  # noqa: S102
        return eval(  # noqa: S307
            compile(ast.Expression(final.value), "<formula>", "eval"),
            restricted,
            namespace,
        )
    namespace.pop("result", None)
    exec(compile(tree, "<formula>", "exec"), restricted, namespace)  # noqa: S102
    return namespace.get("result")


def _base_namespace(values: dict[str, Any]) -> dict[str, Any]:
    return {
        **form_schema.CALC_BUILTINS,
        "math": math,
        "values": {name: _coerce_numeric(value) for name, value in values.items()},
    }


def _eval_one(
    name: str, expr: str, namespace: dict[str, Any]
) -> tuple[Any, CalculationError | None]:
    """Evaluate one formula, returning either its value or a structured
    description of what went wrong. Callers choose whether a failure aborts
    the whole run (`_eval_calculations`) or is reported alongside the
    formulas that did succeed (`dry_run`)."""
    if "__" in expr:
        return None, CalculationError(
            kind="dunder",
            message=f"Invalid expression in '{name}': dunder access not allowed",
        )
    try:
        value = _eval_formula(expr, namespace)
    except ZeroDivisionError:
        return None, CalculationError(
            kind="zero_division", message=f"Division by zero in '{name}'"
        )
    except NameError as exc:
        return None, CalculationError(
            kind="undefined_name",
            message=f"Undefined variable in '{name}': {exc}",
            names=[exc.name] if exc.name else [],
        )
    except KeyError as exc:
        key = str(exc.args[0]) if exc.args else ""
        return None, CalculationError(
            kind="missing_value",
            message=f"Missing value in '{name}': no answer for '{key}'",
            names=[key] if key else [],
        )
    except SyntaxError as exc:
        return None, CalculationError(
            kind="syntax", message=f"Calculation error in '{name}': {exc}"
        )
    except Exception as exc:
        return None, CalculationError(
            kind="runtime", message=f"Calculation error in '{name}': {exc}"
        )

    if isinstance(value, float) and not math.isfinite(value):
        return None, CalculationError(
            kind="non_finite", message=f"Non-finite result in '{name}' (got {value})"
        )

    return value, None


def _eval_calculations(
    values: dict[str, Any], formulas: dict[str, str]
) -> dict[str, Any]:
    namespace = _base_namespace(values)
    results: dict[str, Any] = {}

    for name in _dependency_order(formulas):
        value, error = _eval_one(name, formulas[name], namespace)
        if error is not None:
            raise HTTPException(422, error.message)
        namespace[name] = value
        results[name] = value

    return results


def dry_run(body: CalculationDryRunRequest) -> CalculationDryRunResponse:
    """Evaluate a draft template's formulas without touching the database.

    Unlike `calculate`, one bad formula does not abort the run: every
    calculation reports its own result or error so a template author sees
    all their mistakes at once instead of fixing them one 422 at a time.
    """
    with tracer.start_as_current_span("calculation_service.dry_run") as span:
        draft: dict[str, Any] = {
            "clientForm": body.clientForm.model_dump() if body.clientForm else None,
            "labForm": body.labForm.model_dump() if body.labForm else None,
            "values": body.values,
        }
        values = form_schema.collect_values(draft)
        formulas = form_schema.calculation_formulas(
            {name: calc.model_dump() for name, calc in body.calculations.items()}
        )
        span.set_attribute("calculations.count", len(formulas))

        namespace = _base_namespace(values)
        order, unresolved = _resolve_order(formulas)
        outcomes: dict[str, CalculationOutcome] = {}
        failed: set[str] = set()

        for name in order:
            expr = formulas[name]
            blocked = sorted(_referenced_names(expr) & failed)
            if blocked:
                outcomes[name] = CalculationOutcome(
                    formula=expr,
                    status="skipped",
                    error=CalculationError(
                        kind="dependency_failed",
                        message=(
                            "Not evaluated — depends on "
                            f"{', '.join(blocked)}, which did not produce a result"
                        ),
                        names=blocked,
                    ),
                )
                failed.add(name)
                continue

            value, error = _eval_one(name, expr, namespace)
            if error is not None:
                outcomes[name] = CalculationOutcome(
                    formula=expr, status="error", error=error
                )
                failed.add(name)
                continue

            namespace[name] = value
            outcomes[name] = CalculationOutcome(formula=expr, status="ok", result=value)

        cycle = ", ".join(unresolved)
        for name in unresolved:
            outcomes[name] = CalculationOutcome(
                formula=formulas[name],
                status="error",
                error=CalculationError(
                    kind="circular",
                    message=f"Circular dependency among calculations: {cycle}",
                    names=sorted(set(unresolved) - {name}),
                ),
            )

        referenced: set[str] = set()
        for expr in formulas.values():
            referenced |= _referenced_value_keys(expr)

        span.set_attribute("calculations.failed", len(failed) + len(unresolved))

        return CalculationDryRunResponse(
            values=namespace["values"],
            order=order,
            # Re-key in declaration order so the caller can render the rows in
            # the order the author wrote them; `order` carries the eval order.
            calculations={
                name: outcomes[name] for name in formulas if name in outcomes
            },
            missing_values=sorted(referenced - set(values)),
            duplicate_question_ids=form_schema.find_duplicate_question_ids(draft),
        )


async def calculate(session: AsyncSession, exp_id: uuid.UUID) -> ExperimentDetail:
    with tracer.start_as_current_span("calculation_service.calculate") as span:
        span.set_attribute("exp_id", str(exp_id))

        row = await experiment_repo.get(session, exp_id)
        if row is None:
            raise HTTPException(404, f'Experiment "{exp_id}" not found')

        values = form_schema.collect_values(row.state)
        formulas = form_schema.calculation_formulas(row.state.get("calculations"))
        results = _eval_calculations(values, formulas)

        calculations = form_schema.apply_calculation_results(
            row.state.get("calculations"), results
        )
        new_state = {**row.state, "values": values, "calculations": calculations}
        new_state.pop("calc_result", None)

        row = await experiment_repo.update(session, exp_id, new_state)
        await session.commit()

        return _row_to_detail(row)
