import ast
import concurrent.futures
import math
import uuid
from collections.abc import Callable
from typing import Any

from fastapi import HTTPException
from opentelemetry import trace
from sqlalchemy.ext.asyncio import AsyncSession

from app import form_schema
from app.models import ExperimentDetail
from app.repositories import experiment_repository as experiment_repo
from app.services.experiment_service import _row_to_detail

tracer = trace.get_tracer(__name__)

_EVAL_TIMEOUT_SECS = 5
_MAX_EXPONENT = 1000


_BLOCKED_ATTRS = frozenset({"format", "encode", "decode", "mro", "func", "gi_frame"})


def _validate_ast(tree: ast.AST) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("_"):
                raise HTTPException(
                    422, f"Private attribute access not allowed in formulas: .{node.attr}"
                )
            if node.attr in _BLOCKED_ATTRS:
                raise HTTPException(
                    422, f"Attribute not allowed in formulas: .{node.attr}"
                )
        if isinstance(node, ast.Name) and "__" in node.id:
            raise HTTPException(
                422, f"Double-underscore identifier not allowed in formulas: {node.id}"
            )
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            raise HTTPException(422, "Import statements not allowed in formulas")
        if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Pow):
            if isinstance(node.right, ast.BinOp) and isinstance(node.right.op, ast.Pow):
                raise HTTPException(422, "Chained power expressions (a**b**c) not allowed")
            if isinstance(node.right, ast.Constant) and isinstance(node.right.value, (int, float)):
                if node.right.value > _MAX_EXPONENT:
                    raise HTTPException(422, f"Exponent too large (max {_MAX_EXPONENT}): {node.right.value}")


def _run_with_timeout(fn: Callable[[], Any]) -> Any:
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        future = pool.submit(fn)
        try:
            return future.result(timeout=_EVAL_TIMEOUT_SECS)
        except concurrent.futures.TimeoutError:
            raise HTTPException(
                422,
                f"Formula timed out after {_EVAL_TIMEOUT_SECS}s — "
                "check for unbounded computations",
            )


def _referenced_names(expr: str) -> set[str]:
    """Identifier names a formula references — used only to find which
    *other calculations* it depends on, not to evaluate anything."""
    try:
        tree = ast.parse(expr, mode="exec")
    except SyntaxError:
        return set()  # let the evaluator surface the real syntax error later
    return {node.id for node in ast.walk(tree) if isinstance(node, ast.Name)}


def _dependency_order(formulas: dict[str, str]) -> list[str]:
    """Order calculation names so each is evaluated after every other
    calculation it references — independent of declaration order, since
    nothing upstream (JSONB columns, Python dict order, a future rewrite in
    a language with unordered maps) is guaranteed to preserve the order
    formulas happened to be declared/stored in.
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
            cycle = ", ".join(sorted(remaining))
            raise HTTPException(422, f"Circular dependency among calculations: {cycle}")
        for name in ready:
            order.append(name)
            resolved.add(name)
            del remaining[name]

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
    _validate_ast(tree)
    if tree.body and isinstance(tree.body[-1], ast.Expr):
        final = tree.body.pop()
        assert isinstance(final, ast.Expr)
        if tree.body:
            _run_with_timeout(
                lambda: exec(  # noqa: S102
                    compile(tree, "<formula>", "exec"), restricted, namespace
                )
            )
        return _run_with_timeout(
            lambda: eval(  # noqa: S307
                compile(ast.Expression(final.value), "<formula>", "eval"),
                restricted,
                namespace,
            )
        )
    namespace.pop("result", None)
    _run_with_timeout(
        lambda: exec(compile(tree, "<formula>", "exec"), restricted, namespace)  # noqa: S102
    )
    return namespace.get("result")


def _eval_calculations(
    values: dict[str, Any], formulas: dict[str, str]
) -> dict[str, Any]:
    values = {name: _coerce_numeric(value) for name, value in values.items()}
    namespace: dict[str, Any] = {
        **form_schema.CALC_BUILTINS,
        "math": math,
        "values": values,
    }
    results: dict[str, Any] = {}

    for name in _dependency_order(formulas):
        expr = formulas[name]
        if "__" in expr:
            raise HTTPException(
                422, f"Invalid expression in '{name}': dunder access not allowed"
            )
        try:
            value = _eval_formula(expr, namespace)
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
