"""Tests for app/pdf/fonts.py — Noto Sans registration for multilingual rendering."""

from reportlab.pdfbase import pdfmetrics

from app.pdf.fonts import register_fonts
from app.pdf.renderer import generate_pdf


def test_register_fonts_registers_all_four_variants():
    register_fonts()
    for name in (
        "Noto Sans",
        "Noto Sans-Bold",
        "Noto Sans-Oblique",
        "Noto Sans-BoldOblique",
    ):
        assert pdfmetrics.getFont(name) is not None


def test_register_fonts_is_idempotent():
    register_fonts()
    register_fonts()  # must not raise
    assert pdfmetrics.getFont("Noto Sans") is not None


def test_register_fonts_can_encode_european_scripts():
    register_fonts()
    font = pdfmetrics.getFont("Noto Sans")
    # Polish, Greek, Cyrillic — would raise/KeyError-equivalent on Helvetica's
    # WinAnsi encoding; Noto Sans must be able to measure these strings.
    for text in ("Łódź", "Ελληνικά", "Кириллица"):
        width = pdfmetrics.stringWidth(text, "Noto Sans", 12)
        assert width > 0


def test_generate_pdf_renders_european_scripts_by_default():
    components = [
        {
            "id": "greeting",
            "type": "text",
            "rect": [50, 700, 500, 40],
            "content": "Łódź — Ελληνικά — Кириллица",
        }
    ]
    pdf_bytes = generate_pdf({}, components)
    assert pdf_bytes.startswith(b"%PDF")
