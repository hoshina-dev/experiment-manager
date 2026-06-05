DELETE FROM experiment_templates
WHERE name = 'Heat Capacity Analysis'
  AND sample_type_id = (SELECT id FROM sample_types WHERE name = 'Coal');
