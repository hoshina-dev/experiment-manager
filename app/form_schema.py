"""Shared helpers for the experiment template / context schema."""

from __future__ import annotations

import re
import statistics
from typing import Any

CalcResult = str | int | float | bool | None | list[Any]


def iter_questions(form: dict[str, Any] | None) -> list[dict[str, Any]]:
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
        if q.get("type") == "repeatable-group":
            config = q.get("config") or {}
            children = config.get("questions") if isinstance(config, dict) else None
            if isinstance(children, list):
                out.extend(child for child in children if isinstance(child, dict))
    return out


def collect_question_ids(state: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for form_key in ("clientForm", "labForm"):
        for q in iter_questions(state.get(form_key)):
            q_id = q.get("id")
            if isinstance(q_id, str):
                ids.add(q_id)
    return ids


def _question_default(q: dict[str, Any]) -> Any:
    config = q.get("config") or {}
    if isinstance(config, dict) and config.get("default") is not None:
        return config["default"]
    return q.get("default")


def collect_values(state: dict[str, Any]) -> dict[str, Any]:
    values = dict(state.get("values") or {})
    for form_key in ("clientForm", "labForm"):
        for q in iter_questions(state.get(form_key)):
            q_id = q.get("id")
            if not isinstance(q_id, str) or q_id in values:
                continue
            default = _question_default(q)
            if default is not None:
                values[q_id] = default
    return values


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
    "mean": statistics.mean,
    "median": statistics.median,
    "stdev": statistics.stdev,
}
