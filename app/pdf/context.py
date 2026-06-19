"""
Context flattening — converts a raw experiment snapshot into a flat
str→str dict suitable for {{field}} interpolation.

Rules:
- Top-level scalars (str, int, float, bool) → included directly.
- userForm / workerForm with a "questions" list → each question's id becomes
  a key; value is question.value, then config.default, then legacy default,
  otherwise "[Label]".
- repeatable-group answers stored on the group question's value object are
  flattened onto child question ids.
- calculations / calc_result dicts → keys exposed directly (calc_result wins).
- Other nested dicts → flattened one level as parent_key notation.
- Lists → skipped unless handled by a special rule above.
"""

import json
import re
from typing import Any

_VALID_KEY = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")


def _question_answer(q: dict[str, Any]) -> Any:
    if q.get("value") is not None:
        return q["value"]
    config = q.get("config") or {}
    if isinstance(config, dict) and config.get("default") is not None:
        return config["default"]
    return q.get("default")


def _format_answer(value: Any, q_label: str, q_id: str) -> str:
    if value is None:
        return f"[{q_label}]"
    if isinstance(value, (str, int, float, bool)):
        return str(value)
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return f"[{q_label or q_id}]"


def _add_question_context(
    context: dict[str, str],
    q: dict[str, Any],
    *,
    overwrite: bool,
) -> None:
    q_id = q.get("id", "")
    q_label = q.get("label", q_id)
    if not q_id or not _VALID_KEY.match(q_id):
        return

    if q.get("type") == "repeatable-group":
        group_value = _question_answer(q)
        if isinstance(group_value, dict):
            for child_id, child_value in group_value.items():
                if (
                    isinstance(child_id, str)
                    and _VALID_KEY.match(child_id)
                    and (overwrite or child_id not in context)
                ):
                    context[child_id] = _format_answer(child_value, child_id, child_id)
        return

    if not overwrite and q_id in context:
        return

    answer = _question_answer(q)
    if isinstance(answer, (str, int, float, bool, list, dict)):
        context[q_id] = _format_answer(answer, q_label, q_id)
    else:
        context[q_id] = f"[{q_label}]"


def flatten_context(data: dict[str, Any]) -> dict[str, str]:
    context: dict[str, str] = {}

    for key, value in data.items():
        if isinstance(value, (str, int, float, bool)):
            if _VALID_KEY.match(key):
                context[key] = str(value)

        elif isinstance(value, dict):
            if "questions" in value and isinstance(value["questions"], list):
                for q in value["questions"]:
                    _add_question_context(context, q, overwrite=False)
            elif key in ("calculations", "calc_result"):
                for sub_key, sub_val in value.items():
                    # calc_result always overrides calculations (actual values > expressions)
                    if _VALID_KEY.match(sub_key) and (
                        key == "calc_result" or sub_key not in context
                    ):
                        if isinstance(sub_val, (str, int, float, bool)):
                            context[sub_key] = str(sub_val)
                        else:
                            context[sub_key] = f"[{sub_key}]"
            else:
                for sub_key, sub_val in value.items():
                    flat = f"{key}_{sub_key}"
                    if isinstance(
                        sub_val, (str, int, float, bool)
                    ) and _VALID_KEY.match(flat):
                        context[flat] = str(sub_val)

    if isinstance(data.get("workerForm"), dict):
        worker_questions = data["workerForm"].get("questions")
        if isinstance(worker_questions, list):
            for q in worker_questions:
                _add_question_context(context, q, overwrite=True)

    return context
