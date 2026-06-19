INSERT INTO sample_types (id, name, description)
VALUES (
  'a1b2c3d4-0004-0004-0004-000000000004',
  'Material Sample',
  'Generic material samples for multi-instrument measurement runs'
)
ON CONFLICT (name) WHERE deleted_at IS NULL DO NOTHING;

INSERT INTO experiment_templates (sample_type_id, name, description, template)
SELECT st.id,
       'Repeatable Measurements',
       'Eight paired Instrument A/B readings with list-aware precision calculations',
       '{
  "clientForm": {
    "title": "Material Sample — Experiment Registration",
    "description": "Generic information about the experiment and the sample under test.",
    "questions": [
      {
        "id": "experiment_name",
        "type": "string",
        "label": "Experiment Name",
        "required": true,
        "config": {
          "placeholder": "e.g. Tensile mass calibration — Batch A",
          "maxLength": 120
        }
      },
      {
        "id": "sample_id",
        "type": "string",
        "label": "Sample ID",
        "required": true,
        "config": {
          "placeholder": "e.g. SMP-2026-0042"
        }
      },
      {
        "id": "lab_location",
        "type": "select-string",
        "label": "Lab Location",
        "required": true,
        "config": {
          "options": [
            {
              "label": "Bangkok — Lab 1",
              "value": "bkk_lab_1"
            },
            {
              "label": "Bangkok — Lab 2",
              "value": "bkk_lab_2"
            },
            {
              "label": "Singapore — Lab A",
              "value": "sg_lab_a"
            }
          ],
          "placeholder": "Select location"
        }
      },
      {
        "id": "operator_name",
        "type": "string",
        "label": "Operator Name",
        "required": true,
        "config": {
          "placeholder": "Person running the experiment"
        }
      },
      {
        "id": "test_date",
        "type": "date",
        "label": "Test Date",
        "required": true,
        "config": {
          "default": "2026-06-18"
        }
      }
    ]
  },
  "labForm": {
    "title": "Material Sample — Measurement Run",
    "description": "Measure the same sample 8 times, recording a reading from Instrument A and Instrument B each time. Per-measurement precision is computed by the system.",
    "questions": [
      {
        "id": "measurement",
        "type": "repeatable-group",
        "label": "Sample Measurements",
        "description": "Each repetition captures one reading from Instrument A and one from Instrument B for the same sample.",
        "required": true,
        "config": {
          "count": 8,
          "itemLabel": "Measurement",
          "questions": [
            {
              "id": "reading_a",
              "type": "number",
              "label": "Instrument A Reading (mg)",
              "required": true,
              "config": {
                "min": 0,
                "step": 0.01,
                "placeholder": "Reading from Instrument A"
              }
            },
            {
              "id": "reading_b",
              "type": "number",
              "label": "Instrument B Reading (mg)",
              "required": true,
              "config": {
                "min": 0,
                "step": 0.01,
                "placeholder": "Reading from Instrument B"
              }
            }
          ]
        }
      }
    ]
  },
  "calculations": {
    "n_measurements": {
      "formula": "len(values[''reading_a''])",
      "result": ""
    },
    "precision": {
      "formula": "[round(abs(a - b) / ((a + b) / 2) * 100, 3) for a, b in zip(values[''reading_a''], values[''reading_b''])]",
      "result": ""
    },
    "avg_reading_a": {
      "formula": "round(mean(values[''reading_a'']), 3)",
      "result": ""
    },
    "avg_reading_b": {
      "formula": "round(mean(values[''reading_b'']), 3)",
      "result": ""
    },
    "avg_precision": {
      "formula": "round(mean(precision), 3)",
      "result": ""
    },
    "best_precision": {
      "formula": "min(precision)",
      "result": ""
    },
    "worst_precision": {
      "formula": "max(precision)",
      "result": ""
    },
    "within_spec": {
      "formula": "mean(precision) <= 0.5",
      "result": ""
    },
    "run_summary": {
      "formula": "f\"{values[''sample_id'']}: {len(values[''reading_a''])} reads, A avg {avg_reading_a} mg / B avg {avg_reading_b} mg, avg precision {avg_precision}%\"",
      "result": ""
    }
  }
}'::jsonb
FROM sample_types st
WHERE st.name = 'Material Sample'
ON CONFLICT (sample_type_id, name) WHERE is_current = true AND deleted_at IS NULL DO NOTHING;
