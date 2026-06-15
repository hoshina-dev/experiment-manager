"""
Context flattening — converts a raw experiment snapshot into a flat
str→str dict suitable for {{field}} interpolation.

Rules:
- Top-level scalars (str, int, float, bool) → included directly.
- userForm / workerForm with a "questions" list → each question's id becomes
  a key; value is question.default if present, otherwise "[Label]".
- calculations dict → keys exposed directly (no prefix).
- Other nested dicts → flattened one level as parent_key notation.
- Lists → skipped unless handled by a special rule above.
"""

import re
from typing import Any

_VALID_KEY = re.compile(r"^[A-Za-z_$][A-Za-z0-9_$]*$")


def flatten_context(data: dict[str, Any]) -> dict[str, str]:
    context: dict[str, str] = {}

    for key, value in data.items():
        if isinstance(value, (str, int, float, bool)):
            if _VALID_KEY.match(key):
                context[key] = str(value)

        elif isinstance(value, dict):
            if "questions" in value and isinstance(value["questions"], list):
                for q in value["questions"]:
                    q_id = q.get("id", "")
                    q_label = q.get("label", q_id)
                    if q_id and _VALID_KEY.match(q_id) and q_id not in context:
                        default = q.get("value", q.get("default"))
                        if default is not None and isinstance(
                            default, (str, int, float, bool)
                        ):
                            context[q_id] = str(default)
                        else:
                            context[q_id] = f"[{q_label}]"
            elif key in ("calculations", "calc_result"):
                for sub_key, sub_val in value.items():
                    # calc_result always overrides calculations (actual values > expressions)
                    if _VALID_KEY.match(sub_key) and (key == "calc_result" or sub_key not in context):
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

    return context
