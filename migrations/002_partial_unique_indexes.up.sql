ALTER TABLE sample_types DROP CONSTRAINT sample_types_name_key; -- sample_types_name_key
CREATE UNIQUE INDEX uq_sample_types_name_active
    ON sample_types(name)
    WHERE deleted_at IS NULL; -- soft constraint unique 

ALTER TABLE experiment_templates DROP CONSTRAINT experiment_templates_sample_type_id_name_key;
CREATE UNIQUE INDEX uq_experiment_templates_name_active
    ON experiment_templates(sample_type_id, name)
    WHERE deleted_at IS NULL;
