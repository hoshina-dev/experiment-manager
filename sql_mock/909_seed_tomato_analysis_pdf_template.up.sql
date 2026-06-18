
INSERT INTO pdf_templates (template_id, components)
SELECT et.id, '[
  {"id": "header_bg",               "type": "shape", "shape_type": "rect", "rect": [0, 742, 612, 50],    "color": "#2E7D32", "stroke_width": 0,    "fill": true},
  {"id": "header_accent",           "type": "shape", "shape_type": "rect", "rect": [0, 738, 612, 4],     "color": "#1B5E20", "stroke_width": 0,    "fill": true},
  {"id": "header_title",            "type": "text",  "content": "TOMATO ANALYSIS REPORT",                "rect": [24, 763, 420, 22], "style": {"font": "Helvetica", "size": 16, "bold": true,  "italic": false, "align": "left",   "color": "#FFFFFF"}},
  {"id": "header_subtitle",         "type": "text",  "content": "Moisture Content Determination — Fresh Tomato, Ranch 1982", "rect": [24, 743, 420, 16], "style": {"font": "Helvetica", "size": 10, "bold": false, "italic": false, "align": "left",   "color": "#C8E6C9"}},
  {"id": "header_label",            "type": "text",  "content": "Ranch 1982 Specimen",                   "rect": [460, 751, 130, 12], "style": {"font": "Helvetica", "size": 9,  "bold": false, "italic": false, "align": "right",  "color": "#C8E6C9"}},
  {"id": "section_sample_label",    "type": "text",  "content": "SAMPLE INFORMATION",                    "rect": [50, 717, 250, 14],  "style": {"font": "Helvetica", "size": 9,  "bold": true,  "italic": false, "align": "left",   "color": "#2E7D32"}},
  {"id": "section_sample_divider",  "type": "shape", "shape_type": "line", "rect": [50, 714, 512, 2],    "color": "#2E7D32", "stroke_width": 0.75, "fill": false},
  {"id": "sample_info",             "type": "text",  "content": "Sample type:   Fresh Tomato — Ranch 1982\nTray mass:     {{tray_mass}} g\nSample mass:   {{sample_mass}} g\nMethod:        Gravimetric oven-drying (constant-mass criterion)", "rect": [50, 636, 512, 72], "style": {"font": "Courier", "size": 10, "bold": false, "italic": false, "align": "left", "color": "#212121"}},
  {"id": "section_results_label",   "type": "text",  "content": "MEASUREMENT RESULTS",                   "rect": [50, 619, 250, 14],  "style": {"font": "Helvetica", "size": 9,  "bold": true,  "italic": false, "align": "left",   "color": "#2E7D32"}},
  {"id": "section_results_divider", "type": "shape", "shape_type": "line", "rect": [50, 609, 512, 2],    "color": "#2E7D32", "stroke_width": 0.75, "fill": false},
  {"id": "results_table_bg",        "type": "shape", "shape_type": "rect", "rect": [50, 537, 512, 62],   "color": "#E8F5E9", "stroke_width": 0,    "fill": true},
  {"id": "results_table_border",    "type": "shape", "shape_type": "rect", "rect": [50, 537, 512, 62],   "color": "#A5D6A7", "stroke_width": 0.75, "fill": false},
  {"id": "results_data",            "type": "text",  "content": "Tray + sample before drying:          {{tray_sam}} g\nTray + sample after control drying:   {{tray_ctrl}} g\nMoisture loss:                        {{sample_error}} g\n\nMoisture content  =  {{moisture_pct}} %", "rect": [58, 535, 496, 56], "style": {"font": "Courier", "size": 10, "bold": false, "italic": false, "align": "left", "color": "#1B5E20"}},
  {"id": "section_analysis_label",  "type": "text",  "content": "ANALYSIS SUMMARY",                     "rect": [50, 509, 250, 14],  "style": {"font": "Helvetica", "size": 9,  "bold": true,  "italic": false, "align": "left",   "color": "#2E7D32"}},
  {"id": "section_analysis_divider","type": "shape", "shape_type": "line", "rect": [50, 501, 512, 2],    "color": "#2E7D32", "stroke_width": 0.75, "fill": false},
  {"id": "analysis_body",           "type": "text",  "content": "{{template}}",                          "rect": [50, 210, 512, 280], "style": {"font": "Helvetica", "size": 10, "bold": false, "italic": false, "align": "left",   "color": "#212121"}},
  {"id": "footer_line",             "type": "shape", "shape_type": "line", "rect": [50, 58, 512, 2],     "color": "#BDBDBD", "stroke_width": 0.5,  "fill": false},
  {"id": "footer_text",             "type": "text",  "content": "Confidential — For internal use only.  Ranch 1982 Tomato Analysis Laboratory", "rect": [50, 44, 512, 12], "style": {"font": "Helvetica", "size": 8, "bold": false, "italic": true, "align": "center", "color": "#9E9E9E"}}
]'::jsonb
FROM experiment_templates et
JOIN sample_types st ON et.sample_type_id = st.id
WHERE et.name = 'Tomato Analysis'
  AND st.name = 'Tomato'
ON CONFLICT (template_id) DO UPDATE SET
    components = EXCLUDED.components,
    updated_at = NOW();
