ALTER TABLE pdf_templates DROP COLUMN is_current;
ALTER TABLE experiment_templates ALTER COLUMN lineage_id DROP DEFAULT;
