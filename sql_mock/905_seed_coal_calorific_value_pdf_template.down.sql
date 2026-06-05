DELETE FROM pdf_templates
USING experiment_templates et
JOIN sample_types st ON et.sample_type_id = st.id
WHERE pdf_templates.template_id = et.id
  AND et.name = 'Calorific Value (GCV)'
  AND st.name = 'Coal';
