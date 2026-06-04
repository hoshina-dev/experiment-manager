from io import BytesIO
from typing import Any

from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas as rl_canvas

from .components import PageBreakComponent, ShapeComponent, TextComponent
from .context import flatten_context
from .engine import TemplateEngine
from .parser import interpolate_template


def generate_pdf(data: dict[str, Any], components: list[dict]) -> bytes:
    """Top-level entry point: flatten context, build, render. Returns PDF bytes."""
    context = flatten_context(data)
    engine = TemplateEngine(components)
    ctx = engine.build_context(context)
    return render_pdf(engine.components, ctx)


def render_pdf(components: list, context: dict[str, Any]) -> bytes:
    if not components:
        raise ValueError("render_pdf() called with no components.")

    buf = BytesIO()
    c = rl_canvas.Canvas(buf, pagesize=letter)
    page_width, _ = letter
    c.setTitle("PDF Report")

    total_pages = sum(1 for comp in components if isinstance(comp, PageBreakComponent)) + 1
    current_page = 1

    def _draw_page_number() -> None:
        label = f"Page {current_page} of {total_pages}"
        label_w = c.stringWidth(label, "Helvetica", 10)
        c.setFont("Helvetica", 10)
        c.setFillColor(HexColor("#000000"))
        c.drawString((page_width - label_w) / 2, 30, label)

    for comp in components:
        if isinstance(comp, PageBreakComponent):
            _draw_page_number()
            c.showPage()
            current_page += 1
        elif isinstance(comp, TextComponent):
            _draw_text(c, comp, context)
        elif isinstance(comp, ShapeComponent):
            _draw_shape(c, comp)

    _draw_page_number()
    c.save()
    return buf.getvalue()


def _draw_text(c: Any, comp: TextComponent, context: dict[str, Any]) -> None:
    text = interpolate_template(comp.content, context)

    font = comp.style.font
    if comp.style.bold and comp.style.italic:
        font += "-BoldOblique"
    elif comp.style.bold:
        font += "-Bold"
    elif comp.style.italic:
        font += "-Oblique"

    c.setFont(font, comp.style.size)
    c.setFillColor(HexColor(comp.style.color))

    size = comp.style.size
    line_h = size * 1.2
    max_w = comp.rect.width
    align = comp.style.align
    rx = comp.rect.x
    y = comp.rect.y + comp.rect.height - size

    def _draw_line(line_text: str) -> float:
        line_w = c.stringWidth(line_text, font, size)
        if align == "center":
            lx = rx + (max_w - line_w) / 2
        elif align == "right":
            lx = rx + max_w - line_w
        else:
            lx = rx
        c.drawString(lx, y, line_text)
        return y - line_h

    for para in text.split("\n"):
        if not para:
            y -= line_h
            continue
        words = para.split(" ")
        line = ""
        for word in words:
            candidate = f"{line} {word}" if line else word
            if line and c.stringWidth(candidate, font, size) > max_w:
                y = _draw_line(line)
                line = word
            else:
                line = candidate
        if line:
            y = _draw_line(line)

    c.setFillColor(HexColor("#000000"))


def _draw_shape(c: Any, comp: ShapeComponent) -> None:
    color = HexColor(comp.color)
    c.setStrokeColor(color)
    c.setLineWidth(comp.stroke_width)
    fill_flag = 1 if comp.fill else 0
    if comp.fill:
        c.setFillColor(color)

    x, y, w, h = comp.rect.x, comp.rect.y, comp.rect.width, comp.rect.height
    if comp.shape_type == "rect":
        c.rect(x, y, w, h, stroke=1, fill=fill_flag)
    elif comp.shape_type == "line":
        c.line(x, y + h / 2, x + w, y + h / 2)
    elif comp.shape_type == "circle":
        r = min(w, h) / 2
        c.circle(x + w / 2, y + h / 2, r, stroke=1, fill=fill_flag)
    else:
        raise ValueError(f"Unknown shape_type: {comp.shape_type!r}")
