-- Migration 002 created uq_experiment_templates_name_active, which enforces unique
-- (sample_type_id, name) for every non-deleted row. SCD2 keeps retired versions
-- with the same name, so PDF/template edits that create a new version violate it.
-- Migration 005 added the correct partial index but did not drop this stale one.

DROP INDEX IF EXISTS uq_experiment_templates_name_active;

CREATE UNIQUE INDEX IF NOT EXISTS uq_experiment_templates_current_name
    ON experiment_templates (sample_type_id, name)
    WHERE is_current = true AND deleted_at IS NULL;
