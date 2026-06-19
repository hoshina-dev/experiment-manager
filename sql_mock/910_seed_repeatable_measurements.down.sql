DELETE FROM experiment_templates
WHERE name = 'Repeatable Measurements'
  AND sample_type_id = (SELECT id FROM sample_types WHERE name = 'Material Sample');

DELETE FROM sample_types
WHERE name = 'Material Sample';
