INSERT INTO experiment_templates (sample_type_id, name, description, template)
SELECT st.id,
       'Tomato Analysis',
       'Chemical analysis of any fresh tomato from the ranch 1982',
       '{
  "title": "Tomato Analysis",
  "description": "Chemical analysis of any fresh tomato from the ranch 1982",
  "userForm": {
    "title": "Select Analyses",
    "description": "Choose which analyses are required for this tomato submission.",
    "questions": []
  },
  "workerForm": {
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
    "sample_mass": "tray_sam - tray_mass",
    "sample_error": "tray_sam - tray_ctrl",
    "moisture_pct": "round(1000 * (sample_error / sample_mass)) / 10"
  },
  "template": "Moisture Content Analysis Report\n\nThe specimen submitted for analysis was a fresh tomato sample sourced from Ranch 1982. The determination of moisture content was carried out using a standard gravimetric oven-drying method, in which the sample is weighed before and after controlled drying to constant mass.\n\nPrior to analysis, a clean drying tray was weighed, recording a tare mass of {{tray_mass}} g. The prepared tomato specimen was then placed onto the tray, and the combined mass of tray and fresh sample was recorded as {{tray_sam}} g, yielding a net sample mass of {{sample_mass}} g.\n\nThe loaded tray was introduced into a drying oven maintained at the prescribed temperature and held until the mass reached stability. Following the primary drying cycle, a confirmatory control re-drying was performed to verify that no further moisture loss was occurring. The mass of the tray with the dried residue after the control cycle was measured at {{tray_ctrl}} g, corresponding to a total moisture loss of {{sample_error}} g from the original specimen.\n\nApplying the gravimetric moisture formula, the moisture content of the sample is determined to be {{moisture_pct}}%. This result reflects the proportion of water present in the fresh tomato on a wet-weight basis, and is representative of the moisture characteristic of the specimen as received at the laboratory."
}'::jsonb
FROM sample_types st
WHERE st.name = 'Tomato'
ON CONFLICT (sample_type_id, name) WHERE deleted_at IS NULL DO NOTHING;
