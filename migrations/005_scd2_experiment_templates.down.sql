-- Revert SCD2 migration.
-- WARNING: this will permanently drop lineage_id, version, and is_current data.

DROP INDEX IF EXISTS idx_experiment_templates_lineage_id;
DROP INDEX IF EXISTS uq_experiment_templates_lineage_version;
DROP INDEX IF EXISTS uq_experiment_templates_current_name;

ALTER TABLE experiment_templates
    ADD CONSTRAINT experiment_templates_sample_type_id_name_key
        UNIQUE (sample_type_id, name);

ALTER TABLE experiment_templates
    DROP COLUMN lineage_id,
    DROP COLUMN version,
    DROP COLUMN is_current;