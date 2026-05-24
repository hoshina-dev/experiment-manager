-- DROP TRIGGER IF EXISTS trg_experiments_updated_at ON experiments;
-- DROP TRIGGER IF EXISTS trg_experiment_templates_updated_at ON experiment_templates;
-- DROP TRIGGER IF EXISTS trg_sample_types_updated_at ON sample_types;

DROP FUNCTION IF EXISTS set_updated_at();

DROP TABLE IF EXISTS experiments;
DROP TABLE IF EXISTS experiment_templates;
DROP TABLE IF EXISTS sample_types;

DROP EXTENSION IF EXISTS "uuid-ossp";
