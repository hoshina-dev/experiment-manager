"""Tests for app/pdf/fonts.py — Noto Sans registration for multilingual rendering."""

import multiprocessing
from concurrent.futures import ProcessPoolExecutor

from reportlab.pdfbase import pdfmetrics

from app.pdf.components import TextStyle, component_from_dict
from app.pdf.fonts import register_fonts, resolve_font
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


def _render_in_subprocess(components):
    # Runs inside a worker process with a fresh font registry — only
    # register_fonts() called via the executor's initializer (not anything
    # inherited from the parent) makes this work.
    return generate_pdf({}, components)


def test_generate_pdf_works_in_fresh_subprocess_via_executor_initializer():
    """Regression test for the spawn-method KeyError bug.

    PDF rendering happens inside ProcessPoolExecutor worker subprocesses
    (see app/report_worker.py), not in the parent FastAPI process. ReportLab's
    font registry is process-local, in-memory state, so registering fonts
    only in the parent (e.g. in main.py's lifespan) does not propagate to
    worker subprocesses started with the "spawn" method — every platform
    where "spawn" is the default (macOS today; everywhere from Python 3.14).
    main.py must construct its ProcessPoolExecutor with
    initializer=register_fonts so each worker registers fonts once at
    startup. This test mirrors that exact construction, pinned to "spawn"
    so it's meaningful regardless of platform default.
    """
    components = [
        {
            "id": "greeting",
            "type": "text",
            "rect": [50, 700, 500, 40],
            "content": "Łódź — Ελληνικά — Кириллица",
        }
    ]
    ctx = multiprocessing.get_context("spawn")
    with ProcessPoolExecutor(
        max_workers=1, initializer=register_fonts, mp_context=ctx
    ) as executor:
        future = executor.submit(_render_in_subprocess, components)
        pdf_bytes = future.result(timeout=30)
    assert pdf_bytes.startswith(b"%PDF")


def test_resolve_font_times_roman_bold_and_italic_variants():
    """Regression test: ReportLab names Times' variants Times-Bold /
    Times-Italic / Times-BoldItalic — not Times-Roman-Bold /
    Times-Roman-Oblique / Times-Roman-BoldOblique, which naive suffixing
    used to produce and which were never registered (KeyError at render).
    """
    assert resolve_font("Times-Roman", False, False) == "Times-Roman"
    assert resolve_font("Times-Roman", True, False) == "Times-Bold"
    assert resolve_font("Times-Roman", False, True) == "Times-Italic"
    assert resolve_font("Times-Roman", True, True) == "Times-BoldItalic"
    for name in ("Times-Roman", "Times-Bold", "Times-Italic", "Times-BoldItalic"):
        assert pdfmetrics.getFont(name) is not None


def test_resolve_font_known_families_follow_suffix_convention():
    for family in ("Helvetica", "Courier", "Noto Sans"):
        assert resolve_font(family, False, False) == family
        assert resolve_font(family, True, False) == f"{family}-Bold"
        assert resolve_font(family, False, True) == f"{family}-Oblique"
        assert resolve_font(family, True, True) == f"{family}-BoldOblique"


def test_resolve_font_unknown_family_falls_back_to_naive_suffixing():
    """An unregistered family isn't silently swallowed — it fails at
    setFont() exactly like before, rather than resolve_font() masking it."""
    assert resolve_font("Comic Sans", False, False) == "Comic Sans"
    assert resolve_font("Comic Sans", True, False) == "Comic Sans-Bold"
    assert resolve_font("Comic Sans", False, True) == "Comic Sans-Oblique"
    assert resolve_font("Comic Sans", True, True) == "Comic Sans-BoldOblique"


def test_generate_pdf_renders_times_roman_bold():
    components = [
        {
            "id": "heading",
            "type": "text",
            "rect": [50, 700, 500, 40],
            "content": "Bold Times heading",
            "style": {"font": "Times-Roman", "bold": True},
        }
    ]
    pdf_bytes = generate_pdf({}, components)
    assert pdf_bytes.startswith(b"%PDF")


def test_default_font_is_noto_sans():
    """Guards against a future revert of the default font back to Helvetica."""
    assert TextStyle().font == "Noto Sans"
    comp = component_from_dict(
        {"id": "x", "type": "text", "rect": [0, 0, 10, 10], "content": "hi"}
    )
    assert comp.style.font == "Noto Sans"
