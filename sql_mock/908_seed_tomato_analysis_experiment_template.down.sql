DELETE FROM experiment_templates
WHERE name = 'Tomato Analysis'
  AND sample_type_id = (SELECT id FROM sample_types WHERE name = 'Tomato');
