-- Requires experiment_templates row with id='dd949e81-22ea-46b0-aa04-c0c80d22a9a2' to exist first (managed by experiment manager service).

INSERT INTO pdf_templates (exp_tmpl_id, components)
VALUES ('dd949e81-22ea-46b0-aa04-c0c80d22a9a2', '[
  {"id":"header_bg","type":"shape","shape_type":"rect","rect":[0,742,612,50],"color":"#1A237E","stroke_width":0,"fill":true},
  {"id":"header_title","type":"text","content":"GROSS CALORIFIC VALUE REPORT","rect":[24,763,380,22],"style":{"font":"Helvetica","size":16,"bold":true,"italic":false,"align":"left","color":"#FFFFFF"}},
  {"id":"header_sub","type":"text","content":"Bomb Calorimetry  |  {{fuel_type}}  |  Grade {{sample_grade}}","rect":[24,745,350,14],"style":{"font":"Helvetica","size":9,"bold":false,"italic":false,"align":"left","color":"#9FA8DA"}},
  {"id":"header_date","type":"text","content":"{{analysis_date}}","rect":[440,763,148,12],"style":{"font":"Helvetica","size":9,"bold":false,"italic":false,"align":"right","color":"#9FA8DA"}},
  {"id":"header_analyst","type":"text","content":"{{analyst_name}}","rect":[440,748,148,12],"style":{"font":"Helvetica","size":8,"bold":false,"italic":false,"align":"right","color":"#C5CAE9"}},
  {"id":"result_bg","type":"shape","shape_type":"rect","rect":[50,676,512,58],"color":"#FFF8E1","stroke_width":0,"fill":true},
  {"id":"result_border","type":"shape","shape_type":"rect","rect":[50,676,512,58],"color":"#F9A825","stroke_width":1,"fill":false},
  {"id":"result_fuel_label","type":"text","content":"FUEL: {{fuel_type}}","rect":[58,727,300,12],"style":{"font":"Helvetica","size":9,"bold":true,"italic":false,"align":"left","color":"#37474F"}},
  {"id":"result_gcv_cal","type":"text","content":"{{gcv_cal_g}} cal/g","rect":[58,699,220,22],"style":{"font":"Helvetica","size":20,"bold":true,"italic":false,"align":"left","color":"#E65100"}},
  {"id":"result_gcv_kj","type":"text","content":"{{gcv_kj_kg}} kJ/kg","rect":[292,703,200,16],"style":{"font":"Helvetica","size":14,"bold":false,"italic":false,"align":"left","color":"#BF360C"}},
  {"id":"result_meta","type":"text","content":"Quality: {{sample_quality}}/5  |  Confidence: {{confidence}}%  |  Validity: {{test_validity}}","rect":[58,682,430,12],"style":{"font":"Helvetica","size":8,"bold":false,"italic":false,"align":"left","color":"#78909C"}},
  {"id":"sec_meas_label","type":"text","content":"COMBUSTION MEASUREMENT INPUTS","rect":[50,660,300,12],"style":{"font":"Helvetica","size":9,"bold":true,"italic":false,"align":"left","color":"#1A237E"}},
  {"id":"sec_meas_line","type":"shape","shape_type":"line","rect":[50,656,512,2],"color":"#1A237E","stroke_width":0.75,"fill":false},
  {"id":"meas_data","type":"text","content":"Sample mass         m  = {{sample_mass}} g\nWater equivalent    W  = {{water_equivalent}} cal/°C\nTemperature rise    ΔT = {{temp_rise}} °C\nFuse correction     f  = {{fuse_correction}} cal          net: {{fuse_corr}} cal","rect":[58,570,496,78],"style":{"font":"Courier","size":10,"bold":false,"italic":false,"align":"left","color":"#212121"}},
  {"id":"sec_qc_label","type":"text","content":"QUALITY ASSURANCE & ANALYST INFO","rect":[50,556,350,12],"style":{"font":"Helvetica","size":9,"bold":true,"italic":false,"align":"left","color":"#1A237E"}},
  {"id":"sec_qc_line","type":"shape","shape_type":"line","rect":[50,552,512,2],"color":"#1A237E","stroke_width":0.75,"fill":false},
  {"id":"qc_bg","type":"shape","shape_type":"rect","rect":[50,450,512,96],"color":"#E8EAF6","stroke_width":0,"fill":true},
  {"id":"qc_data","type":"text","content":"Analyst:      {{analyst_name}}                    Date: {{analysis_date}}\nStarted at:   {{test_started_at}}               Time: {{analysis_time}}\nFuel type:    {{fuel_type}}   |   O2 pressure: {{combustion_pressure}} atm\nValidity:     {{test_validity}}   |   Certified: {{certified}}   |   Grade: {{sample_grade}}\nSample color: {{sample_color}}","rect":[58,538,496,82],"style":{"font":"Courier","size":10,"bold":false,"italic":false,"align":"left","color":"#37474F"}},
  {"id":"sec_sum_label","type":"text","content":"ANALYSIS RESULT","rect":[50,432,300,12],"style":{"font":"Helvetica","size":9,"bold":true,"italic":false,"align":"left","color":"#1A237E"}},
  {"id":"sec_sum_line","type":"shape","shape_type":"line","rect":[50,428,512,2],"color":"#1A237E","stroke_width":0.75,"fill":false},
  {"id":"result_formula","type":"text","content":"{{template}}","rect":[50,402,512,20],"style":{"font":"Helvetica","size":12,"bold":true,"italic":false,"align":"center","color":"#E65100"}},
  {"id":"notes_label","type":"text","content":"ANALYST OBSERVATIONS","rect":[50,382,300,10],"style":{"font":"Helvetica","size":8,"bold":true,"italic":false,"align":"left","color":"#455A64"}},
  {"id":"notes_body","type":"text","content":"{{lab_notes}}","rect":[50,100,512,274],"style":{"font":"Helvetica","size":10,"bold":false,"italic":false,"align":"left","color":"#212121"}},
  {"id":"footer_line","type":"shape","shape_type":"line","rect":[50,58,512,2],"color":"#BDBDBD","stroke_width":0.5,"fill":false},
  {"id":"footer_text","type":"text","content":"GCV Analysis Report  |  Generated: {{analysis_date}}  |  Analyst: {{analyst_name}}","rect":[50,44,512,12],"style":{"font":"Helvetica","size":8,"bold":false,"italic":true,"align":"center","color":"#9E9E9E"}}
]'::jsonb)
ON CONFLICT (exp_tmpl_id) DO UPDATE SET
    components = EXCLUDED.components,
    updated_at = NOW();
