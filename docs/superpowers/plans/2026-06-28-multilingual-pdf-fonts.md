# Multilingual PDF Font Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make PDF report text components render Greek, Cyrillic, and Latin-Extended characters (Polish, Czech, Romanian, etc.) correctly by default, instead of the current Helvetica-only base-14 fonts which can't encode them.

**Architecture:** Vendor the four static Noto Sans TTF weights (Regular/Bold/Italic/BoldItalic — one family covering Latin Extended + Greek + Cyrillic) under `app/fonts/`, register them with ReportLab at FastAPI startup under names that match the existing `-Bold`/`-Oblique`/`-BoldOblique` suffix convention already used in `_draw_text()`, and make `"Noto Sans"` the new default font. No rendering logic changes — only registration + defaults.

**Tech Stack:** Python 3.12, FastAPI (lifespan startup hook), ReportLab 4.5.1 (`reportlab.pdfbase.ttfonts.TTFont`, `reportlab.pdfbase.pdfmetrics`), pytest.

## Global Constraints

- Spec: `docs/superpowers/specs/2026-06-28-multilingual-pdf-fonts-design.md`
- Font files must be registered under exactly these names: `"Noto Sans"`, `"Noto Sans-Bold"`, `"Noto Sans-Oblique"`, `"Noto Sans-BoldOblique"` (matches `_draw_text()`'s existing suffix logic in `app/pdf/renderer.py:62-67` — do not change that logic).
- `register_fonts()` must be idempotent (callable more than once without error) and must raise loudly if a vendored font file is missing — no silent fallback.
- Existing base-14 fonts (`Helvetica`, `Times-Roman`, `Courier`) must keep working unchanged for templates that already set them explicitly.
- Out of scope: locale storage, translated UI strings, date/number formatting, non-European scripts (CJK/Arabic). Do not implement these.
- This is a real lab/dev machine, not a throwaway sandbox — vendored binary font files go through normal `git add`, no destructive git operations needed.

---

### Task 1: Vendor Noto Sans fonts + registration module

**Files:**
- Create: `app/fonts/NotoSans-Regular.ttf`
- Create: `app/fonts/NotoSans-Bold.ttf`
- Create: `app/fonts/NotoSans-Italic.ttf`
- Create: `app/fonts/NotoSans-BoldItalic.ttf`
- Create: `app/fonts/OFL.txt`
- Create: `app/pdf/fonts.py`
- Test: `tests/test_pdf_fonts.py`

**Interfaces:**
- Consumes: nothing from earlier tasks (first task).
- Produces: `register_fonts() -> None` in `app/pdf/fonts.py`. Later tasks (Task 2) import and call this from `main.py`. Registers TTFonts under the names `"Noto Sans"`, `"Noto Sans-Bold"`, `"Noto Sans-Oblique"`, `"Noto Sans-BoldOblique"`.

- [ ] **Step 1: Vendor the four TTF files**

This machine already has the exact static (non-variable) Noto Sans cut bundled with LibreOffice, which is what ReportLab needs (one weight/style per file, not a variable font). Copy them into the repo:

```bash
mkdir -p app/fonts
cp "/Applications/LibreOffice.app/Contents/Resources/fonts/truetype/NotoSans-Regular.ttf" app/fonts/NotoSans-Regular.ttf
cp "/Applications/LibreOffice.app/Contents/Resources/fonts/truetype/NotoSans-Bold.ttf" app/fonts/NotoSans-Bold.ttf
cp "/Applications/LibreOffice.app/Contents/Resources/fonts/truetype/NotoSans-Italic.ttf" app/fonts/NotoSans-Italic.ttf
cp "/Applications/LibreOffice.app/Contents/Resources/fonts/truetype/NotoSans-BoldItalic.ttf" app/fonts/NotoSans-BoldItalic.ttf
ls -la app/fonts/
```

Expected: four `.ttf` files listed, each several hundred KB (NOT zero bytes — if `cp` silently fails because the source path doesn't exist on the machine running this step, fall back to downloading the static instances from the Noto Sans GitHub release instead: `https://github.com/notofonts/notofonts.github.io/raw/main/fonts/NotoSans/hinted/ttf/NotoSans-Regular.ttf`, `.../NotoSans-Bold.ttf`, `.../NotoSans-Italic.ttf`, `.../NotoSans-BoldItalic.ttf`).

- [ ] **Step 2: Vendor the OFL license text**

```bash
curl -s -o app/fonts/OFL.txt "https://raw.githubusercontent.com/google/fonts/main/ofl/notosans/OFL.txt"
head -5 app/fonts/OFL.txt
```

Expected: first lines show `Copyright 2022 The Noto Project Authors...` and `This Font Software is licensed under the SIL Open Font License, Version 1.1.`

- [ ] **Step 3: Write the failing test**

Create `tests/test_pdf_fonts.py`:

```python
"""Tests for app/pdf/fonts.py — Noto Sans registration for multilingual rendering."""

from reportlab.pdfbase import pdfmetrics

from app.pdf.fonts import register_fonts


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
```

- [ ] **Step 4: Run test to verify it fails**

Run: `uv run pytest tests/test_pdf_fonts.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'app.pdf.fonts'`

- [ ] **Step 5: Write the registration module**

Create `app/pdf/fonts.py`:

```python
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
```

- [ ] **Step 6: Run test to verify it passes**

Run: `uv run pytest tests/test_pdf_fonts.py -v`
Expected: 3 passed

- [ ] **Step 7: Commit**

```bash
git add app/fonts/ app/pdf/fonts.py tests/test_pdf_fonts.py
git commit -m "feat: vendor Noto Sans fonts and add ReportLab registration module"
```

---

### Task 2: Wire registration into app startup and switch defaults

**Files:**
- Modify: `main.py:1-33` (add import, call `register_fonts()` in `lifespan`)
- Modify: `app/pdf/components.py:30` (`TextStyle.font` default)
- Modify: `app/pdf/components.py:90` (`component_from_dict()` font default)
- Modify: `docs/pdf-report-engine.md` (font table, ~lines 99-104)
- Test: `tests/test_pdf_fonts.py` (extend with an end-to-end `generate_pdf` test)

**Interfaces:**
- Consumes: `register_fonts()` from `app/pdf/fonts.py` (Task 1).
- Produces: `TextStyle.font` and `component_from_dict()` now default to `"Noto Sans"` instead of `"Helvetica"`. Later tasks (Task 3 README) reference this as the documented default.

- [ ] **Step 1: Write the failing end-to-end test**

Add to `tests/test_pdf_fonts.py`:

```python
from app.pdf.renderer import generate_pdf


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
```

This relies on `component_from_dict()`'s default font being something that can
encode these scripts. Today that default is `"Helvetica"`, which will raise
when ReportLab tries to encode the Cyrillic/Greek text.

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_pdf_fonts.py::test_generate_pdf_renders_european_scripts_by_default -v`
Expected: FAIL (exception raised while encoding/drawing the Greek or Cyrillic substring with Helvetica)

- [ ] **Step 3: Switch the default font in `app/pdf/components.py`**

Change line 30:

```python
@dataclass
class TextStyle:
    font: str = "Noto Sans"
```

Change line 90 (inside `component_from_dict`):

```python
        style = TextStyle(
            font=s.get("font", "Noto Sans"),
```

- [ ] **Step 4: Wire `register_fonts()` into `main.py` startup**

In `main.py`, add the import alongside the existing `app.pdf` import (after line 17):

```python
from app.pdf.fonts import register_fonts
from app.pdf.r2_client import check_connection
```

At the top of `lifespan()` (before the existing `check_connection(r2_settings)` call at line 28), add:

```python
@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    register_fonts()
    try:
        check_connection(r2_settings)
```

Registering fonts before the R2 check means a missing/corrupt font file fails
startup immediately, before the app even checks its other dependencies.

- [ ] **Step 5: Run test to verify it passes**

Run: `uv run pytest tests/test_pdf_fonts.py -v`
Expected: 4 passed

- [ ] **Step 6: Update `docs/pdf-report-engine.md`**

Find the `style.font` table row (around line 99):

```markdown
| `font` | string | `"Helvetica"` | `"Helvetica"`, `"Times-Roman"`, `"Courier"` |
```

Replace with:

```markdown
| `font` | string | `"Noto Sans"` | `"Noto Sans"` (default — supports Latin Extended, Greek, Cyrillic), `"Helvetica"`, `"Times-Roman"`, `"Courier"` |
```

- [ ] **Step 7: Run the full PDF test suite to check for regressions**

Run: `uv run pytest tests/ -v -k "pdf or report"`
Expected: all pass (no test in this repo currently asserts on the literal string `"Helvetica"`, confirmed during design research, so this default change should not break anything)

- [ ] **Step 8: Commit**

```bash
git add main.py app/pdf/components.py docs/pdf-report-engine.md tests/test_pdf_fonts.py
git commit -m "feat: register Noto Sans at startup and make it the default PDF font"
```

---

### Task 3: Document the localization/font strategy in the README

**Files:**
- Modify: `README.md` (new `## Localization` section, inserted after the `### PDF reports` subsection ending at line 130, before `## Data model` at line 132)

**Interfaces:**
- Consumes: nothing code-level — this is documentation only, describing behavior shipped in Tasks 1–2.
- Produces: nothing consumed by later tasks (final task in this plan).

- [ ] **Step 1: Insert the README section**

In `README.md`, after this existing block (ends at line 130):

```markdown
| `GET` | `/api/experiments/{exp_id}/report/download` | Get presigned download URL → `{ "url": "...", "expires_in": 900 }` |
```

and before:

```markdown
## Data model
```

insert:

```markdown
## Localization

PDF reports default to the **Noto Sans** font (`app/fonts/`, registered in
`app/pdf/fonts.py`), which covers Latin Extended, Greek, and Cyrillic in a
single embedded font. This means report text in any EU language — including
ones with diacritics (Polish, Czech, Romanian, Lithuanian...), Greek, or
Bulgarian Cyrillic — renders correctly without per-template font juggling.
Templates can still opt into ReportLab's built-in `Helvetica`, `Times-Roman`,
or `Courier` for ASCII-only content (see `docs/pdf-report-engine.md`).

This covers **rendering** multilingual text, not full UI/string
translation. There is currently no locale storage, no translated string
resources, and no locale-aware date/number formatting — building that out
(if ever needed) is a separate, larger effort tracked as future work, not
implemented here.
```

- [ ] **Step 2: Verify the README renders sensibly**

Run: `grep -n '^#' README.md`
Expected: `## Localization` appears between `### PDF reports` and `## Data model` in the heading list.

- [ ] **Step 3: Commit**

```bash
git add README.md
git commit -m "docs: document the Noto Sans localization strategy in README"
```

---

## Self-Review Notes

- **Spec coverage:** Spec's four checkpoints map 1:1 — Task 1 = checkpoint 1, Task 2 = checkpoints 2 (merged tests into Task 2 rather than a separate Task 3, since the registration and the test that proves it works are one reviewable unit; the spec's checkpoint 3 testing content is satisfied inside Task 2's steps), Task 3 = checkpoint 4 (README). All "Out of Scope" items from the spec are explicitly listed in Global Constraints and untouched by any task.
- **Naming consistency:** `register_fonts()` signature (`() -> None`) is identical everywhere it's referenced (Task 1 produces it, Task 2 imports and calls it). Font name strings (`"Noto Sans"`, `"Noto Sans-Bold"`, `"Noto Sans-Oblique"`, `"Noto Sans-BoldOblique"`) are identical across `app/pdf/fonts.py`, the test file, and the Global Constraints section.
- **No placeholders:** every step has literal code/commands; no "add appropriate tests" or "TBD" language.
