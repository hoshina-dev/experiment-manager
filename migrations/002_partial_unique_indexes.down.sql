-- Restore hard UNIQUE constraints (reverses 002_partial_unique_indexes.up.sql)

DROP INDEX IF EXISTS uq_sample_types_name_active;
ALTER TABLE sample_types ADD CONSTRAINT sample_types_name_key UNIQUE (name);

DROP INDEX IF EXISTS uq_experiment_templates_name_active;
ALTER TABLE experiment_templates ADD CONSTRAINT experiment_templates_sample_type_id_name_key UNIQUE (sample_type_id, name);
