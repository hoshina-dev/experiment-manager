-- Add a DB-level default to lineage_id so that seed INSERTs that pre-date
-- migration 005 (which do not supply lineage_id) auto-generate a UUID rather
-- than failing with a NOT NULL constraint violation.
ALTER TABLE experiment_templates
    ALTER COLUMN lineage_id SET DEFAULT uuid_generate_v4();

-- Track which pdf_template row is the active version for a lineage, mirroring
-- the is_current flag on experiment_templates. Old version rows are retired
-- (is_current = false) whenever a new SCD2 version is created.
ALTER TABLE pdf_templates
    ADD COLUMN is_current BOOLEAN NOT NULL DEFAULT true;
