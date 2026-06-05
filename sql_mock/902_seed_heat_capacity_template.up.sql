INSERT INTO experiment_templates (sample_type_id, name, description, template)
SELECT st.id,
       'Heat Capacity Analysis',
       'Bomb-calorimeter determination of specific and molar heat capacity',
       '{
  "userForm": {
    "title": "Sample Information",
    "description": "Details of the specimen submitted for analysis.",
    "questions": [
      { "id": "sample_id",            "type": "string", "label": "Sample ID",                    "required": true, "default": "CHR-001" },
      { "id": "sample_source",        "type": "string", "label": "Source / Grade",               "required": true, "default": "Activated charcoal sample" },
      { "id": "sample_mass",          "type": "string", "label": "Sample mass (g)",              "required": true, "default": "1.0000" },
      { "id": "temperature_initial",  "type": "string", "label": "Initial temperature (°C)",    "required": true, "default": "25.00" },
      { "id": "temperature_final",    "type": "string", "label": "Final temperature (°C)",      "required": true, "default": "30.00" },
      { "id": "calorimeter_constant", "type": "string", "label": "Calorimeter constant (J/°C)", "required": true, "default": "9800.0" }
    ]
  },
  "workerForm": {
    "title": "Analyst Details",
    "description": "Completed by the laboratory analyst after measurement.",
    "questions": [
      { "id": "analyst_name",  "type": "string", "label": "Analyst name",     "default": "Analyst" },
      { "id": "lab_id",        "type": "string", "label": "Laboratory ID",    "default": "LAB-001" },
      { "id": "analysis_date", "type": "string", "label": "Analysis date",    "default": "YYYY-MM-DD" },
      { "id": "instrument",    "type": "string", "label": "Instrument",       "default": "Bomb Calorimeter" },
      { "id": "method_ref",    "type": "string", "label": "Method reference", "default": "ASTM D5865" }
    ]
  },
  "calculations": {
    "delta_T":             "temperature_final - temperature_initial",
    "heat_released":       "Math.round(calorimeter_constant * delta_T * 100) / 100",
    "specific_heat":       "Math.round(heat_released / sample_mass * 10) / 10",
    "molar_heat_capacity": "Math.round(specific_heat * 12.011 * 10) / 10"
  },
  "template": "Sample {{sample_id}} — {{sample_source}} — was analysed on {{analysis_date}} by {{analyst_name}} ({{lab_id}}) using a {{instrument}} following {{method_ref}}.\n\nA specimen of {{sample_mass}} g was combusted under pure oxygen. Temperature rose from {{temperature_initial}} °C to {{temperature_final}} °C, giving ΔT = {{delta_T}} °C. Applying the calorimeter constant of {{calorimeter_constant}} J/°C:\n\n  Q = C × ΔT = {{calorimeter_constant}} × {{delta_T}} = {{heat_released}} J\n\nSpecific heat capacity = Q / m = {{specific_heat}} J/g\nMolar heat capacity (M = 12.011 g/mol) = {{molar_heat_capacity}} J/mol"
}'::jsonb
FROM sample_types st
WHERE st.name = 'Coal'
ON CONFLICT (sample_type_id, name) WHERE deleted_at IS NULL DO NOTHING;
