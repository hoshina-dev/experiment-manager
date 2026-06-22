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
  "clientForm": {
    "name": "Client Form",
    "questions": []
  },
  "labForm": {
    "name": "GCV Measurement Form",
    "description": "Record bomb calorimeter readings and analyst information.",
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
          "default": 1
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
          "default": 2526
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
          "default": 2
        }
      },
      {
        "id": "analyst_name",
        "type": "string",
        "label": "Analyst name",
        "required": true,
        "config": {
          "maxLength": 80,
          "default": "Dr. Analyst",
          "placeholder": "e.g. Dr. Smith"
        }
      },
      {
        "id": "lab_notes",
        "type": "textarea",
        "label": "Observations during test",
        "config": {
          "maxLength": 500,
          "default": "No anomalous exotherms detected during combustion. Sample ignited cleanly on first attempt. Result within expected range for this fuel grade.",
          "placeholder": "e.g. No anomalous exotherms detected...",
          "minRows": 3,
          "maxRows": 8
        }
      },
      {
        "id": "instrument_code",
        "type": "password",
        "label": "Instrument calibration code",
        "config": {
          "minLength": 4,
          "placeholder": "•••••••"
        }
      },
      {
        "id": "fuel_type",
        "type": "select-string",
        "label": "Fuel type",
        "required": true,
        "config": {
          "options": [
            {
              "label": "Coal (Bituminous)",
              "value": "Coal (Bituminous)"
            },
            {
              "label": "Coal (Anthracite)",
              "value": "Coal (Anthracite)"
            },
            {
              "label": "Coke",
              "value": "Coke"
            },
            {
              "label": "Lignite",
              "value": "Lignite"
            },
            {
              "label": "Biomass",
              "value": "Biomass"
            }
          ],
          "default": "Coal (Bituminous)",
          "placeholder": "Select fuel type"
        }
      },
      {
        "id": "combustion_pressure",
        "type": "select-number",
        "label": "Combustion O₂ pressure (atm)",
        "config": {
          "options": [
            {
              "label": "25 atm",
              "value": 25
            },
            {
              "label": "30 atm",
              "value": 30
            },
            {
              "label": "35 atm",
              "value": 35
            }
          ],
          "default": 30
        }
      },
      {
        "id": "corrections_applied",
        "type": "multi-select",
        "label": "Corrections applied",
        "config": {
          "options": [
            {
              "label": "Fuse wire",
              "value": "fuse"
            },
            {
              "label": "Acid formation",
              "value": "acid"
            },
            {
              "label": "Nitrogen correction",
              "value": "nitrogen"
            },
            {
              "label": "Sulfur correction",
              "value": "sulfur"
            }
          ],
          "default": [
            "fuse"
          ],
          "placeholder": "Pick corrections",
          "maxValues": 5
        }
      },
      {
        "id": "test_validity",
        "type": "radio",
        "label": "Test validity",
        "required": true,
        "config": {
          "options": [
            {
              "label": "Valid",
              "value": "Valid"
            },
            {
              "label": "Invalid — discard",
              "value": "Invalid"
            },
            {
              "label": "Repeat required",
              "value": "Repeat"
            }
          ],
          "default": "Valid"
        }
      },
      {
        "id": "qc_checks",
        "type": "checkbox-group",
        "label": "QC checklist completed",
        "config": {
          "options": [
            {
              "label": "Calorimeter calibration verified",
              "value": "calibration"
            },
            {
              "label": "Blank run performed",
              "value": "blank_run"
            },
            {
              "label": "Reference material checked",
              "value": "reference"
            },
            {
              "label": "Duplicate run performed",
              "value": "duplicate"
            }
          ],
          "default": [
            "calibration",
            "reference"
          ]
        }
      },
      {
        "id": "certified",
        "type": "boolean",
        "label": "Certified measurement",
        "config": {
          "default": true
        }
      },
      {
        "id": "sample_grade",
        "type": "segmented",
        "label": "Sample grade",
        "config": {
          "options": [
            {
              "label": "Grade A",
              "value": "A"
            },
            {
              "label": "Grade B",
              "value": "B"
            },
            {
              "label": "Grade C",
              "value": "C"
            }
          ],
          "default": "A"
        }
      },
      {
        "id": "confidence",
        "type": "slider",
        "label": "Result confidence (%)",
        "config": {
          "min": 0,
          "max": 100,
          "step": 5,
          "default": 95,
          "marks": [
            {
              "value": 0,
              "label": "0%"
            },
            {
              "value": 50,
              "label": "50%"
            },
            {
              "value": 100,
              "label": "100%"
            }
          ]
        }
      },
      {
        "id": "sample_quality",
        "type": "rating",
        "label": "Sample quality",
        "config": {
          "count": 5,
          "fractions": 1,
          "default": 4
        }
      },
      {
        "id": "sample_color",
        "type": "color",
        "label": "Sample color (visual observation)",
        "config": {
          "default": "#212121",
          "swatches": [
            "#212121",
            "#546E7A",
            "#795548",
            "#8D6E63",
            "#BDBDBD",
            "#F5F5F5"
          ]
        }
      },
      {
        "id": "analysis_date",
        "type": "date",
        "label": "Analysis date",
        "required": true,
        "config": {
          "default": "2026-06-01"
        }
      },
      {
        "id": "analysis_time",
        "type": "time",
        "label": "Analysis start time",
        "config": {
          "default": "09:00"
        }
      },
      {
        "id": "test_started_at",
        "type": "datetime",
        "label": "Test start (date + time)",
        "config": {
          "default": "2026-06-01T09:00"
        }
      },
      {
        "id": "sample_tags",
        "type": "tags",
        "label": "Sample tags",
        "config": {
          "default": [
            "gcv",
            "calorimetry",
            "coal"
          ],
          "placeholder": "Type and press Enter",
          "maxTags": 8
        }
      }
    ]
  },
  "calculations": {
    "fuse_corr": {
      "formula": "values[''fuse_correction''] or 0",
      "result": 2.0
    },
    "gcv_cal_g": {
      "formula": "round((values[''water_equivalent''] * values[''temp_rise''] - fuse_corr) / values[''sample_mass''])",
      "result": 6313.0
    },
    "gcv_kj_kg": {
      "formula": "round(gcv_cal_g * 4.1868)",
      "result": 26431.0
    }
  },
  "values": {
    "sample_mass": 1,
    "water_equivalent": 2526,
    "temp_rise": 2.5,
    "fuse_correction": 2,
    "analyst_name": "Dr. Pornpun Kittipanya",
    "lab_notes": "No anomalous exotherms detected during combustion. Sample ignited cleanly on first attempt. Result within expected range for this fuel grade.",
    "instrument_code": "CAL-2024-88",
    "fuel_type": "Coal (Bituminous)",
    "combustion_pressure": 30,
    "corrections_applied": [
      "fuse"
    ],
    "test_validity": "Valid",
    "qc_checks": [
      "calibration",
      "blank_run",
      "reference"
    ],
    "certified": true,
    "sample_grade": "A",
    "confidence": 95,
    "sample_quality": 4,
    "sample_color": "#212121",
    "analysis_date": "2026-06-04",
    "analysis_time": "09:15",
    "test_started_at": "2026-06-04T09:15",
    "sample_tags": [
      "gcv",
      "calorimetry",
      "coal",
      "certified"
    ]
  },
  "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "name": "Calorific Value (GCV)",
  "description": "Determine gross calorific value by bomb calorimetry"
}'::jsonb, '{sample_id}', to_jsonb(refs.sample_id::text)),
    '{template_id}', to_jsonb(refs.template_id::text)
  )
FROM refs
ON CONFLICT (id) DO NOTHING;
