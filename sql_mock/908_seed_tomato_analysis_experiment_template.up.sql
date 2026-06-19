INSERT INTO experiment_templates (sample_type_id, name, description, template)
SELECT st.id,
       'Tomato Analysis',
       'Chemical analysis of any fresh tomato from the ranch 1982',
       '{
  "clientForm": {
    "title": "Select Analyses",
    "description": "Choose which analyses are required for this tomato submission.",
    "questions": []
  },
  "labForm": {
    "title": "Experiment Form",
    "description": "Lab stations analysis form",
    "questions": [
      {
        "id": "tray_mass",
        "type": "number",
        "label": "Tray mass (g)",
        "required": true,
        "config": {
          "min": 0,
          "max": 500,
          "step": 0.01,
          "default": 100.0
        }
      },
      {
        "id": "tray_sam",
        "type": "number",
        "label": "Mass of tray with sample before drying (g)",
        "required": true,
        "config": {
          "min": 0,
          "max": 600,
          "step": 0.01,
          "default": 120.0
        }
      },
      {
        "id": "tray_dry",
        "type": "number",
        "label": "Mass of tray with sample after drying (g)",
        "required": false,
        "config": {
          "min": 0,
          "max": 600,
          "step": 0.01,
          "default": 115.0
        }
      },
      {
        "id": "tray_ctrl",
        "type": "number",
        "label": "Mass of tray with sample after control drying (g)",
        "required": true,
        "config": {
          "min": 0,
          "max": 600,
          "step": 0.01,
          "default": 115.0
        }
      }
    ]
  },
  "calculations": {
    "sample_mass": {
      "formula": "values[''tray_sam''] - values[''tray_mass'']",
      "result": ""
    },
    "sample_error": {
      "formula": "values[''tray_sam''] - values[''tray_ctrl'']",
      "result": ""
    },
    "moisture_pct": {
      "formula": "round(1000 * (sample_error / sample_mass)) / 10",
      "result": ""
    }
  }
}'::jsonb
FROM sample_types st
WHERE st.name = 'Tomato'
ON CONFLICT (sample_type_id, name) WHERE is_current = true AND deleted_at IS NULL DO NOTHING;
