-- this is for editor and experiment manager, experiment manager matches exp_tmpl_id and 
-- send both "experiment" and "pdf_templates" to stateless report gen engine in argo workflow
CREATE TABLE pdf_templates (
    exp_tmpl_id  UUID PRIMARY KEY REFERENCES experiment_templates(id) ON DELETE CASCADE,
    components   JSONB NOT NULL DEFAULT '[]',
    created_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
