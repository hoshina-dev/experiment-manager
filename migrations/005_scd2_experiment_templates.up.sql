-- SCD Type 2 for experiment_templates. (Datawarehousing concept, i cant think of other name for this eventhough database schema is not dimension)
--
-- Each edit to a template creates a new row (new id, same lineage_id, version+1,
-- is_current=true) rather than mutating the existing row. Experiments freeze the
-- specific version id at creation time, so their pdf_template and snapshot are
-- immutable for the lifetime of the experiment.

-- Step 1: add columns as nullable so backfill can run before NOT NULL is enforced
ALTER TABLE experiment_templates
    ADD COLUMN lineage_id UUID,
    ADD COLUMN version    INT,
    ADD COLUMN is_current BOOLEAN;

-- Step 2: backfill — every existing row becomes v1, current, self-referencing lineage
UPDATE experiment_templates
   SET lineage_id = id,
       version    = 1,
       is_current = true;

-- Step 3: enforce NOT NULL now that every row has values
ALTER TABLE experiment_templates
    ALTER COLUMN lineage_id SET NOT NULL,
    ALTER COLUMN version    SET NOT NULL,
    ALTER COLUMN is_current SET NOT NULL;

-- Step 4: sensible defaults for future inserts
ALTER TABLE experiment_templates
    ALTER COLUMN version    SET DEFAULT 1,
    ALTER COLUMN is_current SET DEFAULT true;

-- Step 5: only one active (current, non-deleted) version of a name per sample
-- (the old hard UNIQUE(sample_type_id, name) constraint was already replaced
-- by uq_experiment_templates_name_active back in migration 002 — nothing to
-- drop here. The now-stale 002 index is cleaned up later by migration 007.)
CREATE UNIQUE INDEX uq_experiment_templates_current_name
    ON experiment_templates (sample_type_id, name)
    WHERE is_current = true AND deleted_at IS NULL;

-- Step 6: no duplicate version numbers within a lineage
CREATE UNIQUE INDEX uq_experiment_templates_lineage_version
    ON experiment_templates (lineage_id, version);

-- Step 7: fast lookup of all versions for a lineage (editor history view)
CREATE INDEX idx_experiment_templates_lineage_id
    ON experiment_templates (lineage_id);