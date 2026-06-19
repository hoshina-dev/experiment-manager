-- Revert the Calorific Value (GCV) template JSONB back to the simple version from 901.
UPDATE experiment_templates
SET
  description = 'Determine gross calorific value by bomb calorimetry',
  template    = '{
  "title": "Calorific Value (GCV)",
  "description": "Determine gross calorific value by bomb calorimetry",
  "userForm": {},
  "workerForm": {
    "title": "Calorific Value Form",
    "description": "Record bomb calorimeter readings.",
    "questions": [
      {
        "id": "sample_mass",
        "type": "number",
        "label": "Sample mass (g)",
        "required": true,
        "config": {
          "min": 0,
          "max": 10,
          "step": 0.001,
          "default": 1.0
        }
      },
      {
        "id": "water_equivalent",
        "type": "number",
        "label": "Water equivalent of calorimeter (cal/°C)",
        "required": true,
        "config": {
          "min": 1000,
          "max": 5000,
          "step": 0.1,
          "default": 2426.0
        }
      },
      {
        "id": "temp_rise",
        "type": "number",
        "label": "Temperature rise (°C)",
        "required": true,
        "config": {
          "min": 0,
          "max": 10,
          "step": 0.001,
          "default": 2.5
        }
      },
      {
        "id": "fuse_correction",
        "type": "number",
        "label": "Fuse wire correction (cal)",
        "required": false,
        "config": {
          "min": 0,
          "max": 100,
          "step": 0.1,
          "default": 2.0
        }
      }
    ]
  },
  "calculations": {
    "fuse_corr": "fuse_correction or 0",
    "gcv_cal_g": "round((water_equivalent * temp_rise - fuse_corr) / sample_mass)",
    "gcv_kj_kg": "round(gcv_cal_g * 4.1868)"
  },
  "template": "GCV = {{gcv_cal_g}} cal/g ({{gcv_kj_kg}} kJ/kg)"
}'::jsonb
FROM sample_types st
WHERE experiment_templates.sample_type_id = st.id
  AND st.name = 'Coal'
  AND experiment_templates.name = 'Calorific Value (GCV)'
  AND experiment_templates.deleted_at IS NULL;
