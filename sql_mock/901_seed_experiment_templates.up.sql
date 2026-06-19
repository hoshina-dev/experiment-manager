INSERT INTO experiment_templates (sample_type_id, name, description, template)
SELECT id, 'Proximate Analysis', 'Determine moisture, ash, volatile matter, and fixed carbon content',
'{
  "clientForm": {
    "title": "Select Analyses",
    "description": "Choose which analyses are required for this coal submission.",
    "questions": [
      {
        "id": "analyses",
        "type": "checkbox-group",
        "label": "Analyses",
        "config": {
          "options": [
            {
              "label": "Proximate Analysis",
              "value": "proximate"
            },
            {
              "label": "Calorific Value (GCV)",
              "value": "calorific"
            },
            {
              "label": "Sulfur Content Analysis",
              "value": "sulfur"
            }
          ],
          "default": [
            "proximate",
            "calorific"
          ]
        }
      }
    ]
  },
  "labForm": {
    "title": "Proximate Analysis Form",
    "description": "Record masses at each stage of the proximate analysis procedure.",
    "questions": [
      {
        "id": "crucible_mass",
        "type": "number",
        "label": "Crucible mass (g)",
        "required": true,
        "config": {
          "min": 0,
          "max": 200,
          "step": 0.001,
          "default": 20.0
        }
      },
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
        "id": "mass_after_moisture",
        "type": "number",
        "label": "Mass after moisture drying at 105°C (g)",
        "required": true,
        "config": {
          "min": 0,
          "max": 200,
          "step": 0.001,
          "default": 20.8
        }
      },
      {
        "id": "mass_after_volatile",
        "type": "number",
        "label": "Mass after volatile matter removal at 900°C (g)",
        "required": true,
        "config": {
          "min": 0,
          "max": 200,
          "step": 0.001,
          "default": 20.5
        }
      },
      {
        "id": "mass_after_ash",
        "type": "number",
        "label": "Mass after ashing at 750°C (g)",
        "required": true,
        "config": {
          "min": 0,
          "max": 200,
          "step": 0.001,
          "default": 20.1
        }
      }
    ]
  },
  "calculations": {
    "moisture_loss": {
      "formula": "values[''crucible_mass''] + values[''sample_mass''] - values[''mass_after_moisture'']",
      "result": ""
    },
    "volatile_loss": {
      "formula": "values[''mass_after_moisture''] - values[''mass_after_volatile'']",
      "result": ""
    },
    "ash_mass": {
      "formula": "values[''mass_after_ash''] - values[''crucible_mass'']",
      "result": ""
    },
    "moisture_pct": {
      "formula": "round(1000 * moisture_loss / values[''sample_mass'']) / 10",
      "result": ""
    },
    "volatile_pct": {
      "formula": "round(1000 * volatile_loss / values[''sample_mass'']) / 10",
      "result": ""
    },
    "ash_pct": {
      "formula": "round(1000 * ash_mass / values[''sample_mass'']) / 10",
      "result": ""
    },
    "fixed_carbon_pct": {
      "formula": "round(10 * (100 - moisture_pct - volatile_pct - ash_pct)) / 10",
      "result": ""
    }
  }
}'::jsonb
FROM sample_types WHERE name = 'Coal'
ON CONFLICT (sample_type_id, name) WHERE is_current = true AND deleted_at IS NULL DO NOTHING;


-- ── Coal / Calorific Value ────────────────────────────────────────
INSERT INTO experiment_templates (sample_type_id, name, description, template)
SELECT id, 'Calorific Value (GCV)', 'Determine gross calorific value by bomb calorimetry',
'{
  "clientForm": {
    "title": "Select Analyses",
    "description": "Choose which analyses are required for this coal submission.",
    "questions": [
      {
        "id": "analyses",
        "type": "checkbox-group",
        "label": "Analyses",
        "config": {
          "options": [
            {
              "label": "Proximate Analysis",
              "value": "proximate"
            },
            {
              "label": "Calorific Value (GCV)",
              "value": "calorific"
            },
            {
              "label": "Sulfur Content Analysis",
              "value": "sulfur"
            }
          ],
          "default": [
            "proximate",
            "calorific"
          ]
        }
      }
    ]
  },
  "labForm": {
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
    "fuse_corr": {
      "formula": "values[''fuse_correction''] or 0",
      "result": ""
    },
    "gcv_cal_g": {
      "formula": "round((values[''water_equivalent''] * values[''temp_rise''] - fuse_corr) / values[''sample_mass''])",
      "result": ""
    },
    "gcv_kj_kg": {
      "formula": "round(gcv_cal_g * 4.1868)",
      "result": ""
    }
  }
}'::jsonb
FROM sample_types WHERE name = 'Coal'
ON CONFLICT (sample_type_id, name) WHERE is_current = true AND deleted_at IS NULL DO NOTHING;


-- ── Coal / Sulfur Content Analysis ───────────────────────────────
INSERT INTO experiment_templates (sample_type_id, name, description, template)
SELECT id, 'Sulfur Content Analysis', 'Determine total sulfur content by titrimetric method',
'{
  "clientForm": {
    "title": "Select Analyses",
    "description": "Choose which analyses are required for this coal submission.",
    "questions": [
      {
        "id": "analyses",
        "type": "checkbox-group",
        "label": "Analyses",
        "config": {
          "options": [
            {
              "label": "Proximate Analysis",
              "value": "proximate"
            },
            {
              "label": "Calorific Value (GCV)",
              "value": "calorific"
            },
            {
              "label": "Sulfur Content Analysis",
              "value": "sulfur"
            }
          ],
          "default": [
            "proximate",
            "calorific"
          ]
        }
      }
    ]
  },
  "labForm": {
    "title": "Sulfur Analysis Form",
    "description": "Record sample mass and titration volumes.",
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
        "id": "titrant_volume",
        "type": "number",
        "label": "Volume of titrant used (mL)",
        "required": true,
        "config": {
          "min": 0,
          "max": 50,
          "step": 0.01,
          "default": 10.0
        }
      },
      {
        "id": "blank_volume",
        "type": "number",
        "label": "Blank titrant volume (mL)",
        "required": true,
        "config": {
          "min": 0,
          "max": 10,
          "step": 0.01,
          "default": 0.5
        }
      },
      {
        "id": "normality",
        "type": "number",
        "label": "Normality of titrant (N)",
        "required": true,
        "config": {
          "min": 0.001,
          "max": 1,
          "step": 0.001,
          "default": 0.1
        }
      }
    ]
  },
  "calculations": {
    "net_volume": {
      "formula": "values[''titrant_volume''] - values[''blank_volume'']",
      "result": ""
    },
    "sulfur_pct": {
      "formula": "round(10000 * (net_volume * values[''normality''] * 1.603) / values[''sample_mass'']) / 100",
      "result": ""
    }
  }
}'::jsonb
FROM sample_types WHERE name = 'Coal'
ON CONFLICT (sample_type_id, name) WHERE is_current = true AND deleted_at IS NULL DO NOTHING;


-- ══════════════════════════════════════════════════════════════════
-- TOMATO  (1 template)
-- ══════════════════════════════════════════════════════════════════

-- ── Tomato / Moisture Analysis ────────────────────────────────────
INSERT INTO experiment_templates (sample_type_id, name, description, template)
SELECT id, 'Moisture Analysis', 'Determine moisture content by drying method',
'{
  "clientForm": {
    "title": "Select Analyses",
    "description": "Choose which analyses are required for this tomato submission.",
    "questions": [
      {
        "id": "analyses",
        "type": "checkbox-group",
        "label": "Analyses",
        "config": {
          "options": [
            {
              "label": "Moisture Analysis",
              "value": "moisture"
            }
          ],
          "default": [
            "moisture"
          ]
        }
      }
    ]
  },
  "labForm": {
    "title": "Moisture Analysis Form",
    "description": "Record tray and sample masses before and after drying.",
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
        "required": true,
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
FROM sample_types WHERE name = 'Tomato'
ON CONFLICT (sample_type_id, name) WHERE is_current = true AND deleted_at IS NULL DO NOTHING;


-- ══════════════════════════════════════════════════════════════════
-- ENVIRONMENT WATER  (2 templates)
-- ══════════════════════════════════════════════════════════════════

-- ── Environment Water / pH Measurement ───────────────────────────
INSERT INTO experiment_templates (sample_type_id, name, description, template)
SELECT id, 'pH Measurement', 'Measure hydrogen ion concentration in water sample',
'{
  "clientForm": {
    "title": "Select Analyses",
    "description": "Choose which analyses are required for this water submission.",
    "questions": [
      {
        "id": "analyses",
        "type": "checkbox-group",
        "label": "Analyses",
        "config": {
          "options": [
            {
              "label": "pH Measurement",
              "value": "ph"
            },
            {
              "label": "Turbidity Measurement",
              "value": "turbidity"
            }
          ],
          "default": [
            "ph",
            "turbidity"
          ]
        }
      }
    ]
  },
  "labForm": {
    "title": "pH Measurement Form",
    "description": "Record pH meter readings for the water sample.",
    "questions": [
      {
        "id": "sample_id_label",
        "type": "string",
        "label": "Sample label / collection point",
        "required": true
      },
      {
        "id": "temperature",
        "type": "number",
        "label": "Sample temperature at measurement (°C)",
        "required": true,
        "config": {
          "min": 0,
          "max": 100,
          "step": 0.1,
          "default": 25.0
        }
      },
      {
        "id": "ph_reading_1",
        "type": "number",
        "label": "pH reading — replicate 1",
        "required": true,
        "config": {
          "min": 0,
          "max": 14,
          "step": 0.01,
          "default": 7.0
        }
      },
      {
        "id": "ph_reading_2",
        "type": "number",
        "label": "pH reading — replicate 2",
        "required": true,
        "config": {
          "min": 0,
          "max": 14,
          "step": 0.01,
          "default": 7.0
        }
      }
    ]
  },
  "calculations": {
    "ph_avg": {
      "formula": "round(100 * (values[''ph_reading_1''] + values[''ph_reading_2'']) / 2) / 100",
      "result": ""
    },
    "status": {
      "formula": "\"Acidic\" if ph_avg < 6.5 else (\"Alkaline\" if ph_avg > 8.5 else \"Neutral\")",
      "result": ""
    }
  }
}'::jsonb
FROM sample_types WHERE name = 'Environment Water'
ON CONFLICT (sample_type_id, name) WHERE is_current = true AND deleted_at IS NULL DO NOTHING;


-- ── Environment Water / Turbidity Measurement ─────────────────────
INSERT INTO experiment_templates (sample_type_id, name, description, template)
SELECT id, 'Turbidity Measurement', 'Measure water clarity using a nephelometric turbidimeter (NTU)',
'{
  "clientForm": {
    "title": "Select Analyses",
    "description": "Choose which analyses are required for this water submission.",
    "questions": [
      {
        "id": "analyses",
        "type": "checkbox-group",
        "label": "Analyses",
        "config": {
          "options": [
            {
              "label": "pH Measurement",
              "value": "ph"
            },
            {
              "label": "Turbidity Measurement",
              "value": "turbidity"
            }
          ],
          "default": [
            "ph",
            "turbidity"
          ]
        }
      }
    ]
  },
  "labForm": {
    "title": "Turbidity Form",
    "description": "Record turbidimeter readings.",
    "questions": [
      {
        "id": "sample_id_label",
        "type": "string",
        "label": "Sample label / collection point",
        "required": true
      },
      {
        "id": "ntu_reading_1",
        "type": "number",
        "label": "Turbidity reading — replicate 1 (NTU)",
        "required": true,
        "config": {
          "min": 0,
          "max": 1000,
          "step": 0.01,
          "default": 2.5
        }
      },
      {
        "id": "ntu_reading_2",
        "type": "number",
        "label": "Turbidity reading — replicate 2 (NTU)",
        "required": true,
        "config": {
          "min": 0,
          "max": 1000,
          "step": 0.01,
          "default": 2.5
        }
      }
    ]
  },
  "calculations": {
    "ntu_avg": {
      "formula": "round(100 * (values[''ntu_reading_1''] + values[''ntu_reading_2'']) / 2) / 100",
      "result": ""
    },
    "who_limit": {
      "formula": "5",
      "result": ""
    },
    "exceeds_limit": {
      "formula": "\"EXCEEDS WHO limit\" if ntu_avg > who_limit else \"Within WHO limit\"",
      "result": ""
    }
  }
}'::jsonb
FROM sample_types WHERE name = 'Environment Water'
ON CONFLICT (sample_type_id, name) WHERE is_current = true AND deleted_at IS NULL DO NOTHING;
