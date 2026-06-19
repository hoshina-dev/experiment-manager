"""
Context flattening — converts a raw experiment snapshot into a flat
str→str dict suitable for {{field}} interpolation.

Rules:
- Top-level scalars (str, int, float, bool) → included directly.
- values dict → each key exposed; list values joined for display.
- calculations dict → each key uses result when present, otherwise formula.
- Other nested dicts → flattened one level as parent_key notation.
"""

import json
import re
from typing import Any

_VALID_KEY = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")


def _format_scalar(value: Any, label: str) -> str:
    if value is None:
        return f"[{label}]"
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return f"[{label}]"


def _add_calculation_context(context: dict[str, str], name: str, entry: Any) -> None:
    if not _VALID_KEY.match(name):
        return
    if isinstance(entry, dict):
        result = entry.get("result")
        if result is not None and result != "":
            context[name] = _format_scalar(result, name)
            return
        formula = entry.get("formula")
        if isinstance(formula, str):
            context[name] = formula
            return
    if isinstance(entry, (str, int, float, bool)):
        context[name] = str(entry)


def flatten_context(data: dict[str, Any]) -> dict[str, str]:
    context: dict[str, str] = {}

    for key, value in data.items():
        if isinstance(value, (str, int, float, bool)):
            if _VALID_KEY.match(key):
                context[key] = str(value)

        elif isinstance(value, dict):
            if key == "values":
                for sub_key, sub_val in value.items():
                    if _VALID_KEY.match(sub_key):
                        context[sub_key] = _format_scalar(sub_val, sub_key)
            elif key == "calculations":
                for sub_key, sub_val in value.items():
                    _add_calculation_context(context, sub_key, sub_val)
            elif "questions" not in value:
                for sub_key, sub_val in value.items():
                    flat = f"{key}_{sub_key}"
                    if isinstance(
                        sub_val, (str, int, float, bool)
                    ) and _VALID_KEY.match(flat):
                        context[flat] = str(sub_val)

    values = data.get("values")
    if isinstance(values, dict):
        for sub_key, sub_val in values.items():
            if _VALID_KEY.match(sub_key):
                context[sub_key] = _format_scalar(sub_val, sub_key)

    calculations = data.get("calculations")
    if isinstance(calculations, dict):
        for sub_key, sub_val in calculations.items():
            _add_calculation_context(context, sub_key, sub_val)

    return context
