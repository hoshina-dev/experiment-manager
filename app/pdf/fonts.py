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


# Maps a font family's *display* name to the registered ReportLab name for
# each (bold, italic) combination. Needed because ReportLab's own base-14
# naming isn't a consistent "family" + "-Bold"/"-Oblique"/"-BoldOblique"
# suffix — Times breaks the pattern (drops "-Roman", uses "Italic" not
# "Oblique") — and any future custom/uploaded font is even less likely to
# follow it. Registering a family here (built-in or custom) is what makes it
# usable from `style.font`; resolve_font() is the only place that should
# turn a family name into the name ReportLab actually has registered.
FONT_FAMILIES: dict[str, dict[tuple[bool, bool], str]] = {
    "Helvetica": {
        (False, False): "Helvetica",
        (True, False): "Helvetica-Bold",
        (False, True): "Helvetica-Oblique",
        (True, True): "Helvetica-BoldOblique",
    },
    "Courier": {
        (False, False): "Courier",
        (True, False): "Courier-Bold",
        (False, True): "Courier-Oblique",
        (True, True): "Courier-BoldOblique",
    },
    "Times-Roman": {
        (False, False): "Times-Roman",
        (True, False): "Times-Bold",
        (False, True): "Times-Italic",
        (True, True): "Times-BoldItalic",
    },
    "Noto Sans": {
        (False, False): "Noto Sans",
        (True, False): "Noto Sans-Bold",
        (False, True): "Noto Sans-Oblique",
        (True, True): "Noto Sans-BoldOblique",
    },
}


def resolve_font(family: str, bold: bool, italic: bool) -> str:
    """The ReportLab-registered name for `family` in the given style.

    Falls back to naive "-Bold"/"-Oblique"/"-BoldOblique" suffixing for a
    family not in FONT_FAMILIES, so an unregistered/unknown font name fails
    the same way it always has (a clear ReportLab KeyError at setFont) rather
    than silently changing behavior.
    """
    variants = FONT_FAMILIES.get(family)
    if variants is not None:
        return variants[(bold, italic)]
    if bold and italic:
        return f"{family}-BoldOblique"
    if bold:
        return f"{family}-Bold"
    if italic:
        return f"{family}-Oblique"
    return family
