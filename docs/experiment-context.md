# Experiment Context

The **experiment context** is the JSON blob stored in `experiments.state`. It is the single source of truth for an experiment instance — created from the experiment template at experiment creation time and updated incrementally as the lab workflow progresses.

---

## Lifecycle

```
POST /api/experiments
  └─ context initialised from experiment template (frozen snapshot)

PUT /api/experiments/{exp_id}
  └─ worker fills in workerForm question values (and optionally userForm)

POST /api/experiments/{exp_id}/calculate
  └─ server evaluates calculations → writes calc_result

POST /api/experiments/{exp_id}/upgrade-template
  └─ swaps template_id to the current version of the same lineage
     (use when the experiment template was updated after experiment creation)

POST /api/experiments/{exp_id}/report/generate
  └─ PDF engine reads the experiment context to render the report
```

---

## Full field reference

```json
{
  "id":          "uuid",
  "sample_id":   "uuid",
  "template_id": "uuid",
  "title":       "string",
  "description": "string",
  "userForm":    { ... },
  "workerForm":  { ... },
  "calculations": { "var_name": "JS expression" },
  "calc_result":  { "var_name": 42.0 },
  "template":    "string with {{placeholders}}"
}
```

### Top-level fields

| Field | Type | Set by | Description |
|---|---|---|---|
| `id` | UUID string | Ticketing Service (via POST body) | Experiment identifier. Frozen at creation — cannot be changed. |
| `sample_id` | UUID string | POST body | The sample instance this experiment is for. Frozen at creation. |
| `template_id` | UUID string | Server at creation | The specific version of the experiment template used. Frozen at creation; can be updated only via `upgrade-template`. |
| `title` | string | Experiment template | Display name, copied from the experiment template. |
| `description` | string | Experiment template | Description, copied from the experiment template. |
| `userForm` | object or null | Experiment template + worker | Pre-analysis form filled by the sample submitter. Optional. |
| `workerForm` | object | Experiment template + worker | Post-analysis form filled by the lab worker. Required. |
| `calculations` | object | Experiment template + worker PUT | JS-compatible expressions referencing workerForm question ids. Evaluated server-side by `POST /calculate`. |
| `calc_result` | object or null | Server via `POST /calculate` | Computed numeric results. Keys match `calculations` keys. Absent until calculate is called. |
| `template` | string | Experiment template + worker PUT | Output string with `{{placeholder}}` references. Used as the narrative summary in the PDF. |

---

## Form structure — `userForm` and `workerForm`

Both forms share the same structure:

```json
{
  "title": "string",
  "description": "string",
  "questions": [
    {
      "id":       "variable_name",
      "type":     "number",
      "label":    "Sample mass (g)",
      "default":  1.0,
      "value":    1.234,
      "required": true
    }
  ]
}
```

### Question fields

| Field | Required | Description |
|---|---|---|
| `id` | Yes | Variable name used in `calculations` and `{{placeholders}}`. Must match `[A-Za-z_$][A-Za-z0-9_$]*`. |
| `type` | Yes | Input type — see table below. |
| `label` | Yes | Human-readable label shown in the UI. |
| `default` | No | Value used if `value` is not set. |
| `value` | No | Filled in by the worker via PUT. Used by the calculation engine and PDF renderer. |
| `required` | No | UI hint only — not enforced server-side. |

### Question types

| Type | Value shape | Notes |
|---|---|---|
| `number` | `float` | Used as numeric inputs to `calculations`. Supports `min`, `max`, `step` display hints. |
| `string` | `string` | Free text. |
| `textarea` | `string` | Multi-line text. Supports `minRows`, `maxRows`, `maxLength`. |
| `password` | `string` | Masked in UI. |
| `boolean` | `bool` | Checkbox. |
| `date` | `string` | ISO date `YYYY-MM-DD`. |
| `time` | `string` | `HH:MM`. |
| `datetime` | `string` | `YYYY-MM-DDTHH:MM`. |
| `select-string` | `string` | Single-select from `options[]`. |
| `select-number` | `float` | Single-select from `options[]`. |
| `radio` | `string` | Single-select rendered as radio buttons. |
| `multi-select` | `string[]` | Multiple values from `options[]`. Not usable in `{{placeholders}}` or `calculations`. |
| `checkbox-group` | `string[]` | Multiple boolean flags. Not usable in `{{placeholders}}` or `calculations`. |
| `segmented` | `string` | Single-select rendered as a segmented control. |
| `slider` | `float` | Numeric within `min`/`max` range. |
| `rating` | `float` | Star rating. Supports `count`, `fractions`. |
| `color` | `string` | CSS hex colour e.g. `#1565C0`. |
| `tags` | `string[]` | Free-form tag list. Not usable in `{{placeholders}}` or `calculations`. |

> Only `number`, `slider`, `rating`, `select-number` produce numeric values usable in `calculations`. All other types produce strings or arrays.

---

## `calculations` — expression format

```json
"calculations": {
  "delta_T":       "temperature_final - temperature_initial",
  "heat_released": "Math.round(calorimeter_constant * delta_T * 100) / 100",
  "specific_heat": "Math.round(heat_released / sample_mass * 10) / 10"
}
```

- Expressions are evaluated **in order** — later expressions can reference the results of earlier ones.
- Variables are resolved from `workerForm` question `value` (or `default` if value is not set). `userForm` values are not available to calculations.
- JS syntax is translated server-side: `Math.*` → `math.*`, `===` → `==`, `||` → `or`, `null` → `None`, `true` → `True`, `false` → `False`.
- Safe builtins only: `round`, `abs`, `min`, `max`, `math` module.
- `__` (dunder) access is blocked.

### Error responses from `POST /calculate`

| Condition | HTTP | Detail |
|---|---|---|
| Expression contains `__` | 422 | `Invalid expression in '<name>': dunder access not allowed` |
| Division by zero | 422 | `Division by zero in '<name>'` |
| Undefined variable | 422 | `Undefined variable in '<name>': name '...' is not defined` |
| Non-finite result (nan/inf) | 422 | `Non-finite result in '<name>' (got nan)` |
| Any other eval error | 422 | `Calculation error in '<name>': <message>` |
| Experiment not found | 404 | — |

---

## `calc_result`

Written by `POST /calculate`. A flat dict of `{ expression_name: computed_value }`:

```json
"calc_result": {
  "delta_T":       5.35,
  "heat_released": 52657.75,
  "specific_heat": 42670.0
}
```

- Values are Python `int` or `float`.
- Keys exactly match `calculations` keys.
- When the PDF engine builds its render context, `calc_result` values **override** the raw `calculations` expression strings under the same key names. This means `{{delta_T}}` in a PDF component renders `5.35` (not the expression string) once calculate has been called.
- `calc_result` is `null` until `POST /calculate` is called. Generating a PDF before calling calculate will render raw JS expression strings in place of numeric results.

---

## `template` — narrative output string

A free-form string with `{{placeholder}}` references:

```
"Sample {{sample_id}} was analysed on {{analysis_date}} by {{analyst_name}}.\nΔT = {{delta_T}} °C  →  Q = {{heat_released}} J"
```

- Placeholders are resolved using the same context rules as PDF components (see `docs/pdf-report-engine.md`).
- The resolved string is stored back into the render context as `{{template}}`, so PDF components can embed the full narrative with a single `{{template}}` reference.
- Resolved at PDF generation time, not at calculate time.
