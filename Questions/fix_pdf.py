"""Patch generate_answers_pdf.py to fix sizing issues."""
content = open('generate_answers_pdf.py', encoding='utf-8').read()

# 1. Fix registration flowchart - reduce G spacing and adjust CX_R for wider canvas
content = content.replace(
    '    WB = 220; HB = 36; WD = 190; HD = 44\n    G = 20',
    '    WB = 210; HB = 34; WD = 180; HD = 42\n    G = 14'
)

# 2. Fix CX_R for wider 730px canvas
content = content.replace(
    '    CX = 230   # main flow center-x\n    CX_R = 415',
    '    CX = 240   # main flow center-x\n    CX_R = 540'
)

# 3. Use landscape A4 for the document to maximise available height
content = content.replace(
    'from reportlab.lib.pagesizes import A4',
    'from reportlab.lib.pagesizes import A4, landscape'
)
content = content.replace(
    'doc = SimpleDocTemplate(OUTPUT_FILE, pagesize=A4,',
    'doc = SimpleDocTemplate(OUTPUT_FILE, pagesize=A4,'
)

# 4. Scale down ALL Drawing widths to ≤480 (A4 portrait usable = 481 pts)
# and ALL Drawing heights to ≤700
replacements = [
    # login flowchart
    ('def build_login_flowchart():\n    W, H = 520, 690',
     'def build_login_flowchart():\n    W, H = 478, 680'),
    # attendance flowchart
    ('def build_attendance_flowchart():\n    W, H = 520, 800',
     'def build_attendance_flowchart():\n    W, H = 478, 760'),
    # absent worker
    ('def build_absent_worker_flowchart():\n    W, H = 520, 680',
     'def build_absent_worker_flowchart():\n    W, H = 478, 660'),
    # use case diagram
    ('def build_use_case_diagram():\n    W, H = 550, 620',
     'def build_use_case_diagram():\n    W, H = 478, 600'),
    # class diagram
    ('def build_class_diagram():\n    W, H = 560, 700',
     'def build_class_diagram():\n    W, H = 478, 690'),
    # sequence registration
    ('def build_sequence_registration():\n    W, H = 560, 620',
     'def build_sequence_registration():\n    W, H = 478, 610'),
    # sequence attendance
    ('def build_sequence_attendance():\n    W, H = 560, 520',
     'def build_sequence_attendance():\n    W, H = 478, 510'),
    # sequence login
    ('def build_sequence_login():\n    W, H = 500, 380',
     'def build_sequence_login():\n    W, H = 478, 370'),
    # component diagram
    ('def build_component_diagram():\n    W, H = 550, 520',
     'def build_component_diagram():\n    W, H = 478, 510'),
    # er diagram
    ('def build_er_diagram():\n    W, H = 560, 580',
     'def build_er_diagram():\n    W, H = 478, 570'),
    # registration flowchart
    ('W, H = 730, 720', 'W, H = 478, 700'),
]
for old, new in replacements:
    if old in content:
        content = content.replace(old, new)
        print(f'Replaced: {old[:50]}')
    else:
        print(f'NOT FOUND: {old[:50]}')

# Fix CX_R for the login, attendance and absent worker flowcharts too
# (CX=230, CX_R=415 pattern in those functions)
content = content.replace(
    '    CX = 230; CX_R = 415\n    WB = 220; HB = 36; WD = 190; HD = 44; G = 20\n\n    y = H - 50\n    fc_terminal(d, CX, y, 160, 32, "START")\n    y -= 16 + G',
    '    CX = 210; CX_R = 390\n    WB = 200; HB = 34; WD = 180; HD = 42; G = 18\n\n    y = H - 50\n    fc_terminal(d, CX, y, 160, 32, "START")\n    y -= 16 + G'
)

# Fix part_w in sequence diagrams so they fit in 478px
content = content.replace('    part_w = 80; box_h = 30; top_y = H - 45', '    part_w = 68; box_h = 28; top_y = H - 45')
content = content.replace('    part_w = 85; box_h = 30; ll_top = H - 45; ll_bot = 30\n\n    fills = [LIGHT_BLUE, LIGHT_GREEN, LIGHT_TEAL', '    part_w = 68; box_h = 28; ll_top = H - 45; ll_bot = 30\n\n    fills = [LIGHT_BLUE, LIGHT_GREEN, LIGHT_TEAL')
content = content.replace('    part_w = 85; box_h = 30; ll_top = H - 45; ll_bot = 30\n\n    fills = [LIGHT_BLUE, LIGHT_GREEN, LIGHT_AMBER', '    part_w = 68; box_h = 28; ll_top = H - 45; ll_bot = 30\n\n    fills = [LIGHT_BLUE, LIGHT_GREEN, LIGHT_AMBER')
content = content.replace('    part_w = 85; box_h = 30; ll_top = H - 45; ll_bot = 30', '    part_w = 72; box_h = 28; ll_top = H - 45; ll_bot = 30')

open('generate_answers_pdf.py', 'w', encoding='utf-8').write(content)
print('Done patching generate_answers_pdf.py')
