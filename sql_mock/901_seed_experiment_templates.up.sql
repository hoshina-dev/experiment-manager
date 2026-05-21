INSERT INTO experiment_templates (sample_type_id, name, description, template)
SELECT id, 'Proximate Analysis', 'Determine moisture, ash, volatile matter, and fixed carbon content',
'{
  "userForm": {
    "title": "Select Analyses",
    "description": "Choose which analyses are required for this coal submission.",
    "questions": [
      {
        "id": "analyses",
        "type": "checkbox-group",
        "label": "Analyses",
        "default": ["proximate", "calorific"],
        "options": [
          { "label": "Proximate Analysis",     "value": "proximate" },
          { "label": "Calorific Value (GCV)",  "value": "calorific" },
          { "label": "Sulfur Content Analysis","value": "sulfur"    }
        ]
      }
    ]
  },
  "workerForm": {
    "title": "Proximate Analysis Form",
    "description": "Record masses at each stage of the proximate analysis procedure.",
    "questions": [
      { "id": "crucible_mass",       "type": "number", "label": "Crucible mass (g)",                              "required": true  },
      { "id": "sample_mass",         "type": "number", "label": "Sample mass (g)",                               "required": true  },
      { "id": "mass_after_moisture", "type": "number", "label": "Mass after moisture drying at 105°C (g)",       "required": true  },
      { "id": "mass_after_volatile", "type": "number", "label": "Mass after volatile matter removal at 900°C (g)","required": true  },
      { "id": "mass_after_ash",      "type": "number", "label": "Mass after ashing at 750°C (g)",                "required": true  }
    ]
  },
  "calculations": {
    "moisture_loss":    "crucible_mass + sample_mass - mass_after_moisture",
    "volatile_loss":    "mass_after_moisture - mass_after_volatile",
    "ash_mass":         "mass_after_ash - crucible_mass",
    "moisture_pct":     "Math.round(1000 * moisture_loss / sample_mass) / 10",
    "volatile_pct":     "Math.round(1000 * volatile_loss / sample_mass) / 10",
    "ash_pct":          "Math.round(1000 * ash_mass / sample_mass) / 10",
    "fixed_carbon_pct": "Math.round(10 * (100 - moisture_pct - volatile_pct - ash_pct)) / 10"
  },
  "outputTemplate": "Moisture = {{moisture_pct}}% | Volatile Matter = {{volatile_pct}}% | Ash = {{ash_pct}}% | Fixed Carbon = {{fixed_carbon_pct}}%"
}'::jsonb
FROM sample_types WHERE name = 'Coal'
ON CONFLICT (sample_type_id, name) DO NOTHING;


-- ── Coal / Calorific Value ────────────────────────────────────────
INSERT INTO experiment_templates (sample_type_id, name, description, template)
SELECT id, 'Calorific Value (GCV)', 'Determine gross calorific value by bomb calorimetry',
'{
  "userForm": {
    "title": "Select Analyses",
    "description": "Choose which analyses are required for this coal submission.",
    "questions": [
      {
        "id": "analyses",
        "type": "checkbox-group",
        "label": "Analyses",
        "default": ["proximate", "calorific"],
        "options": [
          { "label": "Proximate Analysis",     "value": "proximate" },
          { "label": "Calorific Value (GCV)",  "value": "calorific" },
          { "label": "Sulfur Content Analysis","value": "sulfur"    }
        ]
      }
    ]
  },
  "workerForm": {
    "title": "Calorific Value Form",
    "description": "Record bomb calorimeter readings.",
    "questions": [
      { "id": "sample_mass",      "type": "number", "label": "Sample mass (g)",                          "required": true  },
      { "id": "water_equivalent", "type": "number", "label": "Water equivalent of calorimeter (cal/°C)", "required": true  },
      { "id": "temp_rise",        "type": "number", "label": "Temperature rise (°C)",                    "required": true  },
      { "id": "fuse_correction",  "type": "number", "label": "Fuse wire correction (cal)",               "required": false }
    ]
  },
  "calculations": {
    "fuse_corr": "fuse_correction || 0",
    "gcv_cal_g": "Math.round((water_equivalent * temp_rise - fuse_corr) / sample_mass)",
    "gcv_kj_kg": "Math.round(gcv_cal_g * 4.1868)"
  },
  "outputTemplate": "GCV = {{gcv_cal_g}} cal/g ({{gcv_kj_kg}} kJ/kg)"
}'::jsonb
FROM sample_types WHERE name = 'Coal'
ON CONFLICT (sample_type_id, name) DO NOTHING;


-- ── Coal / Sulfur Content Analysis ───────────────────────────────
INSERT INTO experiment_templates (sample_type_id, name, description, template)
SELECT id, 'Sulfur Content Analysis', 'Determine total sulfur content by titrimetric method',
'{
  "userForm": {
    "title": "Select Analyses",
    "description": "Choose which analyses are required for this coal submission.",
    "questions": [
      {
        "id": "analyses",
        "type": "checkbox-group",
        "label": "Analyses",
        "default": ["proximate", "calorific"],
        "options": [
          { "label": "Proximate Analysis",     "value": "proximate" },
          { "label": "Calorific Value (GCV)",  "value": "calorific" },
          { "label": "Sulfur Content Analysis","value": "sulfur"    }
        ]
      }
    ]
  },
  "workerForm": {
    "title": "Sulfur Analysis Form",
    "description": "Record sample mass and titration volumes.",
    "questions": [
      { "id": "sample_mass",    "type": "number", "label": "Sample mass (g)",             "required": true },
      { "id": "titrant_volume", "type": "number", "label": "Volume of titrant used (mL)", "required": true },
      { "id": "blank_volume",   "type": "number", "label": "Blank titrant volume (mL)",   "required": true },
      { "id": "normality",      "type": "number", "label": "Normality of titrant (N)",    "required": true }
    ]
  },
  "calculations": {
    "net_volume": "titrant_volume - blank_volume",
    "sulfur_pct": "Math.round(10000 * (net_volume * normality * 1.603) / sample_mass) / 100"
  },
  "outputTemplate": "Sulfur content = {{sulfur_pct}}%"
}'::jsonb
FROM sample_types WHERE name = 'Coal'
ON CONFLICT (sample_type_id, name) DO NOTHING;


-- ══════════════════════════════════════════════════════════════════
-- TOMATO  (1 template)
--
-- userForm: customer picks from Moisture Analysis
--           (extend options here as more tomato analyses are added)
-- ══════════════════════════════════════════════════════════════════

-- ── Tomato / Moisture Analysis ────────────────────────────────────
INSERT INTO experiment_templates (sample_type_id, name, description, template)
SELECT id, 'Moisture Analysis', 'Determine moisture content by drying method',
'{
  "userForm": {
    "title": "Select Analyses",
    "description": "Choose which analyses are required for this tomato submission.",
    "questions": [
      {
        "id": "analyses",
        "type": "checkbox-group",
        "label": "Analyses",
        "default": ["moisture"],
        "options": [
          { "label": "Moisture Analysis", "value": "moisture" }
        ]
      }
    ]
  },
  "workerForm": {
    "title": "Moisture Analysis Form",
    "description": "Record tray and sample masses before and after drying.",
    "questions": [
      { "id": "tray_mass", "type": "number", "label": "Tray mass (g)",                                     "required": true },
      { "id": "tray_sam",  "type": "number", "label": "Mass of tray with sample before drying (g)",        "required": true },
      { "id": "tray_dry",  "type": "number", "label": "Mass of tray with sample after drying (g)",         "required": true },
      { "id": "tray_ctrl", "type": "number", "label": "Mass of tray with sample after control drying (g)", "required": true }
    ]
  },
  "calculations": {
    "sample_mass":  "tray_sam - tray_mass",
    "sample_error": "tray_sam - tray_ctrl",
    "moisture_pct": "Math.round(1000 * (sample_error / sample_mass)) / 10"
  },
  "outputTemplate": "Moisture content = {{moisture_pct}}%"
}'::jsonb
FROM sample_types WHERE name = 'Tomato'
ON CONFLICT (sample_type_id, name) DO NOTHING;


-- ══════════════════════════════════════════════════════════════════
-- ENVIRONMENT WATER  (2 templates — both share the same userForm)
--
-- userForm: customer picks from pH Measurement and Turbidity
-- ══════════════════════════════════════════════════════════════════

-- ── Environment Water / pH Measurement ───────────────────────────
INSERT INTO experiment_templates (sample_type_id, name, description, template)
SELECT id, 'pH Measurement', 'Measure hydrogen ion concentration in water sample',
'{
  "userForm": {
    "title": "Select Analyses",
    "description": "Choose which analyses are required for this water submission.",
    "questions": [
      {
        "id": "analyses",
        "type": "checkbox-group",
        "label": "Analyses",
        "default": ["ph", "turbidity"],
        "options": [
          { "label": "pH Measurement",       "value": "ph"        },
          { "label": "Turbidity Measurement","value": "turbidity" }
        ]
      }
    ]
  },
  "workerForm": {
    "title": "pH Measurement Form",
    "description": "Record pH meter readings for the water sample.",
    "questions": [
      { "id": "sample_id_label", "type": "text",   "label": "Sample label / collection point",      "required": true  },
      { "id": "temperature",     "type": "number", "label": "Sample temperature at measurement (°C)","required": true  },
      { "id": "ph_reading_1",    "type": "number", "label": "pH reading — replicate 1",              "required": true  },
      { "id": "ph_reading_2",    "type": "number", "label": "pH reading — replicate 2",              "required": true  }
    ]
  },
  "calculations": {
    "ph_avg": "Math.round(100 * (ph_reading_1 + ph_reading_2) / 2) / 100",
    "status": "ph_avg < 6.5 ? \"Acidic\" : ph_avg > 8.5 ? \"Alkaline\" : \"Neutral\""
  },
  "outputTemplate": "pH = {{ph_avg}} at {{temperature}}°C — {{status}}"
}'::jsonb
FROM sample_types WHERE name = 'Environment Water'
ON CONFLICT (sample_type_id, name) DO NOTHING;


-- ── Environment Water / Turbidity Measurement ─────────────────────
INSERT INTO experiment_templates (sample_type_id, name, description, template)
SELECT id, 'Turbidity Measurement', 'Measure water clarity using a nephelometric turbidimeter (NTU)',
'{
  "userForm": {
    "title": "Select Analyses",
    "description": "Choose which analyses are required for this water submission.",
    "questions": [
      {
        "id": "analyses",
        "type": "checkbox-group",
        "label": "Analyses",
        "default": ["ph", "turbidity"],
        "options": [
          { "label": "pH Measurement",       "value": "ph"        },
          { "label": "Turbidity Measurement","value": "turbidity" }
        ]
      }
    ]
  },
  "workerForm": {
    "title": "Turbidity Form",
    "description": "Record turbidimeter readings.",
    "questions": [
      { "id": "sample_id_label", "type": "text",   "label": "Sample label / collection point",       "required": true },
      { "id": "ntu_reading_1",   "type": "number", "label": "Turbidity reading — replicate 1 (NTU)", "required": true },
      { "id": "ntu_reading_2",   "type": "number", "label": "Turbidity reading — replicate 2 (NTU)", "required": true }
    ]
  },
  "calculations": {
    "ntu_avg":      "Math.round(100 * (ntu_reading_1 + ntu_reading_2) / 2) / 100",
    "who_limit":    "5",
    "exceeds_limit":"ntu_avg > who_limit ? \"EXCEEDS WHO limit\" : \"Within WHO limit\""
  },
  "outputTemplate": "Turbidity = {{ntu_avg}} NTU — {{exceeds_limit}} (5 NTU)"
}'::jsonb
FROM sample_types WHERE name = 'Environment Water'
ON CONFLICT (sample_type_id, name) DO NOTHING;
