-- Requires 901_seed_experiment_templates + 903_seed_coal_calorific_value_experiment_template applied first.
INSERT INTO pdf_templates (template_id, components)
SELECT et.id, '[
  {
    "id": "header_bg",
    "type": "shape",
    "shape_type": "rect",
    "rect": [36, 720, 540, 52],
    "color": "#1565C0",
    "fill": true,
    "stroke_width": 0
  },
  {
    "id": "header_title",
    "type": "text",
    "rect": [46, 726, 520, 36],
    "content": "GROSS CALORIFIC VALUE (GCV) REPORT",
    "style": {
      "font": "Helvetica",
      "size": 18,
      "bold": true,
      "color": "#FFFFFF",
      "align": "center"
    }
  },
  {
    "id": "subheader_line",
    "type": "shape",
    "shape_type": "line",
    "rect": [36, 714, 540, 2],
    "color": "#1565C0",
    "stroke_width": 2
  },
  {
    "id": "meta_date",
    "type": "text",
    "rect": [36, 694, 260, 16],
    "content": "Analysis Date: {{analysis_date}}",
    "style": { "font": "Helvetica", "size": 10, "color": "#424242" }
  },
  {
    "id": "meta_time",
    "type": "text",
    "rect": [36, 676, 260, 16],
    "content": "Start Time: {{analysis_time}}",
    "style": { "font": "Helvetica", "size": 10, "color": "#424242" }
  },
  {
    "id": "meta_fuel",
    "type": "text",
    "rect": [316, 694, 260, 16],
    "content": "Fuel Type: {{fuel_type}}",
    "style": { "font": "Helvetica", "size": 10, "color": "#424242" }
  },
  {
    "id": "meta_grade",
    "type": "text",
    "rect": [316, 676, 260, 16],
    "content": "Sample Grade: {{sample_grade}}",
    "style": { "font": "Helvetica", "size": 10, "color": "#424242" }
  },
  {
    "id": "result_bg",
    "type": "shape",
    "shape_type": "rect",
    "rect": [36, 610, 540, 56],
    "color": "#E3F2FD",
    "fill": true,
    "stroke_width": 0
  },
  {
    "id": "result_border",
    "type": "shape",
    "shape_type": "rect",
    "rect": [36, 610, 540, 56],
    "color": "#1565C0",
    "fill": false,
    "stroke_width": 1
  },
  {
    "id": "result_label",
    "type": "text",
    "rect": [46, 648, 540, 14],
    "content": "RESULT",
    "style": {
      "font": "Helvetica",
      "size": 9,
      "bold": true,
      "color": "#1565C0",
      "align": "center"
    }
  },
  {
    "id": "result_value",
    "type": "text",
    "rect": [46, 618, 540, 24],
    "content": "GCV = {{gcv_cal_g}} cal/g  ({{gcv_kj_kg}} kJ/kg)",
    "style": {
      "font": "Helvetica",
      "size": 20,
      "bold": true,
      "color": "#0D47A1",
      "align": "center"
    }
  },
  {
    "id": "section_measurements",
    "type": "text",
    "rect": [36, 590, 540, 16],
    "content": "MEASUREMENT INPUTS",
    "style": {
      "font": "Helvetica",
      "size": 10,
      "bold": true,
      "color": "#1565C0"
    }
  },
  {
    "id": "section_line",
    "type": "shape",
    "shape_type": "line",
    "rect": [36, 587, 540, 1],
    "color": "#BBDEFB",
    "stroke_width": 1
  },
  {
    "id": "meas_sample_mass",
    "type": "text",
    "rect": [36, 565, 260, 16],
    "content": "Sample mass: {{sample_mass}} g",
    "style": { "font": "Helvetica", "size": 11, "color": "#212121" }
  },
  {
    "id": "meas_water_equiv",
    "type": "text",
    "rect": [36, 547, 260, 16],
    "content": "Water equivalent: {{water_equivalent}} cal/°C",
    "style": { "font": "Helvetica", "size": 11, "color": "#212121" }
  },
  {
    "id": "meas_temp_rise",
    "type": "text",
    "rect": [36, 529, 260, 16],
    "content": "Temperature rise: {{temp_rise}} °C",
    "style": { "font": "Helvetica", "size": 11, "color": "#212121" }
  },
  {
    "id": "meas_fuse_corr",
    "type": "text",
    "rect": [36, 511, 260, 16],
    "content": "Fuse wire correction: {{fuse_correction}} cal",
    "style": { "font": "Helvetica", "size": 11, "color": "#212121" }
  },
  {
    "id": "meas_o2_pressure",
    "type": "text",
    "rect": [316, 565, 260, 16],
    "content": "O₂ pressure: {{combustion_pressure}} atm",
    "style": { "font": "Helvetica", "size": 11, "color": "#212121" }
  },
  {
    "id": "meas_confidence",
    "type": "text",
    "rect": [316, 547, 260, 16],
    "content": "Result confidence: {{confidence}}%",
    "style": { "font": "Helvetica", "size": 11, "color": "#212121" }
  },
  {
    "id": "meas_validity",
    "type": "text",
    "rect": [316, 529, 260, 16],
    "content": "Test validity: {{test_validity}}",
    "style": { "font": "Helvetica", "size": 11, "color": "#212121" }
  },
  {
    "id": "meas_quality",
    "type": "text",
    "rect": [316, 511, 260, 16],
    "content": "Sample quality: {{sample_quality}} / 5",
    "style": { "font": "Helvetica", "size": 11, "color": "#212121" }
  },
  {
    "id": "section_calc",
    "type": "text",
    "rect": [36, 488, 540, 16],
    "content": "CALCULATED VALUES",
    "style": {
      "font": "Helvetica",
      "size": 10,
      "bold": true,
      "color": "#1565C0"
    }
  },
  {
    "id": "calc_line",
    "type": "shape",
    "shape_type": "line",
    "rect": [36, 485, 540, 1],
    "color": "#BBDEFB",
    "stroke_width": 1
  },
  {
    "id": "calc_fuse_corr",
    "type": "text",
    "rect": [36, 465, 260, 16],
    "content": "Fuse correction (calc): {{fuse_corr}} cal",
    "style": { "font": "Helvetica", "size": 11, "color": "#212121" }
  },
  {
    "id": "calc_gcv_cal",
    "type": "text",
    "rect": [36, 447, 260, 16],
    "content": "GCV: {{gcv_cal_g}} cal/g",
    "style": { "font": "Helvetica", "size": 11, "bold": true, "color": "#212121" }
  },
  {
    "id": "calc_gcv_kj",
    "type": "text",
    "rect": [316, 447, 260, 16],
    "content": "GCV: {{gcv_kj_kg}} kJ/kg",
    "style": { "font": "Helvetica", "size": 11, "bold": true, "color": "#212121" }
  },
  {
    "id": "page1_footer_line",
    "type": "shape",
    "shape_type": "line",
    "rect": [36, 60, 540, 1],
    "color": "#BDBDBD",
    "stroke_width": 1
  },
  {
    "id": "page1_footer",
    "type": "text",
    "rect": [36, 44, 540, 12],
    "content": "Calorific Value (GCV)  —  Continued on next page",
    "style": {
      "font": "Helvetica",
      "size": 8,
      "italic": true,
      "color": "#9E9E9E",
      "align": "center"
    }
  },
  {
    "id": "page_break_1",
    "type": "pagebreak"
  },
  {
    "id": "p2_header_bg",
    "type": "shape",
    "shape_type": "rect",
    "rect": [36, 720, 540, 36],
    "color": "#1565C0",
    "fill": true,
    "stroke_width": 0
  },
  {
    "id": "p2_header_title",
    "type": "text",
    "rect": [46, 726, 520, 24],
    "content": "GCV REPORT  —  Analyst & QC Details",
    "style": {
      "font": "Helvetica",
      "size": 13,
      "bold": true,
      "color": "#FFFFFF",
      "align": "center"
    }
  },
  {
    "id": "section_analyst",
    "type": "text",
    "rect": [36, 696, 540, 16],
    "content": "ANALYST INFORMATION",
    "style": {
      "font": "Helvetica",
      "size": 10,
      "bold": true,
      "color": "#1565C0"
    }
  },
  {
    "id": "analyst_line",
    "type": "shape",
    "shape_type": "line",
    "rect": [36, 693, 540, 1],
    "color": "#BBDEFB",
    "stroke_width": 1
  },
  {
    "id": "analyst_name",
    "type": "text",
    "rect": [36, 673, 260, 16],
    "content": "Analyst: {{analyst_name}}",
    "style": { "font": "Helvetica", "size": 11, "color": "#212121" }
  },
  {
    "id": "analyst_date",
    "type": "text",
    "rect": [316, 673, 260, 16],
    "content": "Certified: {{certified}}",
    "style": { "font": "Helvetica", "size": 11, "color": "#212121" }
  },
  {
    "id": "analyst_timestamp",
    "type": "text",
    "rect": [36, 655, 400, 16],
    "content": "Test started at: {{test_started_at}}",
    "style": { "font": "Helvetica", "size": 11, "color": "#212121" }
  },
  {
    "id": "section_qc",
    "type": "text",
    "rect": [36, 630, 540, 16],
    "content": "QC CHECKLIST",
    "style": {
      "font": "Helvetica",
      "size": 10,
      "bold": true,
      "color": "#1565C0"
    }
  },
  {
    "id": "qc_line",
    "type": "shape",
    "shape_type": "line",
    "rect": [36, 627, 540, 1],
    "color": "#BBDEFB",
    "stroke_width": 1
  },
  {
    "id": "qc_checks",
    "type": "text",
    "rect": [36, 607, 540, 16],
    "content": "QC checks: {{qc_checks}}",
    "style": { "font": "Helvetica", "size": 11, "color": "#212121" }
  },
  {
    "id": "corrections",
    "type": "text",
    "rect": [36, 589, 540, 16],
    "content": "Corrections applied: {{corrections_applied}}",
    "style": { "font": "Helvetica", "size": 11, "color": "#212121" }
  },
  {
    "id": "section_notes",
    "type": "text",
    "rect": [36, 562, 540, 16],
    "content": "LAB OBSERVATIONS",
    "style": {
      "font": "Helvetica",
      "size": 10,
      "bold": true,
      "color": "#1565C0"
    }
  },
  {
    "id": "notes_line",
    "type": "shape",
    "shape_type": "line",
    "rect": [36, 559, 540, 1],
    "color": "#BBDEFB",
    "stroke_width": 1
  },
  {
    "id": "notes_bg",
    "type": "shape",
    "shape_type": "rect",
    "rect": [36, 460, 540, 96],
    "color": "#FAFAFA",
    "fill": true,
    "stroke_width": 1
  },
  {
    "id": "lab_notes",
    "type": "text",
    "rect": [44, 464, 524, 88],
    "content": "{{lab_notes}}",
    "style": {
      "font": "Helvetica",
      "size": 10,
      "italic": true,
      "color": "#424242"
    }
  },
  {
    "id": "footer_line",
    "type": "shape",
    "shape_type": "line",
    "rect": [36, 80, 540, 1],
    "color": "#BDBDBD",
    "stroke_width": 1
  },
  {
    "id": "footer_exp",
    "type": "text",
    "rect": [36, 64, 360, 12],
    "content": "Experiment: {{name}}  |  Template: {{template}}",
    "style": {
      "font": "Helvetica",
      "size": 8,
      "color": "#9E9E9E"
    }
  },
  {
    "id": "footer_tags",
    "type": "text",
    "rect": [36, 50, 540, 12],
    "content": "Tags: {{sample_tags}}",
    "style": {
      "font": "Helvetica",
      "size": 8,
      "italic": true,
      "color": "#BDBDBD",
      "align": "right"
    }
  }
]'::jsonb
FROM experiment_templates et
JOIN sample_types st ON et.sample_type_id = st.id
WHERE et.name = 'Calorific Value (GCV)'
  AND st.name = 'Coal'
  AND et.deleted_at IS NULL
ON CONFLICT (template_id) DO UPDATE SET
    components = EXCLUDED.components,
    updated_at = NOW();
