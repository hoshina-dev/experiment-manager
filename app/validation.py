"""JSON Schema validation for experiment forms.

The canonical contract lives in ``experiment.schema.json`` at the repo root. Both
the **experiment template** (the starting JSON authored per analysis) and the
**experiment context** (the living copy stored per experiment) must comply with
it before they are persisted.

Only the schema-defined slice is validated here — ``clientForm``, ``labForm``,
``calculations`` and ``values``. Envelope metadata frozen on the context
(``id``, ``sample_id``, ``template_id``, ``lineage_id``, ``name``,
``description``) is validated by Pydantic, not by the schema, so it is stripped
before validation to avoid tripping the schema's ``additionalProperties: false``.
"""

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "experiment.schema.json"

# Top-level keys defined by experiment.schema.json. `values` is optional on
# templates and present on experiment contexts.
_SCHEMA_KEYS = ("clientForm", "labForm", "calculations", "values")


class FormSchemaError(Exception):
    """Raised when a form payload violates experiment.schema.json.

    Carries a list of human-readable ``location: message`` strings so the
    service layer can surface them in a 422 response.
    """

    def __init__(self, errors: list[str]) -> None:
        self.errors = errors
        super().__init__("; ".join(errors))


@lru_cache(maxsize=1)
def _validator() -> Draft202012Validator:
    with _SCHEMA_PATH.open(encoding="utf-8") as fh:
        schema = json.load(fh)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema)


def _format_error(error) -> str:
    location = "/".join(str(part) for part in error.absolute_path) or "(root)"
    return f"{location}: {error.message}"


def validate_form(payload: dict[str, Any]) -> None:
    """Validate the schema-defined slice of a template or experiment context.

    ``payload`` may be the whole context (with envelope metadata) or just the
    form slice; only the schema keys are validated. Raises ``FormSchemaError``
    listing every violation if the payload does not comply.
    """
    form = {key: payload[key] for key in _SCHEMA_KEYS if key in payload}
    errors = sorted(_validator().iter_errors(form), key=lambda e: list(e.absolute_path))
    if errors:
        raise FormSchemaError([_format_error(e) for e in errors])
