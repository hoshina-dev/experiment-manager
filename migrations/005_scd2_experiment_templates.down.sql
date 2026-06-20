-- Revert SCD2 migration.
-- WARNING: this will permanently drop lineage_id, version, and is_current data.

DROP INDEX IF EXISTS idx_experiment_templates_lineage_id;
DROP INDEX IF EXISTS uq_experiment_templates_lineage_version;
DROP INDEX IF EXISTS uq_experiment_templates_current_name;

-- Falls back to whatever 002 left in place (uq_experiment_templates_name_active);
-- the original hard UNIQUE constraint is 002's to restore, not 005's.

ALTER TABLE experiment_templates
    DROP COLUMN lineage_id,
    DROP COLUMN version,
    DROP COLUMN is_current;