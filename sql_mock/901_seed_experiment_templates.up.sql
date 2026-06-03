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
      { "id": "crucible_mass",       "type": "number", "label": "Crucible mass (g)",                               "required": true,  "min": 0, "max": 200, "step": 0.001, "default": 20.0   },
      { "id": "sample_mass",         "type": "number", "label": "Sample mass (g)",                                "required": true,  "min": 0, "max": 10,  "step": 0.001, "default": 1.0    },
      { "id": "mass_after_moisture", "type": "number", "label": "Mass after moisture drying at 105°C (g)",        "required": true,  "min": 0, "max": 200, "step": 0.001, "default": 20.8   },
      { "id": "mass_after_volatile", "type": "number", "label": "Mass after volatile matter removal at 900°C (g)","required": true,  "min": 0, "max": 200, "step": 0.001, "default": 20.5   },
      { "id": "mass_after_ash",      "type": "number", "label": "Mass after ashing at 750°C (g)",                 "required": true,  "min": 0, "max": 200, "step": 0.001, "default": 20.1   }
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
  "template": "Moisture = {{moisture_pct}}% | Volatile Matter = {{volatile_pct}}% | Ash = {{ash_pct}}% | Fixed Carbon = {{fixed_carbon_pct}}%"
}'::jsonb
FROM sample_types WHERE name = 'Coal'
ON CONFLICT (sample_type_id, name) WHERE deleted_at IS NULL DO NOTHING;


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
      { "id": "sample_mass",      "type": "number", "label": "Sample mass (g)",                          "required": true,  "min": 0,    "max": 10,   "step": 0.001, "default": 1.0    },
      { "id": "water_equivalent", "type": "number", "label": "Water equivalent of calorimeter (cal/°C)", "required": true,  "min": 1000, "max": 5000, "step": 0.1,   "default": 2426.0 },
      { "id": "temp_rise",        "type": "number", "label": "Temperature rise (°C)",                    "required": true,  "min": 0,    "max": 10,   "step": 0.001, "default": 2.5    },
      { "id": "fuse_correction",  "type": "number", "label": "Fuse wire correction (cal)",               "required": false, "min": 0,    "max": 100,  "step": 0.1,   "default": 2.0    }
    ]
  },
  "calculations": {
    "fuse_corr": "fuse_correction || 0",
    "gcv_cal_g": "Math.round((water_equivalent * temp_rise - fuse_corr) / sample_mass)",
    "gcv_kj_kg": "Math.round(gcv_cal_g * 4.1868)"
  },
  "template": "GCV = {{gcv_cal_g}} cal/g ({{gcv_kj_kg}} kJ/kg)"
}'::jsonb
FROM sample_types WHERE name = 'Coal'
ON CONFLICT (sample_type_id, name) WHERE deleted_at IS NULL DO NOTHING;


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
      { "id": "sample_mass",    "type": "number", "label": "Sample mass (g)",             "required": true, "min": 0,    "max": 10,  "step": 0.001, "default": 1.0  },
      { "id": "titrant_volume", "type": "number", "label": "Volume of titrant used (mL)", "required": true, "min": 0,    "max": 50,  "step": 0.01,  "default": 10.0 },
      { "id": "blank_volume",   "type": "number", "label": "Blank titrant volume (mL)",   "required": true, "min": 0,    "max": 10,  "step": 0.01,  "default": 0.5  },
      { "id": "normality",      "type": "number", "label": "Normality of titrant (N)",    "required": true, "min": 0.001,"max": 1,   "step": 0.001, "default": 0.1  }
    ]
  },
  "calculations": {
    "net_volume": "titrant_volume - blank_volume",
    "sulfur_pct": "Math.round(10000 * (net_volume * normality * 1.603) / sample_mass) / 100"
  },
  "template": "Sulfur content = {{sulfur_pct}}%"
}'::jsonb
FROM sample_types WHERE name = 'Coal'
ON CONFLICT (sample_type_id, name) WHERE deleted_at IS NULL DO NOTHING;


-- ══════════════════════════════════════════════════════════════════
-- TOMATO  (1 template)
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
      { "id": "tray_mass", "type": "number", "label": "Tray mass (g)",                                     "required": true, "min": 0, "max": 500, "step": 0.01, "default": 100.0 },
      { "id": "tray_sam",  "type": "number", "label": "Mass of tray with sample before drying (g)",        "required": true, "min": 0, "max": 600, "step": 0.01, "default": 120.0 },
      { "id": "tray_dry",  "type": "number", "label": "Mass of tray with sample after drying (g)",         "required": true, "min": 0, "max": 600, "step": 0.01, "default": 115.0 },
      { "id": "tray_ctrl", "type": "number", "label": "Mass of tray with sample after control drying (g)", "required": true, "min": 0, "max": 600, "step": 0.01, "default": 115.0 }
    ]
  },
  "calculations": {
    "sample_mass":  "tray_sam - tray_mass",
    "sample_error": "tray_sam - tray_ctrl",
    "moisture_pct": "Math.round(1000 * (sample_error / sample_mass)) / 10"
  },
  "template": "Moisture content = {{moisture_pct}}%"
}'::jsonb
FROM sample_types WHERE name = 'Tomato'
ON CONFLICT (sample_type_id, name) WHERE deleted_at IS NULL DO NOTHING;


-- ══════════════════════════════════════════════════════════════════
-- ENVIRONMENT WATER  (2 templates)
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
          { "label": "pH Measurement",        "value": "ph"        },
          { "label": "Turbidity Measurement", "value": "turbidity" }
        ]
      }
    ]
  },
  "workerForm": {
    "title": "pH Measurement Form",
    "description": "Record pH meter readings for the water sample.",
    "questions": [
      { "id": "sample_id_label", "type": "text",   "label": "Sample label / collection point",       "required": true  },
      { "id": "temperature",     "type": "number", "label": "Sample temperature at measurement (°C)", "required": true,  "min": 0, "max": 100, "step": 0.1,  "default": 25.0 },
      { "id": "ph_reading_1",    "type": "number", "label": "pH reading — replicate 1",               "required": true,  "min": 0, "max": 14,  "step": 0.01, "default": 7.0  },
      { "id": "ph_reading_2",    "type": "number", "label": "pH reading — replicate 2",               "required": true,  "min": 0, "max": 14,  "step": 0.01, "default": 7.0  }
    ]
  },
  "calculations": {
    "ph_avg": "Math.round(100 * (ph_reading_1 + ph_reading_2) / 2) / 100",
    "status": "ph_avg < 6.5 ? \"Acidic\" : ph_avg > 8.5 ? \"Alkaline\" : \"Neutral\""
  },
  "template": "pH = {{ph_avg}} at {{temperature}}°C — {{status}}"
}'::jsonb
FROM sample_types WHERE name = 'Environment Water'
ON CONFLICT (sample_type_id, name) WHERE deleted_at IS NULL DO NOTHING;


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
          { "label": "pH Measurement",        "value": "ph"        },
          { "label": "Turbidity Measurement", "value": "turbidity" }
        ]
      }
    ]
  },
  "workerForm": {
    "title": "Turbidity Form",
    "description": "Record turbidimeter readings.",
    "questions": [
      { "id": "sample_id_label", "type": "text",   "label": "Sample label / collection point",        "required": true },
      { "id": "ntu_reading_1",   "type": "number", "label": "Turbidity reading — replicate 1 (NTU)",  "required": true, "min": 0, "max": 1000, "step": 0.01, "default": 2.5 },
      { "id": "ntu_reading_2",   "type": "number", "label": "Turbidity reading — replicate 2 (NTU)",  "required": true, "min": 0, "max": 1000, "step": 0.01, "default": 2.5 }
    ]
  },
  "calculations": {
    "ntu_avg":       "Math.round(100 * (ntu_reading_1 + ntu_reading_2) / 2) / 100",
    "who_limit":     "5",
    "exceeds_limit": "ntu_avg > who_limit ? \"EXCEEDS WHO limit\" : \"Within WHO limit\""
  },
  "template": "Turbidity = {{ntu_avg}} NTU — {{exceeds_limit}} (5 NTU)"
}'::jsonb
FROM sample_types WHERE name = 'Environment Water'
ON CONFLICT (sample_type_id, name) WHERE deleted_at IS NULL DO NOTHING;
