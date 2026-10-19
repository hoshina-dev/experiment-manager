BEGIN;

ALTER TABLE sample_types
    ADD COLUMN is_visible_on_web BOOLEAN NOT NULL DEFAULT false,
    ADD COLUMN display_order INTEGER;

WITH ranked AS (
    SELECT id, row_number() OVER (ORDER BY name, id)::integer AS position
    FROM sample_types
)
UPDATE sample_types s SET display_order = r.position,
    is_visible_on_web = (s.deleted_at IS NULL)
FROM ranked r WHERE r.id = s.id;

ALTER TABLE sample_types ALTER COLUMN display_order SET NOT NULL;
ALTER TABLE sample_types ADD CONSTRAINT sample_types_display_order_positive
    CHECK (display_order >= 1);

CREATE TABLE experiment_template_web_settings (
    lineage_id UUID PRIMARY KEY,
    sample_type_id UUID NOT NULL REFERENCES sample_types(id) ON DELETE RESTRICT,
    is_visible_on_web BOOLEAN NOT NULL DEFAULT false,
    display_order INTEGER NOT NULL CHECK (display_order >= 1),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE INDEX ix_experiment_template_web_settings_sample_type_id
    ON experiment_template_web_settings(sample_type_id);

WITH latest AS (
    SELECT DISTINCT ON (lineage_id) lineage_id, sample_type_id, name,
        is_current, deleted_at
    FROM experiment_templates
    ORDER BY lineage_id, version DESC
), ranked AS (
    SELECT *, row_number() OVER (
        PARTITION BY sample_type_id ORDER BY name, lineage_id
    )::integer AS position FROM latest
)
INSERT INTO experiment_template_web_settings
    (lineage_id, sample_type_id, is_visible_on_web, display_order)
SELECT lineage_id, sample_type_id, is_current AND deleted_at IS NULL, position
FROM ranked;

COMMIT;
