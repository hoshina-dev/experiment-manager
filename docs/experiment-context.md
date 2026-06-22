# Experiment Context

The **experiment context** is the JSON blob stored in `experiments.state`. It follows the [form-poc schema-bundle](https://github.com/hoshina-dev/form-poc/tree/main/schema-bundle) shape, plus experiment-manager metadata fields frozen at creation.

---

## Lifecycle

```
POST /api/experiments
  └─ context initialised from experiment template (frozen snapshot)

PUT /api/experiments/{exp_id}
  └─ worker sends the full slice back, but only `values` is actually
     applied — clientForm/labForm/calculations must match the experiment's
     template byte-for-byte (result excluded) or the request is rejected
     with 422. See "PUT body" below.

POST /api/experiments/{exp_id}/calculate
  └─ server evaluates calculations → writes result on each calculation object

POST /api/experiments/{exp_id}/report/generate
  └─ PDF engine reads the experiment context to render the report
```

---

## Full field reference

```json
{
  "id":           "uuid",
  "sample_id":    "uuid",
  "template_id":  "uuid",
  "lineage_id":   "uuid",
  "name":         "string",
  "description":  "string",
  "clientForm":   { "name": "...", "questions": [ ... ] },
  "labForm":      { "name": "...", "questions": [ ... ] },
  "calculations": { "var_name": { "formula": "...", "result": 42.0 } },
  "values":       { "question_id": 1.234 }
}
```

### Top-level fields

| Field | Type | Set by | Description |
|---|---|---|---|
| `id` | UUID string | Ticketing Service (via POST body) | Experiment identifier. Frozen at creation. |
| `sample_id` | UUID string | POST body | The sample instance this experiment is for. Frozen at creation. |
| `template_id` | UUID string | Server at creation | The specific version of the experiment template used. Frozen at creation. |
| `lineage_id` | UUID string | Server at creation | Template lineage id. Frozen at creation. |
| `name` | string | DB column at creation | Display name from `experiment_templates.name`. Frozen at creation. |
| `description` | string | DB column at creation | Description from `experiment_templates.description`. Frozen at creation. |
| `clientForm` | object | Experiment template only | Pre-analysis form (client intake). PUT must echo this unchanged; the server re-derives it from the template either way. |
| `labForm` | object | Experiment template only | Lab measurement form. Required. PUT must echo this unchanged; the server re-derives it from the template either way. |
| `calculations` | object | Experiment template (`formula`) + `/calculate` (`result`) | Map of `{ formula, result? }`. Formulas are Python expressions. PUT cannot set `result` — only `/calculate` writes it. |
| `values` | object | Worker via PUT | Collected answers keyed by question id. Repeatable-group children use columnar arrays. The only field PUT actually changes. |

Template JSONB (`experiment_templates.template`) stores only `clientForm`, `labForm`, and `calculations` — no duplicate `name`/`description`.

---

## Form structure — `clientForm` and `labForm`

Both forms share the same structure:

```json
{
  "name": "string",
  "description": "string",
  "questions": [
    {
      "id":       "sample_mass",
      "type":     "number",
      "label":    "Sample mass (g)",
      "required": true,
      "config": {
        "min": 0,
        "max": 10,
        "step": 0.001,
        "default": 1.0
      }
    }
  ]
}
```

Question options (`default`, `min`, `max`, `options`, etc.) live under `config`. Answers are **not** stored on questions — they go in the top-level `values` dict.

### Repeatable-group answers

Child question ids map to columnar arrays in `values`:

```json
"values": {
  "reading_a": [10.12, 10.08, 9.97],
  "reading_b": [10.10, 10.11, 10.00]
}
```

---

## `calculations`

Each entry is an object:

```json
"calculations": {
  "moisture_pct": {
    "formula": "round(1000 * moisture_loss / values['sample_mass']) / 10",
    "result": 25.0
  }
}
```

- `formula` — Python expression. Scalar inputs use `values['question_id']`. Repeatable-group inputs are lists. Intermediate results reference earlier calculation names directly.
- `result` — written by `POST /calculate`. Empty string until evaluated. May be an array for list-valued formulas.

Safe builtins in the eval namespace: `round`, `abs`, `min`, `max`, `sum`, `len`, `mean`, `median`, `stdev`, `math`.

Write `round(x)` not `Math.round(x)`, `or` not `||`, `"A" if cond else "B"` not ternary JS syntax.

When the PDF engine builds its render context, `calculations[name].result` is used when present; otherwise the formula string is shown.

---

## PUT body

The request body still requires the full slice (no API contract break for
existing clients), but only `values` is ever persisted:

```json
{
  "clientForm": { ... },
  "labForm": { ... },
  "calculations": { ... },
  "values": { "sample_mass": 1.023 }
}
```

`clientForm`, `labForm`, and each calculation's `formula` are validated
against the experiment's own template (looked up by the frozen
`template_id`, not the lineage's current version — an older experiment
keeps using the template version it was created against, even if the
lineage has since been edited). Any `result` value in `calculations` is
ignored — only `POST /calculate` may set it. If the submitted
clientForm/labForm/calculations don't match the template, the request
fails with **422** rather than silently persisting whatever was sent; the
correct recovery is to `GET` the experiment again and resend its current
shape with just `values` changed.

This exists because the server previously trusted these fields verbatim:
a buggy frontend (or a malicious client) could silently rewrite an
experiment's question/formula definitions, or fabricate a `calculations.result`
that was never actually computed by `/calculate` — and that fabricated value
would render into the generated PDF report as if it were real.

Frozen fields (`id`, `sample_id`, `template_id`, `lineage_id`, `name`, `description`) are preserved from the existing context.
