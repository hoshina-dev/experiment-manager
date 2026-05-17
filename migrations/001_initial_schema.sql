CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- High-level category: Coal, Soil, Water, etc.
CREATE TABLE sample_types (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name            TEXT NOT NULL,
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ
);

-- Specific analysis within a type
-- e.g. Coal -> "Proximate analysis", "Calorific value"
CREATE TABLE analyses (
    id                  UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sample_type_id      UUID NOT NULL REFERENCES sample_types(id) ON DELETE RESTRICT,
    name                TEXT NOT NULL,
    description         TEXT,

    user_inputs         JSONB,

    -- e.g. [{"code": "crucible_mass", "label": "Crucible Mass (g)", ...}, {...}, ...]
    analysis_inputs     JSONB NOT NULL DEFAULT '[]'::jsonb,

    -- e.g. [{"code": "moisture_loss", "label": "Moisture Loss (%)", "formula": "(sample_mass - mass_after_moisture) / (sample_mass * 100)"}, {...}, ...]
    calculations        JSONB NOT NULL DEFAULT '[]'::jsonb,

    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,
    UNIQUE (sample_type_id, name)
);

CREATE INDEX idx_analyses_sample_type ON analyses(sample_type_id);

-- State of input form for each ticket
CREATE TABLE job_inputs (
    id                      UUID PRIMARY KEY, -- Uses the same id as ticket_analyses id, as it has 1-1 relation.

    user_form_state         JSONB NOT NULL,
    technician_form_state   JSONB NOT NULL,

    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at              TIMESTAMPTZ,
);

CREATE INDEX idx_job_inputs_job_analysis ON job_inputs(job_id);

-- Final reportable values.
-- Produced by evaluating calculation formulas against job_inputs.
CREATE TABLE job_results (
    id                  UUID PRIMARY KEY,   -- Uses the same id as ticket_analyses id, as it has 1-1 relation.
    value               JSONB NOT NULL,     -- e.g. [{"code": "moisture_loss", "label": "Moisture Loss (%)", "result": 32}, {...}, ...]
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at          TIMESTAMPTZ,
);

-- updated_at triggers
CREATE OR REPLACE FUNCTION set_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_sample_types_updated_at BEFORE UPDATE ON sample_types
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_analyses_updated_at BEFORE UPDATE ON analyses
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_job_inputs_updated_at BEFORE UPDATE ON job_inputs
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();
CREATE TRIGGER trg_job_results_updated_at BEFORE UPDATE ON job_results
    FOR EACH ROW EXECUTE FUNCTION set_updated_at();