"""Registers vendored Noto Sans fonts with ReportLab for multilingual PDF text.

Noto Sans covers Latin Extended, Greek, and Cyrillic in one family, unlike
ReportLab's built-in base-14 fonts (Helvetica/Times-Roman/Courier), which are
limited to WinAnsi/Latin-1 and cannot render e.g. Polish, Greek, or Bulgarian
text.

Registered under names that match the existing "-Bold"/"-Oblique"/
"-BoldOblique" suffix convention in app/pdf/renderer.py, so no rendering
logic needs to change.
"""

from pathlib import Path

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

_FONTS_DIR = Path(__file__).resolve().parent.parent / "fonts"

_VARIANTS = {
    "Noto Sans": "NotoSans-Regular.ttf",
    "Noto Sans-Bold": "NotoSans-Bold.ttf",
    "Noto Sans-Oblique": "NotoSans-Italic.ttf",
    "Noto Sans-BoldOblique": "NotoSans-BoldItalic.ttf",
}


def register_fonts() -> None:
    """Register the four Noto Sans variants with ReportLab. Safe to call more than once."""
    for font_name, filename in _VARIANTS.items():
        path = _FONTS_DIR / filename
        if not path.is_file():
            raise FileNotFoundError(
                f"Required font file missing: {path}. "
                f"Expected vendored Noto Sans TTF files under {_FONTS_DIR}."
            )
        pdfmetrics.registerFont(TTFont(font_name, str(path)))
