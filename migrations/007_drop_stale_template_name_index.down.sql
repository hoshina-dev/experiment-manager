DROP INDEX IF EXISTS uq_experiment_templates_current_name;

CREATE UNIQUE INDEX IF NOT EXISTS uq_experiment_templates_name_active
    ON experiment_templates(sample_type_id, name)
    WHERE deleted_at IS NULL;
