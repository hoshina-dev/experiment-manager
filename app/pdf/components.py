"""
Component definitions — pure data structures.
Rect format: [x, y, width, height] in points (1/72 inch).
ReportLab origin is bottom-left; y=0 is the bottom of the page.
Letter page: 612 × 792 points.
"""

from dataclasses import dataclass, field
from typing import Any, Literal

from .parser import extract_fields


@dataclass
class Rect:
    x: float
    y: float
    width: float
    height: float

    @classmethod
    def from_list(cls, data: list[float]) -> "Rect":
        if len(data) != 4:
            raise ValueError(f"Rect requires 4 values, got {len(data)}")
        return cls(x=data[0], y=data[1], width=data[2], height=data[3])


@dataclass
class TextStyle:
    font: str = "Helvetica"
    size: int = 12
    bold: bool = False
    italic: bool = False
    align: Literal["left", "center", "right"] = "left"
    color: str = "#000000"


@dataclass
class Component:
    id: str
    type: str
    rect: Rect

    @property
    def template_fields(self) -> set[str]:
        return set()


@dataclass
class TextComponent(Component):
    content: str = ""
    style: TextStyle = field(default_factory=TextStyle)

    @property
    def template_fields(self) -> set[str]:
        return set(extract_fields(self.content))


@dataclass
class ShapeComponent(Component):
    shape_type: Literal["rect", "line", "circle"] = "rect"
    color: str = "#000000"
    stroke_width: float = 1.0
    fill: bool = False


@dataclass
class PageBreakComponent(Component):
    """Sentinel — signals a page break to the renderer."""

    def __init__(self, id: str = "pagebreak"):
        super().__init__(id=id, type="pagebreak", rect=Rect(0, 0, 0, 0))


def component_from_dict(data: dict[str, Any]) -> Component:
    comp_type = data.get("type")
    comp_id = data.get("id")

    if not comp_id:
        raise ValueError(f"Component missing required 'id' field: {data!r}")

    if comp_type == "text":
        if "rect" not in data:
            raise ValueError(
                f"Text component {comp_id!r} missing required 'rect' field"
            )
        rect = Rect.from_list(data["rect"])
        s = data.get("style", {})
        style = TextStyle(
            font=s.get("font", "Helvetica"),
            size=s.get("size", 12),
            bold=s.get("bold", False),
            italic=s.get("italic", False),
            align=s.get("align", "left"),
            color=s.get("color", "#000000"),
        )
        return TextComponent(
            id=comp_id,
            type="text",
            rect=rect,
            content=data.get("content", ""),
            style=style,
        )

    elif comp_type == "shape":
        if "rect" not in data:
            raise ValueError(
                f"Shape component {comp_id!r} missing required 'rect' field"
            )
        rect = Rect.from_list(data["rect"])
        return ShapeComponent(
            id=comp_id,
            type="shape",
            rect=rect,
            shape_type=data.get("shape_type", "rect"),
            color=data.get("color", "#000000"),
            stroke_width=data.get("stroke_width", 1.0),
            fill=data.get("fill", False),
        )

    elif comp_type == "pagebreak":
        return PageBreakComponent(id=comp_id)

    else:
        raise ValueError(f"Unknown component type: {comp_type!r} (id={comp_id!r})")
