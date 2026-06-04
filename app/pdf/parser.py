import re
from typing import Any

FIELD_PATTERN = re.compile(r"\{\{\s*([\w$]+)\s*\}\}")


def interpolate_template(template: str, context: dict[str, Any]) -> str:
    """Replace {{field}} placeholders with values from context. Unmatched fields left as-is."""

    def _replace(match: re.Match) -> str:
        value = context.get(match.group(1))
        return str(value) if value is not None else match.group(0)

    return FIELD_PATTERN.sub(_replace, template)


def extract_fields(text: str) -> list[str]:
    """Return unique field names found in {{field}} placeholders."""
    return list(set(FIELD_PATTERN.findall(text)))
