BEGIN;
DROP TABLE experiment_template_web_settings;
ALTER TABLE sample_types DROP CONSTRAINT sample_types_display_order_positive;
ALTER TABLE sample_types DROP COLUMN display_order, DROP COLUMN is_visible_on_web;
COMMIT;
