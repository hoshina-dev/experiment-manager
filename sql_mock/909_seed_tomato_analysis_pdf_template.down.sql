DELETE FROM pdf_templates
WHERE template_id = (
    SELECT et.id
    FROM experiment_templates et
    JOIN sample_types st ON et.sample_type_id = st.id
    WHERE et.name = 'Tomato Analysis'
      AND st.name = 'Tomato'
);
