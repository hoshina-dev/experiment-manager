# Experiment Context

The **experiment context** is the JSON blob stored in `experiments.state`. It follows the [form-poc schema-bundle](https://github.com/hoshina-dev/form-poc/tree/main/schema-bundle) shape, plus experiment-manager metadata fields frozen at creation.

---

## Lifecycle

```
POST /api/experiments
  └─ context initialised from experiment template (frozen snapshot)

PUT /api/experiments/{exp_id}
  └─ worker updates clientForm, labForm, calculations, and values

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
  "clientForm":   { "title": "...", "questions": [ ... ] },
  "labForm":      { "title": "...", "questions": [ ... ] },
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
| `clientForm` | object | Experiment template + worker PUT | Pre-analysis form (client intake). |
| `labForm` | object | Experiment template + worker PUT | Lab measurement form. Required. |
| `calculations` | object | Experiment template + worker PUT | Map of `{ formula, result? }`. Formulas are Python expressions. |
| `values` | object | Worker via PUT | Collected answers keyed by question id. Repeatable-group children use columnar arrays. |

Template JSONB (`experiment_templates.template`) stores only `clientForm`, `labForm`, and `calculations` — no duplicate `name`/`description`.

---

## Form structure — `clientForm` and `labForm`

Both forms share the same structure:

```json
{
  "title": "string",
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

Send the full updatable slice:

```json
{
  "clientForm": { ... },
  "labForm": { ... },
  "calculations": { ... },
  "values": { "sample_mass": 1.023 }
}
```

Frozen fields (`id`, `sample_id`, `template_id`, `lineage_id`, `name`, `description`) are preserved from the existing context.
