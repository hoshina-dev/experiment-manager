"""
Template engine — parse components, validate context, expand self-references.
Zero rendering dependencies; safe to import anywhere.
"""

from typing import Any

from .components import Component, component_from_dict
from .parser import interpolate_template


class TemplateEngine:
    def __init__(self, components: list[dict[str, Any]]) -> None:
        self.components: list[Component] = [component_from_dict(c) for c in components]
        self.fields: set[str] = self._extract_all_fields()

    def validate(self, context: dict[str, Any]) -> dict[str, str]:
        """Return missing-field errors keyed by field name. Empty dict means valid."""
        return {f: f"Missing required field: {f}" for f in self.fields - set(context.keys())}

    def build_context(self, context: dict[str, Any]) -> dict[str, Any]:
        """Expand {{template}} self-reference in context before rendering."""
        ctx = dict(context)
        raw_template = ctx.get("template", "")
        if raw_template:
            ctx["template"] = interpolate_template(raw_template, ctx)
        return ctx

    def _extract_all_fields(self) -> set[str]:
        fields: set[str] = set()
        for comp in self.components:
            fields.update(comp.template_fields)
        return fields
