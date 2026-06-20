-- uq_experiment_templates_current_name belongs to migration 005, not 007 —
-- only restore what 007.up actually dropped.
CREATE UNIQUE INDEX IF NOT EXISTS uq_experiment_templates_name_active
    ON experiment_templates(sample_type_id, name)
    WHERE deleted_at IS NULL;
