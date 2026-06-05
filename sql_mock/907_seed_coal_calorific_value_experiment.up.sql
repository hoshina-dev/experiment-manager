-- Coal / Calorific Value (GCV) experiment — completed, all question types filled in.
-- sample_id and template_id resolved by JOIN; no hardcoded UUIDs.
WITH refs AS (
  SELECT et.id AS template_id, st.id AS sample_id
  FROM experiment_templates et
  JOIN sample_types st ON et.sample_type_id = st.id
  WHERE et.name = 'Calorific Value (GCV)'
    AND st.name = 'Coal'
    AND et.deleted_at IS NULL
)
INSERT INTO experiments (id, state)
SELECT
  '3fa85f64-5717-4562-b3fc-2c963f66afa6'::uuid,
  jsonb_set(
    jsonb_set('{
    "id":          "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "title":       "Calorific Value (GCV)",
    "description": "Determine gross calorific value by bomb calorimetry",
    "userForm": {},
    "workerForm": {
      "title": "GCV Measurement Form",
      "description": "Record bomb calorimeter readings and analyst information.",
      "questions": [
        { "id": "sample_mass",         "type": "number",        "label": "Sample mass (g)",                         "min": 0,    "max": 10,   "step": 0.001, "default": 1,     "required": true,  "value": 1 },
        { "id": "water_equivalent",    "type": "number",        "label": "Water equivalent of calorimeter (cal/°C)","min": 1000, "max": 5000, "step": 0.1,   "default": 2526,  "required": true,  "value": 2526 },
        { "id": "temp_rise",           "type": "number",        "label": "Temperature rise (°C)",                   "min": 0,    "max": 10,   "step": 0.001, "default": 2.5,   "required": true,  "value": 2.5 },
        { "id": "fuse_correction",     "type": "number",        "label": "Fuse wire correction (cal)",              "min": 0,    "max": 100,  "step": 0.1,   "default": 2,     "required": false, "value": 2 },
        { "id": "analyst_name",        "type": "string",        "label": "Analyst name",                            "required": true,  "placeholder": "e.g. Dr. Smith",  "default": "Dr. Analyst",        "maxLength": 80, "value": "Dr. Pornpun Kittipanya" },
        { "id": "lab_notes",           "type": "textarea",      "label": "Observations during test",                "placeholder": "e.g. No anomalous exotherms detected...", "default": "No anomalous exotherms detected during combustion. Sample ignited cleanly on first attempt. Result within expected range for this fuel grade.", "minRows": 3, "maxRows": 8, "maxLength": 500, "value": "No anomalous exotherms detected during combustion. Sample ignited cleanly on first attempt. Result within expected range for this fuel grade." },
        { "id": "instrument_code",     "type": "password",      "label": "Instrument calibration code",             "placeholder": "•••••••", "minLength": 4, "value": "CAL-2024-88" },
        { "id": "fuel_type",           "type": "select-string", "label": "Fuel type",                               "required": true, "placeholder": "Select fuel type", "options": [{"label":"Coal (Bituminous)","value":"Coal (Bituminous)"},{"label":"Coal (Anthracite)","value":"Coal (Anthracite)"},{"label":"Coke","value":"Coke"},{"label":"Lignite","value":"Lignite"},{"label":"Biomass","value":"Biomass"}], "default": "Coal (Bituminous)", "value": "Coal (Bituminous)" },
        { "id": "combustion_pressure", "type": "select-number", "label": "Combustion O₂ pressure (atm)",            "options": [{"label":"25 atm","value":25},{"label":"30 atm","value":30},{"label":"35 atm","value":35}], "default": 30, "value": 30 },
        { "id": "corrections_applied", "type": "multi-select",  "label": "Corrections applied",                     "placeholder": "Pick corrections", "maxValues": 5, "options": [{"label":"Fuse wire","value":"fuse"},{"label":"Acid formation","value":"acid"},{"label":"Nitrogen correction","value":"nitrogen"},{"label":"Sulfur correction","value":"sulfur"}], "default": ["fuse"], "value": ["fuse"] },
        { "id": "test_validity",       "type": "radio",         "label": "Test validity",                           "required": true, "options": [{"label":"Valid","value":"Valid"},{"label":"Invalid — discard","value":"Invalid"},{"label":"Repeat required","value":"Repeat"}], "default": "Valid", "value": "Valid" },
        { "id": "qc_checks",           "type": "checkbox-group","label": "QC checklist completed",                  "options": [{"label":"Calorimeter calibration verified","value":"calibration"},{"label":"Blank run performed","value":"blank_run"},{"label":"Reference material checked","value":"reference"},{"label":"Duplicate run performed","value":"duplicate"}], "default": ["calibration","reference"], "value": ["calibration","blank_run","reference"] },
        { "id": "certified",           "type": "boolean",       "label": "Certified measurement",                   "default": true, "value": true },
        { "id": "sample_grade",        "type": "segmented",     "label": "Sample grade",                            "options": [{"label":"Grade A","value":"A"},{"label":"Grade B","value":"B"},{"label":"Grade C","value":"C"}], "default": "A", "value": "A" },
        { "id": "confidence",          "type": "slider",        "label": "Result confidence (%)",                   "min": 0, "max": 100, "step": 5, "default": 95, "marks": [{"value":0,"label":"0%"},{"value":50,"label":"50%"},{"value":100,"label":"100%"}], "value": 95 },
        { "id": "sample_quality",      "type": "rating",        "label": "Sample quality",                          "count": 5, "fractions": 1, "default": 4, "value": 4 },
        { "id": "sample_color",        "type": "color",         "label": "Sample color (visual observation)",       "default": "#212121", "swatches": ["#212121","#546E7A","#795548","#8D6E63","#BDBDBD","#F5F5F5"], "value": "#212121" },
        { "id": "analysis_date",       "type": "date",          "label": "Analysis date",                           "required": true, "default": "2026-06-01", "value": "2026-06-04" },
        { "id": "analysis_time",       "type": "time",          "label": "Analysis start time",                     "default": "09:00", "value": "09:15" },
        { "id": "test_started_at",     "type": "datetime",      "label": "Test start (date + time)",                "default": "2026-06-01T09:00", "value": "2026-06-04T09:15" },
        { "id": "sample_tags",         "type": "tags",          "label": "Sample tags",                             "placeholder": "Type and press Enter", "maxTags": 8, "default": ["gcv","calorimetry","coal"], "value": ["gcv","calorimetry","coal","certified"] }
      ]
    },
    "calculations": {
      "fuse_corr": "2",
      "gcv_cal_g": "6313",
      "gcv_kj_kg": "26431"
    },
    "template": "GCV = {{gcv_cal_g}} cal/g ({{gcv_kj_kg}} kJ/kg)"
  }'::jsonb, '{sample_id}', to_jsonb(refs.sample_id::text)),
    '{template_id}', to_jsonb(refs.template_id::text)
  )
FROM refs
ON CONFLICT (id) DO NOTHING;
