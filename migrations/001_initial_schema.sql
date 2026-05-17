-- This design has 1 assumption: Ticketing service database will have at least 2 tables:
-- 1. tickets               contain status of each ticket.
-- 2. ticket_experiments    many2many relation of each ticket with experiment templates. For example, ticket X has to do Proximate analysis & Calorific analysis

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

-- Specific experiment within a type
-- e.g. Coal -> "Proximate analysis", "Calorific value"
CREATE TABLE experiment_templates (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    sample_type_id  UUID NOT NULL REFERENCES sample_types(id) ON DELETE RESTRICT,
    name            TEXT NOT NULL,
    description     TEXT,

    template        JSONB NOT NULL, -- จท

    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at      TIMESTAMPTZ,
    UNIQUE (sample_type_id, name)
);

CREATE INDEX idx_experiment_templates_sample_type ON experiment_templates(sample_type_id);

-- State of input form for each ticket
CREATE TABLE experiments (
    id           UUID PRIMARY KEY, -- Uses the same id as ticket_analyses id, as it has 1-1 relation.

    state        JSONB NOT NULL,

    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    deleted_at   TIMESTAMPTZ,
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