"""Shared helpers for the experiment template / context schema."""

from __future__ import annotations

import re
import statistics
from typing import Any

CalcResult = str | int | float | bool | None | list[Any]


def iter_questions(
    form: dict[str, Any] | None, expand_repeatable_groups: bool = True
) -> list[dict[str, Any]]:
    """Top-level questions in `form`. By default also flattens a
    repeatable-group's child questions into the result (useful for callers
    that just want every question id, e.g. duplicate-id detection). Pass
    `expand_repeatable_groups=False` for callers that need to handle a
    group's children themselves — e.g. to apply `config.count` when filling
    in defaults, which flattening would lose.
    """
    if not isinstance(form, dict):
        return []
    questions = form.get("questions")
    if not isinstance(questions, list):
        return []
    out: list[dict[str, Any]] = []
    for q in questions:
        if not isinstance(q, dict):
            continue
        out.append(q)
        if expand_repeatable_groups and q.get("type") == "repeatable-group":
            config = q.get("config") or {}
            children = config.get("questions") if isinstance(config, dict) else None
            if isinstance(children, list):
                out.extend(child for child in children if isinstance(child, dict))
    return out


def find_duplicate_question_ids(state: dict[str, Any]) -> list[str]:
    """Question ids used more than once across clientForm + labForm
    (including repeatable-group children). The schema documents ids as
    unique across both forms, but JSON Schema's `uniqueItems` only applies
    within a single array — it can't see across clientForm and labForm —
    so this has to be checked separately.
    """
    seen: dict[str, int] = {}
    for form_key in ("clientForm", "labForm"):
        for q in iter_questions(state.get(form_key)):
            q_id = q.get("id")
            if isinstance(q_id, str):
                seen[q_id] = seen.get(q_id, 0) + 1
    return sorted(q_id for q_id, count in seen.items() if count > 1)


def _question_default(q: dict[str, Any]) -> Any:
    config = q.get("config") or {}
    if isinstance(config, dict) and config.get("default") is not None:
        return config["default"]
    return q.get("default")


def collect_values(state: dict[str, Any]) -> dict[str, Any]:
    values = dict(state.get("values") or {})
    for form_key in ("clientForm", "labForm"):
        for q in iter_questions(state.get(form_key), expand_repeatable_groups=False):
            if q.get("type") == "repeatable-group":
                _collect_repeatable_group_defaults(q, values)
                continue
            q_id = q.get("id")
            if not isinstance(q_id, str) or q_id in values:
                continue
            default = _question_default(q)
            if default is not None:
                values[q_id] = default
    return values


def _collect_repeatable_group_defaults(
    group: dict[str, Any], values: dict[str, Any]
) -> None:
    """Columnar storage: a child's `config.default` fills every repetition,
    not just one bare scalar — `config.count` says how many entries the
    column needs.
    """
    config = group.get("config") or {}
    if not isinstance(config, dict):
        return
    count = config.get("count")
    children = config.get("questions")
    if not isinstance(count, int) or not isinstance(children, list):
        return
    for child in children:
        if not isinstance(child, dict):
            continue
        child_id = child.get("id")
        if not isinstance(child_id, str) or child_id in values:
            continue
        default = _question_default(child)
        if default is not None:
            values[child_id] = [default] * count


def calculation_formulas(calculations: dict[str, Any] | None) -> dict[str, str]:
    formulas: dict[str, str] = {}
    for name, entry in (calculations or {}).items():
        if isinstance(entry, dict):
            formula = entry.get("formula")
            if isinstance(formula, str):
                formulas[name] = formula
        elif isinstance(entry, str):
            formulas[name] = entry
    return formulas


def apply_calculation_results(
    calculations: dict[str, Any] | None, results: dict[str, CalcResult]
) -> dict[str, dict[str, Any]]:
    updated: dict[str, dict[str, Any]] = {}
    for name, entry in (calculations or {}).items():
        if isinstance(entry, dict):
            formula = entry.get("formula", "")
        elif isinstance(entry, str):
            formula = entry
        else:
            continue
        updated[name] = {"formula": formula, "result": results.get(name, "")}
    return updated


def migrate_formula(formula: str, question_ids: set[str], calc_names: set[str]) -> str:
    updated = formula
    for q_id in sorted(question_ids, key=len, reverse=True):
        if q_id in calc_names:
            continue
        updated = re.sub(rf"\b{re.escape(q_id)}\b", f"values['{q_id}']", updated)
    return updated


CALC_BUILTINS: dict[str, Any] = {
    "round": round,
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "zip": zip,
    "mean": statistics.mean,
    "median": statistics.median,
    "stdev": statistics.stdev,
}
