-- report fields on experiments: populated by the in-process report worker after PDF generation
ALTER TABLE experiments
    ADD COLUMN report_status        TEXT,         -- NULL | 'pending' | 'processing' | 'success' | 'failed'
    ADD COLUMN report_r2_key        TEXT,         -- NULL until generation succeeds
    ADD COLUMN report_generated_at  TIMESTAMPTZ,  -- NULL until generation succeeds
    ADD COLUMN report_error         TEXT;         -- last failure message, NULL on success
