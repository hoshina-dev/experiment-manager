-- Coal / Heat Capacity experiment — completed, worker values filled in.
-- sample_id and template_id resolved by JOIN; no hardcoded UUIDs.
WITH refs AS (
  SELECT et.id AS template_id, st.id AS sample_id
  FROM experiment_templates et
  JOIN sample_types st ON et.sample_type_id = st.id
  WHERE et.name = 'Heat Capacity Analysis'
    AND st.name = 'Coal'
    AND et.deleted_at IS NULL
)
INSERT INTO experiments (id, state)
SELECT
  '7b1e39a5-86e2-433f-a194-397061316cb6'::uuid,
  jsonb_set(
    jsonb_set(
    '{
  "clientForm": {
    "name": "Sample Information",
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
    "name": "Analyst Details",
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
      "result": 5.35
    },
    "heat_released": {
      "formula": "round(values[''calorimeter_constant''] * delta_T * 100) / 100",
      "result": 52657.75
    },
    "specific_heat": {
      "formula": "round(heat_released / values[''sample_mass''] * 10) / 10",
      "result": 42670.0
    },
    "molar_heat_capacity": {
      "formula": "round(specific_heat * 12.011 * 10) / 10",
      "result": 512.3
    }
  },
  "values": {
    "sample_id": "CHR-2024-047",
    "sample_source": "Activated coconut charcoal, 99.5% purity (Sigma-Aldrich #C9157)",
    "sample_mass": "1.2340",
    "temperature_initial": "24.82",
    "temperature_final": "30.17",
    "calorimeter_constant": "9845.0",
    "analyst_name": "Dr. Pornpun Kittipanya",
    "lab_id": "TH-CHEM-LAB-03",
    "analysis_date": "2024-11-14",
    "instrument": "Parr 6200 Isoperibol Calorimeter",
    "method_ref": "ASTM D5865 / ISO 1928"
  },
  "id": "7b1e39a5-86e2-433f-a194-397061316cb6",
  "name": "Heat Capacity Analysis",
  "description": "Bomb-calorimeter determination of specific and molar heat capacity"
}'::jsonb,
    '{sample_id}', to_jsonb(refs.sample_id::text)),
    '{template_id}', to_jsonb(refs.template_id::text)
  )
FROM refs
ON CONFLICT (id) DO NOTHING;
