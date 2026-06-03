INSERT INTO sample_types (id, name, description)
VALUES
  ('a1b2c3d4-0001-0001-0001-000000000001', 'Tomato',            'Fresh tomato samples for agricultural and food quality analysis'),
  ('a1b2c3d4-0002-0002-0002-000000000002', 'Coal',              'Coal samples for energy content and combustion property analysis'),
  ('a1b2c3d4-0003-0003-0003-000000000003', 'Environment Water', 'Water samples for environmental quality and safety monitoring')
ON CONFLICT (name) WHERE deleted_at IS NULL DO NOTHING;