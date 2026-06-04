ALTER TABLE experiments
    DROP COLUMN IF EXISTS report_status,
    DROP COLUMN IF EXISTS report_r2_key,
    DROP COLUMN IF EXISTS report_generated_at,
    DROP COLUMN IF EXISTS report_error;
