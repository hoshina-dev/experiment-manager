INSERT INTO experiment_templates (sample_type_id, name, description, template)
SELECT st.id,
       'Heat Capacity Analysis',
       'Bomb-calorimeter determination of specific and molar heat capacity',
       '{
  "clientForm": {
    "title": "Sample Information",
    "description": "Details of the specimen submitted for analysis.",
    "questions": [
      {
        "id": "sample_id",
        "type": "string",
        "label": "Sample ID",
        "required": true,
        "config": {
          "default": "CHR-001"
        }
      },
      {
        "id": "sample_source",
        "type": "string",
        "label": "Source / Grade",
        "required": true,
        "config": {
          "default": "Activated charcoal sample"
        }
      },
      {
        "id": "sample_mass",
        "type": "string",
        "label": "Sample mass (g)",
        "required": true,
        "config": {
          "default": "1.0000"
        }
      },
      {
        "id": "temperature_initial",
        "type": "string",
        "label": "Initial temperature (°C)",
        "required": true,
        "config": {
          "default": "25.00"
        }
      },
      {
        "id": "temperature_final",
        "type": "string",
        "label": "Final temperature (°C)",
        "required": true,
        "config": {
          "default": "30.00"
        }
      },
      {
        "id": "calorimeter_constant",
        "type": "string",
        "label": "Calorimeter constant (J/°C)",
        "required": true,
        "config": {
          "default": "9800.0"
        }
      }
    ]
  },
  "labForm": {
    "title": "Analyst Details",
    "description": "Completed by the laboratory analyst after measurement.",
    "questions": [
      {
        "id": "analyst_name",
        "type": "string",
        "label": "Analyst name",
        "config": {
          "default": "Analyst"
        }
      },
      {
        "id": "lab_id",
        "type": "string",
        "label": "Laboratory ID",
        "config": {
          "default": "LAB-001"
        }
      },
      {
        "id": "analysis_date",
        "type": "string",
        "label": "Analysis date",
        "config": {
          "default": "YYYY-MM-DD"
        }
      },
      {
        "id": "instrument",
        "type": "string",
        "label": "Instrument",
        "config": {
          "default": "Bomb Calorimeter"
        }
      },
      {
        "id": "method_ref",
        "type": "string",
        "label": "Method reference",
        "config": {
          "default": "ASTM D5865"
        }
      }
    ]
  },
  "calculations": {
    "delta_T": {
      "formula": "values[''temperature_final''] - values[''temperature_initial'']",
      "result": ""
    },
    "heat_released": {
      "formula": "round(values[''calorimeter_constant''] * delta_T * 100) / 100",
      "result": ""
    },
    "specific_heat": {
      "formula": "round(heat_released / values[''sample_mass''] * 10) / 10",
      "result": ""
    },
    "molar_heat_capacity": {
      "formula": "round(specific_heat * 12.011 * 10) / 10",
      "result": ""
    }
  }
}'::jsonb
FROM sample_types st
WHERE st.name = 'Coal'
ON CONFLICT (sample_type_id, name) WHERE is_current = true AND deleted_at IS NULL DO NOTHING;
