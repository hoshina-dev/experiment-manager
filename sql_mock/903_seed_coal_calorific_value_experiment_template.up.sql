-- Coal / Calorific Value (GCV) — upgrade template JSONB to all-component version.
-- Updates the row seeded by 901_seed_experiment_templates; no hardcoded UUID.
UPDATE experiment_templates
SET
  description = 'Determine gross calorific value by bomb calorimetry. All question types showcased.',
  template    = '{
    "title": "Calorific Value (GCV)",
    "description": "Determine gross calorific value by bomb calorimetry",
    "userForm": {},
    "workerForm": {
      "title": "GCV Measurement Form",
      "description": "Record bomb calorimeter readings and analyst information.",
      "questions": [
        {
          "id": "sample_mass",
          "type": "number",
          "label": "Sample mass (g)",
          "min": 0, "max": 10, "step": 0.001, "default": 1,
          "required": true
        },
        {
          "id": "water_equivalent",
          "type": "number",
          "label": "Water equivalent of calorimeter (cal/°C)",
          "min": 1000, "max": 5000, "step": 0.1, "default": 2526,
          "required": true
        },
        {
          "id": "temp_rise",
          "type": "number",
          "label": "Temperature rise (°C)",
          "min": 0, "max": 10, "step": 0.001, "default": 2.5,
          "required": true
        },
        {
          "id": "fuse_correction",
          "type": "number",
          "label": "Fuse wire correction (cal)",
          "min": 0, "max": 100, "step": 0.1, "default": 2,
          "required": false
        },
        {
          "id": "analyst_name",
          "type": "string",
          "label": "Analyst name",
          "placeholder": "e.g. Dr. Smith",
          "default": "Dr. Analyst",
          "maxLength": 80,
          "required": true
        },
        {
          "id": "lab_notes",
          "type": "textarea",
          "label": "Observations during test",
          "description": "Any anomalies, conditions, or notes from the run.",
          "placeholder": "e.g. No anomalous exotherms detected...",
          "default": "No anomalous exotherms detected during combustion. Sample ignited cleanly on first attempt. Result within expected range for this fuel grade.",
          "minRows": 3, "maxRows": 8, "maxLength": 500
        },
        {
          "id": "instrument_code",
          "type": "password",
          "label": "Instrument calibration code",
          "description": "Access/calibration code for the calorimeter. Not shown in report.",
          "placeholder": "•••••••",
          "minLength": 4
        },
        {
          "id": "fuel_type",
          "type": "select-string",
          "label": "Fuel type",
          "description": "Classification of the sample material.",
          "placeholder": "Select fuel type",
          "options": [
            { "label": "Coal (Bituminous)", "value": "Coal (Bituminous)" },
            { "label": "Coal (Anthracite)", "value": "Coal (Anthracite)" },
            { "label": "Coke",              "value": "Coke" },
            { "label": "Lignite",           "value": "Lignite" },
            { "label": "Biomass",           "value": "Biomass" }
          ],
          "default": "Coal (Bituminous)",
          "required": true
        },
        {
          "id": "combustion_pressure",
          "type": "select-number",
          "label": "Combustion O₂ pressure (atm)",
          "description": "Oxygen pressure used for bomb charging.",
          "options": [
            { "label": "25 atm", "value": 25 },
            { "label": "30 atm", "value": 30 },
            { "label": "35 atm", "value": 35 }
          ],
          "default": 30
        },
        {
          "id": "corrections_applied",
          "type": "multi-select",
          "label": "Corrections applied",
          "description": "Select all correction factors included in the result.",
          "placeholder": "Pick corrections",
          "maxValues": 5,
          "options": [
            { "label": "Fuse wire",           "value": "fuse" },
            { "label": "Acid formation",       "value": "acid" },
            { "label": "Nitrogen correction",  "value": "nitrogen" },
            { "label": "Sulfur correction",    "value": "sulfur" }
          ],
          "default": ["fuse"]
        },
        {
          "id": "test_validity",
          "type": "radio",
          "label": "Test validity",
          "description": "Analyst assessment of this run.",
          "options": [
            { "label": "Valid",              "value": "Valid" },
            { "label": "Invalid — discard",  "value": "Invalid" },
            { "label": "Repeat required",    "value": "Repeat" }
          ],
          "default": "Valid",
          "required": true
        },
        {
          "id": "qc_checks",
          "type": "checkbox-group",
          "label": "QC checklist completed",
          "description": "Confirm which QC steps were performed.",
          "options": [
            { "label": "Calorimeter calibration verified", "value": "calibration" },
            { "label": "Blank run performed",              "value": "blank_run" },
            { "label": "Reference material checked",       "value": "reference" },
            { "label": "Duplicate run performed",          "value": "duplicate" }
          ],
          "default": ["calibration", "reference"]
        },
        {
          "id": "certified",
          "type": "boolean",
          "label": "Certified measurement",
          "description": "Mark as a certified result for official reporting.",
          "default": true
        },
        {
          "id": "sample_grade",
          "type": "segmented",
          "label": "Sample grade",
          "description": "Quality grade classification of the sample.",
          "options": [
            { "label": "Grade A", "value": "A" },
            { "label": "Grade B", "value": "B" },
            { "label": "Grade C", "value": "C" }
          ],
          "default": "A"
        },
        {
          "id": "confidence",
          "type": "slider",
          "label": "Result confidence (%)",
          "description": "Analyst''s confidence in the reported value.",
          "min": 0, "max": 100, "step": 5, "default": 95,
          "marks": [
            { "value": 0,   "label": "0%" },
            { "value": 50,  "label": "50%" },
            { "value": 100, "label": "100%" }
          ]
        },
        {
          "id": "sample_quality",
          "type": "rating",
          "label": "Sample quality",
          "description": "Visual and physical quality of the sample received.",
          "count": 5, "fractions": 1, "default": 4
        },
        {
          "id": "sample_color",
          "type": "color",
          "label": "Sample color (visual observation)",
          "description": "Approximate color of the sample material.",
          "default": "#212121",
          "swatches": ["#212121", "#546E7A", "#795548", "#8D6E63", "#BDBDBD", "#F5F5F5"]
        },
        {
          "id": "analysis_date",
          "type": "date",
          "label": "Analysis date",
          "description": "Date the test was performed.",
          "default": "2026-06-01",
          "required": true
        },
        {
          "id": "analysis_time",
          "type": "time",
          "label": "Analysis start time",
          "description": "Time the combustion run began.",
          "default": "09:00"
        },
        {
          "id": "test_started_at",
          "type": "datetime",
          "label": "Test start (date + time)",
          "description": "Full timestamp for traceability.",
          "default": "2026-06-01T09:00"
        },
        {
          "id": "sample_tags",
          "type": "tags",
          "label": "Sample tags",
          "description": "Free-form tags for search and classification.",
          "placeholder": "Type and press Enter",
          "maxTags": 8,
          "default": ["gcv", "calorimetry", "coal"]
        }
      ]
    },
    "calculations": {
      "fuse_corr": "fuse_correction || 0",
      "gcv_cal_g": "Math.round((water_equivalent * temp_rise - fuse_corr) / sample_mass)",
      "gcv_kj_kg": "Math.round(gcv_cal_g * 4.1868)"
    },
    "template": "GCV = {{gcv_cal_g}} cal/g ({{gcv_kj_kg}} kJ/kg)"
  }'::jsonb
FROM sample_types st
WHERE experiment_templates.sample_type_id = st.id
  AND st.name = 'Coal'
  AND experiment_templates.name = 'Calorific Value (GCV)'
  AND experiment_templates.deleted_at IS NULL;
