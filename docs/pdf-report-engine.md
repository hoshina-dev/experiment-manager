# PDF Report Engine

This document describes how to author a `pdf_templates.components` value — the JSON array that defines a PDF report layout. An AI reading this document has everything it needs to produce any layout.

---

## Overview

A report is defined as an ordered array of **components**. Components are rendered top-to-bottom in array order. Each component is a JSON object with at minimum:

| Field | Type | Required | Description |
|---|---|---|---|
| `id` | string | Yes | Unique identifier within the components array. Used for debugging only. |
| `type` | string | Yes | One of: `"text"`, `"shape"`, `"pagebreak"` |
| `rect` | array | Depends on type | `[x, y, width, height]` in points. Not used by `pagebreak`. |

---

## Coordinate System

- Page size: **Letter — 612 × 792 points** (1 point = 1/72 inch)
- Origin `(0, 0)` is the **bottom-left** corner of the page
- `y` increases upward — higher `y` = closer to the top
- Typical usable area: `x` from `36` to `576` (36pt margins), `y` from `72` to `756`

```
y=792 ┌────────────────────────────┐
      │  top of page               │
      │  header area  y ≈ 720–756  │
      │  body area    y ≈ 120–700  │
      │  footer area  y ≈  60–100  │
y=0   └────────────────────────────┘
      x=0                      x=612
```

The renderer automatically prints **"Page N of M"** centred at `y=30` on every page — leave `y < 60` clear.

---

## Template Variables — `{{field}}`

Any string field in a component can contain `{{field_name}}` placeholders. The engine replaces them at render time using a flattened render context built from the experiment context.

For the full list of available variables and how the render context is built, see `docs/experiment-context.md`.

**Key rules:**
- `calculations[name].result` is used for the same key when present — `{{my_var}}` renders the computed value after `POST /calculate` is called, and the formula string before.
- Unresolved `{{field}}` placeholders are left as-is in the output — no crash.
- Lists (multi-select, checkbox-group, tags) are skipped and cannot be used in placeholders.
- Always call `POST /calculate` before generating a PDF if the experiment template uses `calculations`.

---

## Component Types

---

### `text`

Renders a string inside a bounding box. Supports word-wrap and multi-line via `\n`.

```json
{
  "id": "my_label",
  "type": "text",
  "rect": [36, 700, 540, 20],
  "content": "Sample mass: {{sample_mass}} g",
  "style": {
    "font": "Helvetica",
    "size": 12,
    "bold": false,
    "italic": false,
    "align": "left",
    "color": "#000000"
  }
}
```

#### `rect` — `[x, y, width, height]`

| Field | Meaning |
|---|---|
| `x` | Left edge of the text box |
| `y` | Bottom edge of the text box |
| `width` | Maximum line width before word-wrap |
| `height` | Used to position the first line: text starts at `y + height - font_size` |

For a single line of text, set `height` ≈ `font_size + 4`.
For multi-line blocks, set `height` = estimated total height (lines × font_size × 1.2).

#### `content`

Any string. May contain `{{field}}` placeholders. Newlines (`\n`) start a new paragraph. Long lines word-wrap at the `width` boundary.

#### `style`

| Field | Type | Default | Values |
|---|---|---|---|
| `font` | string | `"Noto Sans"` | `"Noto Sans"` (default — supports Latin Extended, Greek, Cyrillic), `"Helvetica"`, `"Times-Roman"`, `"Courier"` |
| `size` | int | `12` | Points. Common: 8 (fine print), 10 (body), 12 (normal), 14–18 (subheading), 20–24 (hero) |
| `bold` | bool | `false` | Appends `-Bold` to the font name |
| `italic` | bool | `false` | Appends `-Oblique` (Helvetica) or `-Italic` (Times) |
| `align` | string | `"left"` | `"left"`, `"center"`, `"right"` |
| `color` | string | `"#000000"` | Any CSS hex colour, e.g. `"#1565C0"` |

Bold + italic together → `-BoldOblique`.

---

### `shape`

Renders a geometric primitive. No content or interpolation.

```json
{
  "id": "header_bg",
  "type": "shape",
  "shape_type": "rect",
  "rect": [36, 720, 540, 48],
  "color": "#1565C0",
  "fill": true,
  "stroke_width": 0
}
```

#### Fields

| Field | Type | Default | Description |
|---|---|---|---|
| `shape_type` | string | `"rect"` | `"rect"`, `"line"`, `"circle"` |
| `rect` | array | required | `[x, y, width, height]` |
| `color` | string | `"#000000"` | Hex colour — applies to both stroke and fill |
| `fill` | bool | `false` | Fill the interior with `color` |
| `stroke_width` | float | `1.0` | Border/line thickness in points. Set `0` for invisible border on filled shapes |

#### `shape_type` behaviour

**`rect`** — Draws a rectangle at `[x, y, width, height]`.

```json
{ "shape_type": "rect", "rect": [36, 700, 540, 40], "color": "#E3F2FD", "fill": true, "stroke_width": 0 }
```

**`line`** — Draws a horizontal line. `x` and `width` define start and length. `y` and `height` are averaged to find the vertical centre (`y + height/2`). Use `height: 1` or `height: 2` for a thin rule.

```json
{ "shape_type": "line", "rect": [36, 690, 540, 1], "color": "#BDBDBD", "stroke_width": 1 }
```

**`circle`** — Draws a circle centred in the bounding box. Radius = `min(width, height) / 2`.

```json
{ "shape_type": "circle", "rect": [270, 400, 60, 60], "color": "#1565C0", "fill": true, "stroke_width": 0 }
```

---

### `pagebreak`

Ends the current page and starts a new one. The renderer prints "Page N of M" at the bottom of each page automatically.

```json
{
  "id": "page_break_1",
  "type": "pagebreak"
}
```

`rect` is not required and is ignored.

---

## Layout Patterns

### Header band

A filled rectangle behind white text. Draw the shape first, then the text on top.

```json
{ "id": "hdr_bg",    "type": "shape", "shape_type": "rect", "rect": [36, 720, 540, 48], "color": "#1565C0", "fill": true, "stroke_width": 0 },
{ "id": "hdr_title", "type": "text",  "rect": [46, 726, 520, 36], "content": "REPORT TITLE",
  "style": { "font": "Helvetica", "size": 18, "bold": true, "color": "#FFFFFF", "align": "center" } }
```

Draw order matters: shape before text. Components are rendered in array order.

### Section separator

A label followed by a hairline rule.

```json
{ "id": "sec_label", "type": "text",  "rect": [36, 630, 540, 14], "content": "MEASUREMENTS",
  "style": { "font": "Helvetica", "size": 9, "bold": true, "color": "#1565C0" } },
{ "id": "sec_line",  "type": "shape", "shape_type": "line", "rect": [36, 627, 540, 1], "color": "#BBDEFB", "stroke_width": 1 }
```

### Highlighted result box

A background rectangle, an optional border, a small label, and a large value.

```json
{ "id": "res_bg",     "type": "shape", "shape_type": "rect",  "rect": [36, 590, 540, 56], "color": "#E3F2FD", "fill": true,  "stroke_width": 0 },
{ "id": "res_border", "type": "shape", "shape_type": "rect",  "rect": [36, 590, 540, 56], "color": "#1565C0", "fill": false, "stroke_width": 1 },
{ "id": "res_label",  "type": "text",  "rect": [46, 628, 520, 12], "content": "RESULT",
  "style": { "font": "Helvetica", "size": 9, "bold": true, "color": "#1565C0", "align": "center" } },
{ "id": "res_value",  "type": "text",  "rect": [46, 598, 520, 24], "content": "{{result_field}}",
  "style": { "font": "Helvetica", "size": 20, "bold": true, "color": "#0D47A1", "align": "center" } }
```

### Two-column row

Two text components side by side by splitting the 540pt width.

```json
{ "id": "col_left",  "type": "text", "rect": [36,  650, 260, 14], "content": "Left label: {{left_val}}",  "style": { "font": "Helvetica", "size": 11, "color": "#212121" } },
{ "id": "col_right", "type": "text", "rect": [316, 650, 260, 14], "content": "Right label: {{right_val}}", "style": { "font": "Helvetica", "size": 11, "color": "#212121" } }
```

Left column: `x=36, width=260`. Right column: `x=316, width=260` (316 = 36 + 260 + 20 gap).

### Footer

A hairline at `y=60` and small italic text below it. Keep everything above `y=60` for body content.

```json
{ "id": "footer_line", "type": "shape", "shape_type": "line", "rect": [36, 60, 540, 1], "color": "#BDBDBD", "stroke_width": 1 },
{ "id": "footer_text", "type": "text",  "rect": [36, 44, 540, 12], "content": "Report — {{name}}",
  "style": { "font": "Helvetica", "size": 8, "italic": true, "color": "#9E9E9E", "align": "center" } }
```

### Multi-page report

Insert a `pagebreak` component wherever you want a new page. Each page is fully independent — repeat headers/footers by including them after the pagebreak.

```json
{ "id": "page1_footer_line", "type": "shape", ... },
{ "id": "page1_footer_text", "type": "text",  ..., "content": "Continued on next page" },
{ "id": "break_1", "type": "pagebreak" },
{ "id": "page2_header_bg",   "type": "shape", ... },
{ "id": "page2_header_text", "type": "text",  ... }
```

---

## Vertical spacing guide

| Purpose | Typical `height` | Notes |
|---|---|---|
| Large hero value (20–24pt font) | 24–30 | `y + height - size` sets baseline |
| Normal body row (11pt) | 16 | Leaves 5pt breathing room |
| Small label / caption (9pt) | 14 | |
| Section rule line | 1–2 | `stroke_width` does the visual weight |
| Header band (18pt title) | 42–52 | Enough padding around text |
| Multi-line note block | `lines × 12` | font 10, line_height ≈ 12 |

Rows stack downward: each row's `y` = previous row's `y` − row `height` − gap (usually 2–4pt).

---

## Available fonts

Only the 14 PDF built-in fonts are available (no file uploads).

| Family | Variants |
|---|---|
| `Helvetica` | `Helvetica`, `-Bold`, `-Oblique`, `-BoldOblique` |
| `Times-Roman` | `Times-Roman`, `-Bold`, `-Italic`, `-BoldItalic` |
| `Courier` | `Courier`, `-Bold`, `-Oblique`, `-BoldOblique` |

`bold: true` and `italic: true` in the style object select the correct variant automatically.

---

## Complete minimal example

A one-page report for a simple measurement:

```json
[
  { "id": "hdr_bg",    "type": "shape", "shape_type": "rect", "rect": [36, 720, 540, 42],
    "color": "#1A237E", "fill": true, "stroke_width": 0 },
  { "id": "hdr_title", "type": "text", "rect": [46, 726, 520, 28],
    "content": "ANALYSIS REPORT",
    "style": { "font": "Helvetica", "size": 16, "bold": true, "color": "#FFFFFF", "align": "center" } },

  { "id": "sec_inputs", "type": "text", "rect": [36, 694, 540, 14],
    "content": "INPUTS",
    "style": { "font": "Helvetica", "size": 9, "bold": true, "color": "#3949AB" } },
  { "id": "sec_line",   "type": "shape", "shape_type": "line", "rect": [36, 691, 540, 1],
    "color": "#C5CAE9", "stroke_width": 1 },

  { "id": "row1", "type": "text", "rect": [36, 673, 260, 14],
    "content": "Sample mass: {{sample_mass}} g",
    "style": { "font": "Helvetica", "size": 11, "color": "#212121" } },

  { "id": "res_bg",     "type": "shape", "shape_type": "rect", "rect": [36, 590, 540, 52],
    "color": "#E8EAF6", "fill": true, "stroke_width": 0 },
  { "id": "res_border", "type": "shape", "shape_type": "rect", "rect": [36, 590, 540, 52],
    "color": "#3949AB", "fill": false, "stroke_width": 1.5 },
  { "id": "res_label",  "type": "text", "rect": [46, 624, 520, 12],
    "content": "RESULT",
    "style": { "font": "Helvetica", "size": 9, "bold": true, "color": "#3949AB", "align": "center" } },
  { "id": "res_value",  "type": "text", "rect": [46, 598, 520, 22],
    "content": "{{template}}",
    "style": { "font": "Helvetica", "size": 18, "bold": true, "color": "#1A237E", "align": "center" } },

  { "id": "footer_line", "type": "shape", "shape_type": "line", "rect": [36, 60, 540, 1],
    "color": "#BDBDBD", "stroke_width": 1 },
  { "id": "footer_text", "type": "text", "rect": [36, 44, 540, 12],
    "content": "{{name}}",
    "style": { "font": "Helvetica", "size": 8, "italic": true, "color": "#9E9E9E", "align": "center" } }
]
```

---

## Limitations

- **No images** — only text, rectangles, lines, and circles
- **No tables** — simulate with aligned text columns and shape rules
- **No dynamic height** — every component has a fixed `rect`; content that overflows is clipped
- **No colour per character** — colour is per-component only
- **No variable positioning** — coordinates are static; the layout does not reflow based on content length
- **Lists not renderable** — multi-select / checkbox-group `value` arrays are skipped by the context builder and cannot appear in `{{field}}` references
- **Unresolved fields render as-is** — `{{unknown}}` stays literally in the output instead of causing an error
