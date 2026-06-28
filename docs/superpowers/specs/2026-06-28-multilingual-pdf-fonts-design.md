# Multilingual Font Support for PDF Reports

## Problem

PDF report generation (`app/pdf/`) uses ReportLab's built-in base-14 fonts (`Helvetica`,
`Times-Roman`, `Courier`). These are Type1 fonts limited to WinAnsi/Latin-1 encoding —
they cannot render Greek, Cyrillic, or several Latin Extended characters used by EU
languages (e.g. Polish `ł`, Czech `č`/`š`, Romanian `ș`/`ț`, Bulgarian Cyrillic, Greek).
The app is used primarily in a European context, so report templates need to support
these scripts.

## Scope

This covers **font/script rendering only**: making PDF output correctly render
multilingual text. It does **not** cover translating UI strings, storing a user/org
locale preference, or formatting dates/numbers per locale — those require a separate,
larger i18n subsystem (string resources, locale storage, Babel/CLDR formatting) and are
out of scope here. The README will document this distinction and note the larger
i18n effort as future work.

## Approach

Register an embeddable, OFL-licensed Noto Sans font family (covers Latin Extended +
Greek + Cyrillic in one font) with ReportLab at app startup, and make it the new
default font for text components, while leaving the existing base-14 fonts available
as opt-in choices for templates that don't need non-Latin scripts.

### Why Noto Sans, registered under suffix-matching names

`_draw_text()` in `app/pdf/renderer.py` already builds bold/italic font names by string
concatenation:

```python
font = comp.style.font
if comp.style.bold and comp.style.italic:
    font += "-BoldOblique"
elif comp.style.bold:
    font += "-Bold"
elif comp.style.italic:
    font += "-Oblique"
```

If the four Noto Sans TTF variants are registered under the names `"Noto Sans"`,
`"Noto Sans-Bold"`, `"Noto Sans-Oblique"`, and `"Noto Sans-BoldOblique"`, this logic
needs **no changes** — it already produces exactly those names when `comp.style.font`
is `"Noto Sans"`. This avoids touching rendering logic at all; only registration and
defaults change.

## Components

### `app/fonts/` (new)

Vendored TTF files:
- `NotoSans-Regular.ttf`
- `NotoSans-Bold.ttf`
- `NotoSans-Italic.ttf`
- `NotoSans-BoldItalic.ttf`
- `OFL.txt` (Open Font License text, required for redistribution)

### `app/pdf/fonts.py` (new)

```python
def register_fonts() -> None:
    """Register vendored TTF fonts with ReportLab. Idempotent."""
```

Uses `reportlab.pdfbase.ttfonts.TTFont` + `reportlab.pdfbase.pdfmetrics.registerFont`
to register the four files under the names above. Raises (does not silently skip) if a
font file is missing — a packaging mistake should fail loudly at startup, not produce
silently garbled PDFs later.

### `main.py` (modified)

Call `register_fonts()` once during the FastAPI `lifespan` startup, before the app
accepts requests — guarantees fonts are available before any PDF generation request
can race ahead of registration.

### `app/pdf/components.py` (modified)

- `TextStyle.font` default: `"Helvetica"` → `"Noto Sans"`
- `component_from_dict()` font default: same change

This is additive: templates that already explicitly set `font: "Helvetica"` /
`"Times-Roman"` / `"Courier"` continue to work unchanged, since those base-14 fonts
need no registration.

### `docs/pdf-report-engine.md` (modified)

Update the `style.font` table to list `"Noto Sans"` (new default) alongside the
existing three base-14 options.

### `README.md` (modified)

New section documenting:
- Why Noto Sans is the default (multilingual rendering for EU languages)
- That this covers rendering, not full UI translation
- A short "future work" pointer to the larger i18n subsystem (locale storage,
  translated string resources, date/number formatting) as a separate, not-yet-built
  effort

## Error Handling

- `register_fonts()` raises `FileNotFoundError` (or lets ReportLab's own error
  surface) if a vendored TTF is missing — caught nowhere, intentionally, so a broken
  deploy fails at startup rather than producing bad PDFs.
- No runtime fallback logic is introduced: if a template specifies an unregistered
  font name, ReportLab's existing `KeyError` behavior on `setFont()` is preserved
  unchanged.

## Testing

New `tests/test_pdf_fonts.py`:
- `register_fonts()` can be called twice without error (idempotency).
- `generate_pdf()` succeeds (no exception) for a template containing Greek, Cyrillic,
  and Polish-diacritic text in a text component using the default font.
- The above test would fail today (before this change) since `Helvetica` cannot encode
  Greek/Cyrillic — confirms the test is a real regression check, not a tautology.

## Checkpoints (one commit/push each, in order)

1. **Vendor fonts + registration module.** Add `app/fonts/*.ttf` + `OFL.txt` and
   `app/pdf/fonts.py` with `register_fonts()`. Inert — nothing calls it yet.
2. **Wire it in.** Call `register_fonts()` from `main.py` startup; switch defaults in
   `app/pdf/components.py`; update `docs/pdf-report-engine.md`.
3. **Tests.** Add `tests/test_pdf_fonts.py` per the Testing section above.
4. **README.** Add the localization/font-strategy section with the future-i18n note.

## Out of Scope (explicitly deferred)

- User/org locale storage (DB column, settings).
- Translated UI/report label strings (Babel/gettext or JSON resource files).
- Locale-aware date/number formatting.
- Non-European scripts (CJK, Arabic, etc.) — Noto Sans (this variant) doesn't cover
  these; would need additional font files and a script-detection fallback chain if
  ever needed.
