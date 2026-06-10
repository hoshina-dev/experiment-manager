-- Add a DB-level default to lineage_id so that seed INSERTs that pre-date
-- migration 005 (which do not supply lineage_id) auto-generate a UUID rather
-- than failing with a NOT NULL constraint violation.
ALTER TABLE experiment_templates
    ALTER COLUMN lineage_id SET DEFAULT uuid_generate_v4();
