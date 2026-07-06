# -*- coding: utf-8 -*-
"""
Smart Attendance System Using Face Recognition
Complete Project Q&A PDF — All Flowcharts + UML Diagrams
FIXED for A4 page size (493 x 739 pt usable area)
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle, Flowable,
)
from reportlab.graphics.shapes import (
    Drawing, Rect, Ellipse, Line, String, Polygon, Circle,
)

OUTPUT_FILE = "Smart_Attendance_Project_Answers.pdf"

# ─── A4 safe drawing dimensions ──────────────────────────────────────────────
# A4 usable: 493 x 739 pt  (with 18mm margins)
# Budget per diagram page: heading~28 + desc~35 + sp~8 + caption~18 = 89 pt overhead
# Safe Drawing target width : 488 pt
# Safe Drawing target max-h : 739 - 89 = 650 pt  → use 640 to be safe
SAFE_W = 488       # target display width  (fits in 493 usable)
SAFE_H = 640       # target display max height

# ─── Colours ─────────────────────────────────────────────────────────────────
TEAL        = colors.HexColor("#00d1c7")
DARK_TEAL   = colors.HexColor("#007a74")
DARK_BG     = colors.HexColor("#0f172a")
SLATE       = colors.HexColor("#475569")
LIGHT_GREY  = colors.HexColor("#f1f5f9")
MID_GREY    = colors.HexColor("#94a3b8")
WHITE       = colors.white
BLACK       = colors.HexColor("#1e293b")
RED         = colors.HexColor("#dc2626")
GREEN       = colors.HexColor("#16a34a")
AMBER       = colors.HexColor("#d97706")
BLUE        = colors.HexColor("#1d4ed8")
PURPLE      = colors.HexColor("#7c3aed")
LIGHT_BLUE  = colors.HexColor("#dbeafe")
LIGHT_GREEN = colors.HexColor("#dcfce7")
LIGHT_RED   = colors.HexColor("#fee2e2")
LIGHT_AMBER = colors.HexColor("#fef3c7")
LIGHT_TEAL  = colors.HexColor("#ccfbf1")
LIGHT_PURPLE= colors.HexColor("#ede9fe")

# ─── Text styles ─────────────────────────────────────────────────────────────
cover_title  = ParagraphStyle("CT",  fontSize=24, fontName="Helvetica-Bold",
                textColor=TEAL, alignment=1, spaceAfter=8, leading=30)
cover_sub    = ParagraphStyle("CS",  fontSize=12, fontName="Helvetica",
                textColor=SLATE, alignment=1, spaceAfter=4)
cover_meta   = ParagraphStyle("CM",  fontSize=9.5, fontName="Helvetica",
                textColor=MID_GREY, alignment=1, spaceAfter=3)
q_hdr        = ParagraphStyle("QH",  fontSize=13, fontName="Helvetica-Bold",
                textColor=WHITE, backColor=DARK_BG, borderPad=(7,9,7,9),
                spaceAfter=8, spaceBefore=14, leading=18)
diag_hdr     = ParagraphStyle("DH",  fontSize=11, fontName="Helvetica-Bold",
                textColor=WHITE, backColor=DARK_TEAL, borderPad=(5,7,5,7),
                spaceAfter=6, spaceBefore=10, leading=16)
sec_hdr      = ParagraphStyle("SH",  fontSize=10.5, fontName="Helvetica-Bold",
                textColor=TEAL, spaceAfter=4, spaceBefore=7)
body         = ParagraphStyle("BD",  fontSize=9, fontName="Helvetica",
                textColor=BLACK, spaceAfter=4, leading=13)
bullet_s     = ParagraphStyle("BL",  fontSize=9, fontName="Helvetica",
                textColor=BLACK, spaceAfter=3, leading=12, leftIndent=12)
caption_s    = ParagraphStyle("CA",  fontSize=8, fontName="Helvetica-Oblique",
                textColor=SLATE, alignment=1, spaceAfter=3, spaceBefore=2)
tc_s         = ParagraphStyle("TC",  fontSize=7.5, fontName="Helvetica",
                textColor=BLACK, leading=10)
th_s         = ParagraphStyle("TH",  fontSize=7.5, fontName="Helvetica-Bold",
                textColor=TEAL, leading=10)

def hr():    return HRFlowable(width="100%", thickness=1, color=TEAL, spaceAfter=5, spaceBefore=2)
def sp(h=5): return Spacer(1, h)
def qt(n,t,e): e.append(sp(10)); e.append(Paragraph(f"Q{n}. {t}", q_hdr))
def dh(t,e):   e.append(Paragraph(t, diag_hdr))
def p(t,e,s=body): e.append(Paragraph(t, s))
def sec(t,e):  e.append(Paragraph(t, sec_hdr))
def bl(its,e): [e.append(Paragraph(f"\u2022  {i}", bullet_s)) for i in its]
def cap(t,e):  e.append(Paragraph(t, caption_s))

def mk_table(rows, cw):
    def wrap(c, ri):
        return Paragraph(str(c), th_s if ri == 0 else tc_s)
    data = [[wrap(c, ri) for c in row] for ri, row in enumerate(rows)]
    t = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),DARK_BG),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[LIGHT_GREY,WHITE]),
        ("ALIGN",(0,0),(-1,-1),"LEFT"), ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("GRID",(0,0),(-1,-1),0.4,MID_GREY),
        ("TOPPADDING",(0,0),(-1,-1),4), ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LEFTPADDING",(0,0),(-1,-1),5), ("RIGHTPADDING",(0,0),(-1,-1),5),
    ]))
    return t

# ═══════════════════════════════════════════════════════════════════════════════
#  ScaledDrawing — auto-shrink a Drawing to fit SAFE_W x SAFE_H
# ═══════════════════════════════════════════════════════════════════════════════
class ScaledDrawing(Flowable):
    """Wraps a ReportLab Drawing and scales it to fit target_w x max_h."""
    def __init__(self, drawing, target_w=SAFE_W, max_h=SAFE_H):
        super().__init__()
        d = drawing
        sx = target_w / d.width
        sy = max_h / d.height if d.height > max_h else 1.0
        scale = min(sx, sy)
        self.drawing  = d
        self.scale    = scale
        self.width    = d.width  * scale
        self.height   = d.height * scale

    def wrap(self, aw, ah):
        return self.width, self.height

    def draw(self):
        self.canv.saveState()
        self.canv.scale(self.scale, self.scale)
        self.drawing.drawOn(self.canv, 0, 0)
        self.canv.restoreState()

def sd(drawing):
    """Return a ScaledDrawing from a raw Drawing."""
    return ScaledDrawing(drawing)

# ═══════════════════════════════════════════════════════════════════════════════
#  Drawing Primitives
# ═══════════════════════════════════════════════════════════════════════════════
def _wrap(text, max_ch):
    words = text.split()
    lines, cur = [], []
    for w in words:
        test = " ".join(cur + [w])
        if len(test) > max_ch and cur:
            lines.append(" ".join(cur)); cur = [w]
        else:
            cur.append(w)
    if cur: lines.append(" ".join(cur))
    return lines

def _txt(d, cx, cy, text, font="Helvetica", size=8, color=WHITE, max_ch=24, lh=10):
    lines = _wrap(text, max_ch)
    total = (len(lines)-1)*lh
    for i, ln in enumerate(lines):
        d.add(String(cx, cy + total/2 - i*lh - size*0.35,
                     ln, fontName=font, fontSize=size,
                     fillColor=color, textAnchor="middle"))

def _ahddn(d, x, y, dir="down", sz=6, col=BLACK):
    if dir=="down":    pts=[x-sz/2,y+sz, x+sz/2,y+sz, x,y]
    elif dir=="up":    pts=[x-sz/2,y-sz, x+sz/2,y-sz, x,y]
    elif dir=="right": pts=[x-sz,y+sz/2, x-sz,y-sz/2, x,y]
    elif dir=="left":  pts=[x+sz,y+sz/2, x+sz,y-sz/2, x,y]
    d.add(Polygon(pts, fillColor=col, strokeColor=col, strokeWidth=0))

# Flowchart shape helpers
# HB=process height, HD=decision height, HT=terminal height  (all drawn at NATIVE scale)
HT=28; HB=30; HD=38; G=11   # gap between shapes

def fc_start(d, cx, cy, w=180, text="START", fill=DARK_BG):
    rx=HT/2
    d.add(Rect(cx-w/2, cy-HT/2, w, HT, rx=rx, ry=rx,
               fillColor=fill, strokeColor=TEAL, strokeWidth=2))
    _txt(d, cx, cy, text, font="Helvetica-Bold", size=9, color=WHITE, max_ch=30)

def fc_proc(d, cx, cy, w=200, text="", fill=LIGHT_BLUE, tc=BLACK):
    d.add(Rect(cx-w/2, cy-HB/2, w, HB,
               fillColor=fill, strokeColor=BLUE, strokeWidth=1.4))
    _txt(d, cx, cy, text, size=7.5, color=tc, max_ch=32, lh=9)

def fc_io(d, cx, cy, w=200, text="", fill=LIGHT_TEAL, tc=BLACK):
    off=9
    pts=[cx-w/2+off,cy+HB/2, cx+w/2+off,cy+HB/2,
         cx+w/2-off,cy-HB/2, cx-w/2-off,cy-HB/2]
    d.add(Polygon(pts, fillColor=fill, strokeColor=DARK_TEAL, strokeWidth=1.4))
    _txt(d, cx, cy, text, size=7.5, color=tc, max_ch=32, lh=9)

def fc_dec(d, cx, cy, w=180, text="", fill=LIGHT_AMBER, tc=BLACK):
    pts=[cx,cy+HD/2, cx+w/2,cy, cx,cy-HD/2, cx-w/2,cy]
    d.add(Polygon(pts, fillColor=fill, strokeColor=AMBER, strokeWidth=1.5))
    _txt(d, cx, cy, text, size=7.5, color=tc, max_ch=20, lh=9)

def fc_err(d, cx, cy, w=115, h=28, text="", fill=LIGHT_RED, tc=RED):
    d.add(Rect(cx-w/2, cy-h/2, w, h, rx=3, ry=3,
               fillColor=fill, strokeColor=RED, strokeWidth=1.2))
    _txt(d, cx, cy, text, size=7, color=tc, max_ch=20, lh=9)

def v_arr(d, cx, y1, y2, col=BLACK):
    d.add(Line(cx, y1, cx, y2+6, strokeColor=col, strokeWidth=1.4))
    _ahddn(d, cx, y2, "down", 6, col)

def h_arr(d, x1, x2, cy, col=BLACK, label=None, above=True, dash=False):
    kw = dict(strokeColor=col, strokeWidth=1.3)
    if dash: kw["strokeDashArray"] = [4,3]
    d.add(Line(x1, cy, x2-6, cy, **kw))
    _ahddn(d, x2, cy, "right", 6, col)
    if label:
        ly = cy+5 if above else cy-12
        d.add(String((x1+x2)/2, ly, label, fontName="Helvetica", fontSize=6.5,
                     fillColor=SLATE, textAnchor="middle"))

def h_arr_l(d, x1, x2, cy, col=BLACK, label=None, above=True, dash=False):
    kw = dict(strokeColor=col, strokeWidth=1.3)
    if dash: kw["strokeDashArray"] = [4,3]
    d.add(Line(x1, cy, x2+6, cy, **kw))
    _ahddn(d, x2, cy, "left", 6, col)
    if label:
        ly = cy+5 if above else cy-12
        d.add(String((x1+x2)/2, ly, label, fontName="Helvetica", fontSize=6.5,
                     fillColor=SLATE, textAnchor="middle"))

def yes_lbl(d, cx, y):
    d.add(String(cx+5, y-HD/2-11, "YES", fontName="Helvetica-Bold",
                 fontSize=7.5, fillColor=GREEN, textAnchor="start"))

def no_lbl(d, cx, cy, side="right"):
    if side=="right":
        d.add(String(cx+HD/2*0.55+4, cy-3, "NO", fontName="Helvetica-Bold",
                     fontSize=7.5, fillColor=RED, textAnchor="start"))
    else:
        d.add(String(cx-HD/2*0.55-18, cy-3, "NO", fontName="Helvetica-Bold",
                     fontSize=7.5, fillColor=RED, textAnchor="start"))

def legend(d, x, y):
    items = [
        (DARK_BG, TEAL, "Start / End"),
        (LIGHT_BLUE, BLUE, "Process"),
        (LIGHT_TEAL, DARK_TEAL, "Input / Output"),
        (LIGHT_AMBER, AMBER, "Decision"),
        (LIGHT_RED, RED, "Error / Reject"),
    ]
    d.add(String(x, y+2, "LEGEND:", fontName="Helvetica-Bold",
                 fontSize=7.5, fillColor=DARK_BG, textAnchor="start"))
    for i, (fc, sc, lbl) in enumerate(items):
        col = i // 3; row = i % 3
        lx = x + col*130; ly = y - 14 - row*14
        d.add(Rect(lx, ly-2, 12, 9, fillColor=fc, strokeColor=sc, strokeWidth=1))
        d.add(String(lx+15, ly-1, lbl, fontName="Helvetica", fontSize=7.5,
                     fillColor=BLACK, textAnchor="start"))

def diag_title(d, W, H, text):
    d.add(String(W/2, H-18, text, fontName="Helvetica-Bold", fontSize=11,
                 fillColor=DARK_BG, textAnchor="middle"))
    d.add(Line(10, H-24, W-10, H-24, strokeColor=TEAL, strokeWidth=1.5))

def bg(d, W, H, col="#fafafa"):
    d.add(Rect(0,0,W,H, fillColor=colors.HexColor(col),
               strokeColor=MID_GREY, strokeWidth=0.8))

# ═══════════════════════════════════════════════════════════════════════════════
#  FLOWCHART 1A — Registration Part A  (START → Duplicate check)
# ═══════════════════════════════════════════════════════════════════════════════
def fc_reg_a():
    NW, NH = 540, 640
    d = Drawing(NW, NH); bg(d, NW, NH)
    diag_title(d, NW, NH, "FLOWCHART 1A — Student Registration: Steps 1-10")
    CX=220; CX_R=415; DW=185

    y = NH-38
    fc_start(d, CX, y, 160, "START")
    y -= HT/2+G; v_arr(d, CX, y+G-2, y)

    fc_io(d, CX, y, 220, "Student fills Form (Name, Gmail, Roll No, Dept, Password)")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "Gmail address?")
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 115, 26, "HTTP 400: Only @gmail.com allowed")
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "Email already registered?")
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 115, 26, "HTTP 400: Email exists")
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "Roll number already taken?")
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 115, 26, "HTTP 400: Roll No exists")
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    fc_io(d, CX, y, 220, "Browser captures Face Image via WebRTC Webcam (Base64 JPEG)")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_proc(d, CX, y, 220, "face_service.extract_encoding()  →  128-D float vector")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "Exactly 1 face detected?")
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 115, 26, "HTTP 400: No / Multiple faces")
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    fc_proc(d, CX, y, 220, "find_best_match() — compare vs. ALL active student encodings")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "Duplicate face found?")
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 115, 42, "Deactivate existing account\nLog CRITICAL security_log\nHTTP 400 Rejected")
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    # Continuation box
    d.add(Rect(CX-100, y-16, 200, 28, fillColor=colors.HexColor("#e0e7ff"),
               strokeColor=BLUE, strokeWidth=1.5, rx=4))
    d.add(String(CX, y-2, "Continued in Flowchart 1B  ->", fontName="Helvetica-Bold",
                 fontSize=8, fillColor=BLUE, textAnchor="middle"))

    legend(d, 10, 58)
    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  FLOWCHART 1B — Registration Part B  (OTP generation → END)
# ═══════════════════════════════════════════════════════════════════════════════
def fc_reg_b():
    NW, NH = 540, 570
    d = Drawing(NW, NH); bg(d, NW, NH)
    diag_title(d, NW, NH, "FLOWCHART 1B — Student Registration: Steps 11-20 (continued)")
    CX=220; CX_R=415; DW=185

    # Continuation indicator
    y = NH-38
    d.add(Rect(CX-110, y-14, 220, 26, fillColor=colors.HexColor("#e0e7ff"),
               strokeColor=BLUE, strokeWidth=1.5, rx=4))
    d.add(String(CX, y, "<- Continued from Flowchart 1A", fontName="Helvetica-Bold",
                 fontSize=8, fillColor=BLUE, textAnchor="middle"))
    y -= 14+G; v_arr(d, CX, y+G-2, y)

    fc_proc(d, CX, y, 220, "Generate 6-digit OTP → hash with SHA-256 + secret salt")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_proc(d, CX, y, 220, "Insert user doc in MongoDB  (is_verified=False, stores face encoding)")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_io(d, CX, y, 220, "send_otp_email() via Gmail SMTP — HTML OTP email to student")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "Email delivered?")
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 115, 26, "HTTP 503: SMTP failure")
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    fc_io(d, CX, y, 220, "Student enters 6-digit OTP on /otp.html verification page")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "OTP expired (> 10 minutes)?")
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 115, 26, "HTTP 400: Expired — resend OTP")
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "SHA-256 hash of OTP matches?")
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 115, 26, "HTTP 400: Wrong OTP")
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    fc_proc(d, CX, y, 220, "Set is_verified=True, clear otp_hash in MongoDB")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_proc(d, CX, y, 220, "Log EMAIL_VERIFIED event + send_registration_success() email")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_start(d, CX, y-4, 220, "END — Account Active. Redirect to Login Page")

    legend(d, 10, 50)
    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  FLOWCHART 2 — Login
# ═══════════════════════════════════════════════════════════════════════════════
def fc_login():
    NW, NH = 540, 610
    d = Drawing(NW, NH); bg(d, NW, NH)
    diag_title(d, NW, NH, "FLOWCHART 2 — Login / Authentication Process")
    CX=220; CX_R=415; DW=185

    y = NH-38
    fc_start(d, CX, y, 160, "START")
    y -= HT/2+G; v_arr(d, CX, y+G-2, y)

    fc_io(d, CX, y, 220, "User enters Email + Password on /login.html")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "User found by email in MongoDB?")
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 115, 26, "HTTP 401: Invalid credentials")
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "Account active (is_active=True)?")
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 115, 26, "HTTP 403: Account deactivated")
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "bcrypt password hash matches?")
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 115, 26, "HTTP 401: Invalid credentials")
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "Email verified (is_verified=True)?")
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 115, 26, "HTTP 400: Verify email first")
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    fc_proc(d, CX, y, 220, "Create JWT (HS256, sub=email, exp=60 min) via python-jose")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_proc(d, CX, y, 220, "Update last_login_at in MongoDB  →  return {access_token}")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_io(d, CX, y, 220, "Frontend stores JWT in localStorage")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_proc(d, CX, y, 220, "GET /users/me — decode JWT → determine role (student/teacher/admin)")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_start(d, CX, y-4, 220, "END — Redirect to Role Dashboard")

    legend(d, 10, 52)
    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  FLOWCHART 3 — Attendance Marking
# ═══════════════════════════════════════════════════════════════════════════════
def fc_attend():
    NW, NH = 540, 635
    d = Drawing(NW, NH); bg(d, NW, NH)
    diag_title(d, NW, NH, "FLOWCHART 3 — Face-Based Attendance Marking")
    CX=200; CX_R=395; DW=185

    y = NH-38
    fc_start(d, CX, y, 200, "START — Teacher clicks Mark Attendance")
    y -= HT/2+G; v_arr(d, CX, y+G-2, y)

    fc_io(d, CX, y, 220, "Browser captures classroom webcam frame (Base64 JPEG)")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "Geofencing enabled?")
    # YES branch to right — check GPS
    geo_cy = y
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    d.add(String(CX+DW/2+4, y+3, "YES", fontName="Helvetica-Bold", fontSize=7.5, fillColor=AMBER))
    geo_gps_y = y
    fc_proc(d, CX_R, geo_gps_y, 220, "Get GPS via navigator.geolocation", fill=LIGHT_BLUE, tc=BLUE)
    geo_dec_y = y - 30
    d.add(Line(CX_R, geo_gps_y-13, CX_R, geo_dec_y+HD/2, strokeColor=BLACK, strokeWidth=1.4))
    pts=[CX_R, geo_dec_y+HD/2, CX_R+55,geo_dec_y, CX_R,geo_dec_y-HD/2, CX_R-55,geo_dec_y]
    d.add(Polygon(pts, fillColor=LIGHT_AMBER, strokeColor=AMBER, strokeWidth=1.3))
    _txt(d, CX_R, geo_dec_y, "Within campus radius?", size=7, color=BLACK, max_ch=18, lh=8)
    d.add(String(CX_R-60, geo_dec_y-3, "NO", fontName="Helvetica-Bold", fontSize=7, fillColor=RED))
    d.add(Line(CX_R-55, geo_dec_y, CX_R-140, geo_dec_y, strokeColor=BLACK, strokeWidth=1.3))
    d.add(Line(CX_R-140, geo_dec_y, CX_R-140, geo_dec_y-22, strokeColor=BLACK, strokeWidth=1.3))
    d.add(Rect(CX_R-195, geo_dec_y-36, 110, 18, fillColor=LIGHT_RED, strokeColor=RED, strokeWidth=1,rx=3))
    _txt(d, CX_R-140, geo_dec_y-27, "HTTP 400: Outside campus", size=7, color=RED, max_ch=22, lh=8)
    # YES (within campus) joins back
    d.add(Line(CX_R, geo_dec_y-HD/2, CX_R, y-HD/2-G, strokeColor=BLACK, strokeWidth=1.3))
    d.add(Line(CX_R, y-HD/2-G, CX+DW/2, y-HD/2-G, strokeColor=BLACK, strokeWidth=1.3))
    d.add(String(CX_R+4, geo_dec_y-HD/2-8, "YES", fontName="Helvetica-Bold", fontSize=7, fillColor=GREEN))

    # NO (geo disabled) — goes straight down
    d.add(String(CX-DW/2-18, y-3, "NO", fontName="Helvetica-Bold", fontSize=7.5, fillColor=GREEN))
    y -= HD/2+G+20; v_arr(d, CX, y+G-2+20, y)

    fc_proc(d, CX, y, 220, "extract_multiple_encodings(image) — detect all face encodings")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "1+ faces detected in frame?")
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 110, 26, "HTTP 400: No faces detected")
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    fc_proc(d, CX, y, 220, "Fetch all active verified students in teacher's department")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_proc(d, CX, y, 220, "find_matches() — Euclidean distance <= FACE_TOLERANCE (0.5)")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "1+ students matched?")
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 110, 26, "HTTP 404: No matching students")
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "check_in time <= 09:30 IST?")
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 110, 26, "Status = 'Late'", fill=LIGHT_AMBER, tc=AMBER)
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    fc_proc(d, CX, y, 220, "Status = 'Present' — insert attendance record in MongoDB")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_start(d, CX, y-4, 220, "END — Return {count, students[], distance_km}")

    legend(d, 10, 52)
    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  FLOWCHART 4 — Absent Worker
# ═══════════════════════════════════════════════════════════════════════════════
def fc_absent():
    NW, NH = 540, 565
    d = Drawing(NW, NH); bg(d, NW, NH)
    diag_title(d, NW, NH, "FLOWCHART 4 — Absent Notification Background Worker")
    CX=220; CX_R=415; DW=185

    y = NH-38
    fc_start(d, CX, y, 220, "START — FastAPI lifespan asyncio task launched")
    y -= HT/2+G; v_arr(d, CX, y+G-2, y)

    fc_proc(d, CX, y, 220, "Loop: await asyncio.sleep(60 seconds)")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "Absent notifications enabled in admin config?")
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 110, 26, "Skip — back to sleep(60)", fill=LIGHT_AMBER, tc=AMBER)
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW+10, "Current IST time >= absent_notice_hour?")
    d.add(Line(CX+(DW+10)/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 110, 26, "Not yet — back to sleep(60)", fill=LIGHT_AMBER, tc=AMBER)
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    fc_proc(d, CX, y, 220, "Fetch all departments from users collection (distinct values)")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_proc(d, CX, y, 220, "FOR EACH dept: find students with no attendance record today")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_dec(d, CX, y, DW, "Already sent today? (claim_doc status = 'sent')")
    d.add(Line(CX+DW/2, y, CX_R, y, strokeColor=BLACK, strokeWidth=1.4))
    no_lbl(d, CX, y, "right")
    fc_err(d, CX_R, y, 110, 26, "Skip dept (duplicate guard)", fill=LIGHT_AMBER, tc=AMBER)
    yes_lbl(d, CX, y); y -= HD/2+G; v_arr(d, CX, y+G-2, y)

    fc_proc(d, CX, y, 220, "Create/update claim_doc — status = 'processing'")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_io(d, CX, y, 220, "Send HTML absence email to each absent student via SMTP")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_proc(d, CX, y, 220, "Update claim_doc status='sent' + log ABSENT_EMAIL_SENT event")
    y -= HB/2+G; v_arr(d, CX, y+G-2, y)

    fc_start(d, CX, y-4, 220, "Continue → Next department / back to sleep(60)")

    legend(d, 10, 48)
    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  UML 1 — Use Case Diagram
# ═══════════════════════════════════════════════════════════════════════════════
def uml_usecase():
    NW, NH = 580, 640
    d = Drawing(NW, NH)
    d.add(Rect(0,0,NW,NH, fillColor=colors.HexColor("#f0fdfa"), strokeColor=MID_GREY, strokeWidth=0.8))
    diag_title(d, NW, NH, "UML 1 — Use Case Diagram")

    # System boundary
    d.add(Rect(110, 36, 340, 578, fillColor=colors.HexColor("#f8fffd"),
               strokeColor=DARK_TEAL, strokeWidth=2, rx=5, ry=5))
    d.add(String(280, 600, "Smart Attendance System",
                 fontName="Helvetica-Bold", fontSize=9, fillColor=DARK_TEAL, textAnchor="middle"))

    def actor(cx, cy, name):
        r=10
        d.add(Circle(cx, cy+r*2.2, r, fillColor=LIGHT_BLUE, strokeColor=BLUE, strokeWidth=1.3))
        d.add(Line(cx, cy+r*1.3, cx, cy-r*0.5, strokeColor=BLUE, strokeWidth=1.3))
        d.add(Line(cx-r*1.1, cy+r*0.4, cx+r*1.1, cy+r*0.4, strokeColor=BLUE, strokeWidth=1.3))
        d.add(Line(cx, cy-r*0.5, cx-r*0.9, cy-r*1.8, strokeColor=BLUE, strokeWidth=1.3))
        d.add(Line(cx, cy-r*0.5, cx+r*0.9, cy-r*1.8, strokeColor=BLUE, strokeWidth=1.3))
        for i, ln in enumerate(name.split("\n")):
            d.add(String(cx, cy-r*2.2-i*10, ln, fontName="Helvetica-Bold", fontSize=7.5,
                         fillColor=DARK_BG, textAnchor="middle"))

    def uc(cx, cy, rx, ry, text):
        d.add(Ellipse(cx, cy, rx, ry, fillColor=LIGHT_TEAL, strokeColor=DARK_TEAL, strokeWidth=1.3))
        lines = _wrap(text, 16)
        lh=9; tot=(len(lines)-1)*lh
        for i,ln in enumerate(lines):
            d.add(String(cx, cy+tot/2-i*lh-3, ln, fontName="Helvetica", fontSize=7,
                         fillColor=DARK_BG, textAnchor="middle"))

    def ln(ax,ay, bx,by): d.add(Line(ax,ay,bx,by, strokeColor=SLATE, strokeWidth=0.9))

    # Actors
    actor(52,  460, "Student")
    actor(52,  250, "Teacher")
    actor(52,  60,  "Admin")
    actor(524, 360, "Email\nService")
    actor(524, 120, "MongoDB")

    # Use cases
    UCS = {
        "Register (Face+OTP)":       (270,570),
        "Login":                      (185,510),
        "View Dashboard":             (280,510),
        "Change Password":            (375,510),
        "Mark Attendance (Face)":     (200,410),
        "Mark Attendance (Manual)":   (370,410),
        "View Dept Students":         (210,330),
        "Export Reports":             (360,330),
        "Send Absent Notices":        (280,260),
        "Manage Users":               (200,180),
        "Configure Settings":         (365,180),
        "Review Security Logs":       (210,100),
        "Verify OTP":                 (360,100),
    }
    rx,ry = 68,20
    for lbl,(cx,cy) in UCS.items():
        uc(cx,cy,rx,ry,lbl)

    def conn(ax,ay,lbl):
        cx,cy=UCS[lbl]
        ex=cx-rx if ax<cx else cx+rx
        ln(ax+10, ay+46, ex, cy)

    for l in ["Register (Face+OTP)","Login","View Dashboard","Change Password"]:
        conn(52,400,l)
    for l in ["Mark Attendance (Face)","Mark Attendance (Manual)","View Dept Students","Export Reports","Send Absent Notices"]:
        conn(52,190,l)
    for l in ["Manage Users","Configure Settings","Review Security Logs"]:
        conn(52,0,l)
    for l in ["Verify OTP","Send Absent Notices","Register (Face+OTP)"]:
        cx,cy=UCS[l]; ln(512,360,cx+rx,cy)
    ln(512,120, 450, 300)

    # Note
    d.add(Rect(8,6,240,26, fillColor=LIGHT_AMBER, strokeColor=AMBER, strokeWidth=0.8, rx=3))
    d.add(String(12,22,"All actors communicate via REST API (HTTP/JWT)",
                 fontName="Helvetica",fontSize=7.5,fillColor=BLACK))
    d.add(String(12,10,"hosted by FastAPI + Uvicorn on port 8000.",
                 fontName="Helvetica",fontSize=7.5,fillColor=BLACK))
    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  UML 2 — Class Diagram
# ═══════════════════════════════════════════════════════════════════════════════
def uml_class():
    NW, NH = 580, 680
    d = Drawing(NW, NH)
    d.add(Rect(0,0,NW,NH, fillColor=colors.HexColor("#f0f4ff"), strokeColor=MID_GREY, strokeWidth=0.8))
    diag_title(d, NW, NH, "UML 2 — Class Diagram (Core Classes)")

    def cls(x, y, w, name, attrs, methods, fc=LIGHT_BLUE, hc=BLUE):
        rh=10; hh=20; ah=max(len(attrs),1)*rh+6; mh=max(len(methods),1)*rh+6
        tot=hh+ah+mh
        d.add(Rect(x,y-hh, w,hh, fillColor=hc, strokeColor=DARK_BG, strokeWidth=1.1))
        d.add(String(x+w/2, y-hh/2-3.5, name, fontName="Helvetica-Bold", fontSize=8,
                     fillColor=WHITE, textAnchor="middle"))
        d.add(Rect(x,y-hh-ah, w,ah, fillColor=fc, strokeColor=DARK_BG, strokeWidth=1.1))
        for i,a in enumerate(attrs):
            d.add(String(x+4, y-hh-5-i*rh-7, a, fontName="Helvetica", fontSize=7,
                         fillColor=DARK_BG, textAnchor="start"))
        d.add(Rect(x,y-tot, w,mh, fillColor=colors.HexColor("#eff6ff"),
                   strokeColor=DARK_BG, strokeWidth=1.1))
        for i,m in enumerate(methods):
            d.add(String(x+4, y-hh-ah-5-i*rh-7, m, fontName="Helvetica-Oblique", fontSize=7,
                         fillColor=DARK_BG, textAnchor="start"))
        return tot

    def assoc(x1,y1,x2,y2,lbl="",c1="",c2="",dash=False):
        sw=[4,3] if dash else None
        kw=dict(strokeColor=SLATE,strokeWidth=1)
        if sw: kw["strokeDashArray"]=sw
        d.add(Line(x1,y1,x2,y2,**kw))
        if lbl:
            mx,my=(x1+x2)/2,(y1+y2)/2
            d.add(String(mx+3,my+3,lbl,fontName="Helvetica",fontSize=6.5,fillColor=SLATE))
        if c1: d.add(String(x1+3,y1+3,c1,fontName="Helvetica-Bold",fontSize=7,fillColor=BLUE))
        if c2: d.add(String(x2-16,y2+3,c2,fontName="Helvetica-Bold",fontSize=7,fillColor=RED))

    # User
    uh=cls(8,NH-36,155,"User (MongoDB doc)",
         ["+ id:int  + full_name:str","+ email:str (UNIQUE)","+ roll_number:str (UNIQUE)",
          "+ hashed_password:str","+ role:{student|teacher|admin}","+ department:str",
          "+ is_active:bool  is_verified:bool","+ face_encoding:float[128]","+ otp_hash:str",
          "+ preferences:dict","+ last_login_at:str"],
         ["+ get_by_email()","+ get_by_id()"],
         LIGHT_BLUE,BLUE)

    # Attendance
    ah_=cls(172,NH-36,150,"Attendance (MongoDB doc)",
         ["+ id:int","+ user_id:int (FK→users.id)","+ date:str (YYYY-MM-DD)",
          "+ check_in:str (HH:MM:SS)","+ status:{Present|Late|Absent}",
          "+ method:{face|manual|System}","+ marked_by_user_id:int",
          "+ latitude:float  longitude:float","+ created_at:str"],
         ["+ mark_by_face()","+ mark_manual()","+ get_history()"],
         LIGHT_GREEN,GREEN)

    # SecurityLog
    cls(330,NH-36,148,"SecurityLog (MongoDB doc)",
         ["+ id:int","+ event_type:str","+ severity:str",
          "+ details:str","+ metadata:dict","+ user_id:int (FK→users.id)",
          "+ target_user_id:int","+ ip_address:str","+ created_at:str"],
         ["+ log_event()"],
         LIGHT_RED,RED)

    # FaceService
    cls(8,NH-36-uh-28,155,"FaceService",
         ["- face_tolerance:float","- FACE_AVAILABLE:bool"],
         ["+ extract_encoding(img)","+ extract_multiple_encodings(img)",
          "+ find_best_match(cand,users)","+ find_matches(cands,users)","+ compare(a,b):float"],
         LIGHT_PURPLE,PURPLE)

    # AttendanceService
    cls(172,NH-36-ah_-28,150,"AttendanceService",
         ["- settings:Settings"],
         ["+ get_student_stats()","+ mark_by_face()","+ mark_manual()",
          "+ send_absent_notifications()","+ get_report_rows()","+ get_teacher_stats()"],
         LIGHT_GREEN,GREEN)

    # UserService
    cls(330,NH-36-ah_-28,148,"UserService",
         ["- settings:Settings"],
         ["+ create_student_user()","+ create_teacher_user()","+ verify_login()",
          "+ update_password()","+ admin_update_user()","+ delete_user()"],
         LIGHT_AMBER,AMBER)

    # EmailService
    cls(8,NH-36-uh-28-130,155,"EmailService",
         ["- _LAST_MAIL_ERROR:str"],
         ["+ send_otp_email()","+ send_absent_notice()",
          "+ send_registration_success()","+ send_password_changed()"],
         LIGHT_TEAL,DARK_TEAL)

    # Settings
    cls(330,130,148,"Settings (config)",
         ["+ secret_key:str","+ mongodb_uri:str","+ face_tolerance:float",
          "+ campus_lat/lon:float","+ max_distance_km:float",
          "+ absent_notice_hour:int","+ late_hour:int"],
         [],LIGHT_GREY,SLATE)

    # Associations
    assoc(163,NH-36-65, 172,NH-36-65, "records","1","*")
    assoc(163,NH-36-150, 330,NH-36-100, "logs","1","*")
    assoc(172,NH-36-ah_-60, 163,NH-36-60-130, "uses","","",dash=True)
    assoc(330+74,NH-36-ah_-80, 330+74,135, "reads","","",dash=True)

    d.add(String(190,10,"Solid=Association  Dashed=Dependency",
                 fontName="Helvetica-Oblique",fontSize=7.5,fillColor=SLATE,textAnchor="middle"))
    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  UML 3–5 — Sequence Diagrams
# ═══════════════════════════════════════════════════════════════════════════════
def _seq_frame(title, parts, part_fills, part_hdrs, msgs, NW, NH):
    d = Drawing(NW, NH)
    d.add(Rect(0,0,NW,NH, fillColor=colors.HexColor("#f8faff"), strokeColor=MID_GREY, strokeWidth=0.8))
    diag_title(d, NW, NH, title)

    n = len(parts)
    pw = 70; bh = 26
    # distribute evenly
    margin = 30
    step = (NW - 2*margin) / (n-1) if n>1 else NW/2
    pxs = [int(margin + i*step) for i in range(n)]
    ll_top = NH - 44; ll_bot = 48

    for i,(nm,px) in enumerate(zip(parts, pxs)):
        fill = part_fills[i]; hdr = part_hdrs[i]
        d.add(Rect(px-pw/2, ll_top, pw, bh, fillColor=fill, strokeColor=hdr,
                   strokeWidth=1.3, rx=3, ry=3))
        lns = nm.split("\n")
        for li,ln_ in enumerate(lns):
            yo = ll_top + bh/2 + (0.5-li)*8
            d.add(String(px, yo, ln_, fontName="Helvetica-Bold", fontSize=6.5,
                         fillColor=DARK_BG, textAnchor="middle"))
        d.add(Line(px, ll_top, px, ll_bot, strokeColor=SLATE, strokeWidth=1,
                   strokeDashArray=[4,3]))

    for frm,to,ym,label,ret,col in msgs:
        x1=pxs[frm]; x2=pxs[to]
        if x1 < x2:
            h_arr(d, x1, x2, ym, col, label, above=True, dash=ret)
        else:
            h_arr_l(d, x1, x2, ym, col, label, above=True, dash=ret)

    # legend note
    d.add(Rect(5,5,280,18, fillColor=LIGHT_AMBER, strokeColor=AMBER, strokeWidth=0.6, rx=2))
    d.add(String(9,11,"Solid arrow = call   Dashed arrow = return/response",
                 fontName="Helvetica-Oblique",fontSize=7,fillColor=BLACK))
    return d

def uml_seq_reg():
    NW,NH=580,620
    parts=["Browser\n(Student)","auth.py\n(Route)","face_service","user_service","email_service","MongoDB"]
    fills=[LIGHT_BLUE,LIGHT_GREEN,LIGHT_PURPLE,LIGHT_AMBER,LIGHT_TEAL,LIGHT_RED]
    hdrs =[BLUE,GREEN,PURPLE,AMBER,DARK_TEAL,RED]
    t=NH-70
    msgs=[
        (0,1,t-0,  "POST /register (email, password, face_image, dept)",False,DARK_BG),
        (1,2,t-22, "extract_encoding(face_image)",                       False,PURPLE),
        (2,1,t-36, "128-D embedding / HTTP 400",                         True, PURPLE),
        (1,2,t-52, "find_best_match(enc, all_students)",                  False,PURPLE),
        (2,1,t-66, "None / HTTP 400 (duplicate)",                         True, PURPLE),
        (1,3,t-84, "create_student_user(payload, encoding, otp)",         False,AMBER),
        (3,5,t-98, "users.insert_one(doc)",                               False,RED),
        (5,3,t-112,"inserted_id",                                          True, RED),
        (3,1,t-126,"user doc",                                             True, AMBER),
        (1,4,t-146,"send_otp_email(email, otp)",                          False,DARK_TEAL),
        (4,1,t-160,"True / False (SMTP error)",                            True, DARK_TEAL),
        (1,5,t-178,"security_logs.insert(STUDENT_REGISTERED)",             False,RED),
        (1,0,t-198,"200 OK: verification email sent",                      True, DARK_BG),
        (0,1,t-220,"POST /verify-otp (email, otp)",                        False,DARK_BG),
        (1,3,t-238,"mark_verified(db, user)",                              False,AMBER),
        (3,5,t-252,"users.update(is_verified=True, clear otp)",             False,RED),
        (5,3,t-266,"ack",                                                   True, RED),
        (1,4,t-284,"send_registration_success(email)",                      False,DARK_TEAL),
        (1,5,t-298,"security_logs.insert(EMAIL_VERIFIED)",                  False,RED),
        (1,0,t-318,"200 OK: verification successful",                        True, DARK_BG),
    ]
    return _seq_frame("UML 3 — Sequence: Student Registration",parts,fills,hdrs,msgs,NW,NH)

def uml_seq_attend():
    NW,NH=580,530
    parts=["Browser\n(Teacher)","teacher.py\n(Route)","attendance\n_service","face_service","geo_utils","MongoDB"]
    fills=[LIGHT_BLUE,LIGHT_GREEN,LIGHT_TEAL,LIGHT_PURPLE,LIGHT_AMBER,LIGHT_RED]
    hdrs =[BLUE,GREEN,DARK_TEAL,PURPLE,AMBER,RED]
    t=NH-70
    msgs=[
        (0,1,t-0,  "POST /teacher/mark-attendance (image, lat, lon)",     False,DARK_BG),
        (1,2,t-20, "mark_attendance_by_face(db, teacher, image, lat, lon)",False,DARK_TEAL),
        (2,4,t-40, "is_within_radius(lat, lon, campus_lat, campus_lon)",   False,AMBER),
        (4,2,t-54, "True / False + distance_km",                           True, AMBER),
        (2,3,t-72, "extract_multiple_encodings(image)",                    False,PURPLE),
        (3,2,t-86, "list of 128-D face encodings",                         True, PURPLE),
        (2,5,t-106,"users.find(role=student, dept=teacher_dept, active)",   False,RED),
        (5,2,t-120,"active dept students with face_encodings",              True, RED),
        (2,3,t-140,"find_matches(candidates, students)",                    False,PURPLE),
        (3,2,t-154,"matched [{user, distance}] within tolerance",           True, PURPLE),
        (2,5,t-174,"_insert_or_update_attendance() per matched student",    False,RED),
        (5,2,t-188,"attendance record (or existing if duplicate)",          True, RED),
        (2,1,t-208,"{message, marked_count, students[], distance_km}",      True, DARK_TEAL),
        (1,0,t-228,"200 OK: JSON attendance results",                        True, DARK_BG),
    ]
    return _seq_frame("UML 4 — Sequence: Attendance Marking (Face)",parts,fills,hdrs,msgs,NW,NH)

def uml_seq_login():
    NW,NH=540,370
    parts=["Browser","auth.py\n(Route)","user_service","security\n(utils)","MongoDB"]
    fills=[LIGHT_BLUE,LIGHT_GREEN,LIGHT_AMBER,LIGHT_TEAL,LIGHT_RED]
    hdrs =[BLUE,GREEN,AMBER,DARK_TEAL,RED]
    t=NH-70
    msgs=[
        (0,1,t-0,  "POST /login (email, password)",                      False,DARK_BG),
        (1,2,t-20, "get_user_by_email(db, email)",                        False,AMBER),
        (2,4,t-38, "users.find_one({email})",                             False,RED),
        (4,2,t-52, "user doc or None",                                    True, RED),
        (2,1,t-70, "user doc",                                            True, AMBER),
        (1,3,t-90, "verify_password(plain, hashed)",                      False,DARK_TEAL),
        (3,1,t-104,"True / False",                                         True, DARK_TEAL),
        (1,3,t-122,"create_access_token({sub: email})",                    False,DARK_TEAL),
        (3,1,t-136,"signed JWT (HS256)",                                   True, DARK_TEAL),
        (1,4,t-156,"users.update_one(last_login_at=now)",                  False,RED),
        (4,1,t-170,"ack",                                                  True, RED),
        (1,0,t-190,"200 OK: {access_token, token_type: bearer}",           True, DARK_BG),
        (0,1,t-210,"GET /users/me  (Authorization: Bearer <token>)",       False,DARK_BG),
        (1,0,t-228,"200 OK: UserOut {id, role, dept, ...}",                 True, DARK_BG),
        (0,1,t-246,"Redirect to /student|teacher|admin dashboard",          False,DARK_BG),
    ]
    return _seq_frame("UML 5 — Sequence: User Login",parts,fills,hdrs,msgs,NW,NH)

# ═══════════════════════════════════════════════════════════════════════════════
#  UML 6 — Component Diagram
# ═══════════════════════════════════════════════════════════════════════════════
def uml_component():
    NW,NH=580,530
    d=Drawing(NW,NH)
    d.add(Rect(0,0,NW,NH, fillColor=colors.HexColor("#f0fdf4"), strokeColor=MID_GREY, strokeWidth=0.8))
    diag_title(d,NW,NH,"UML 6 — Component Diagram")

    def comp(x,y,w,h,name,sub="",fc=LIGHT_BLUE,hc=BLUE):
        d.add(Rect(x,y,w,h, fillColor=fc, strokeColor=hc, strokeWidth=1.5, rx=4,ry=4))
        nx=x+w-18; ny=y+h-14
        d.add(Rect(nx,ny,16,12, fillColor=WHITE, strokeColor=hc, strokeWidth=1))
        d.add(Rect(nx-4,ny+3,8,3, fillColor=hc, strokeColor=hc))
        d.add(Rect(nx-4,ny+8,8,3, fillColor=hc, strokeColor=hc))
        d.add(String(x+w/2-8, y+h/2+4, name, fontName="Helvetica-Bold", fontSize=8.5,
                     fillColor=DARK_BG, textAnchor="middle"))
        if sub:
            d.add(String(x+w/2-8, y+h/2-8, sub, fontName="Helvetica", fontSize=7,
                         fillColor=SLATE, textAnchor="middle"))

    def conn(x1,y1,x2,y2,label="",col=DARK_BG,dash=False):
        kw=dict(strokeColor=col,strokeWidth=1.5)
        if dash: kw["strokeDashArray"]=[4,3]
        d.add(Line(x1,y1,x2,y2,**kw))
        if label:
            mx,my=(x1+x2)/2,(y1+y2)/2
            d.add(String(mx+3,my+3,label,fontName="Helvetica",fontSize=7,fillColor=col))

    # Components
    comp(10,  390, 130, 100, "Browser",         "HTML/CSS/JS\nWebRTC+Geoloc",   LIGHT_BLUE,  BLUE)
    comp(185, 340, 190, 150, "FastAPI App",      "main.py+Routes\nUvicorn :8000", LIGHT_TEAL, DARK_TEAL)
    comp(185, 210, 190,  70, "Static File Mount","→ /static/frontend/",           LIGHT_GREY, SLATE)
    comp(420, 340, 130,  90, "MongoDB",          "Motor async\nAll collections",   LIGHT_GREEN, GREEN)
    comp(420, 205, 130,  85, "Gmail SMTP",       "smtplib\nPort 587 STARTTLS",     LIGHT_AMBER, AMBER)
    comp(185,  80, 190,  80, "face_recognition\nLibrary","dlib HOG\nResNet-34 encoder",LIGHT_PURPLE,PURPLE)
    comp(420,  80, 130,  70, "WebSocket\nManager","ws_manager\n/ws endpoint",      LIGHT_RED, RED)

    # Connections
    conn(140,440, 185,440, "HTTP REST", DARK_BG)
    conn(140,420, 420, 115, "WS /ws", RED, dash=True)
    conn(140,460, 185,255, "GET /static/", SLATE, dash=True)
    conn(375,415, 420,390, "Motor\nasync", GREEN)
    conn(375,370, 420,255, "smtplib", AMBER)
    conn(280,340, 280,160, "Python import", PURPLE)
    conn(375,360, 420,120, "broadcast()", RED)

    d.add(Rect(5,5,260,22, fillColor=LIGHT_AMBER, strokeColor=AMBER, strokeWidth=0.6, rx=2))
    d.add(String(9,16,"All components run in a single server process (monolith).",
                 fontName="Helvetica-Oblique",fontSize=7.5,fillColor=BLACK))
    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  UML 7 — ER Diagram
# ═══════════════════════════════════════════════════════════════════════════════
def uml_er():
    NW,NH=580,600
    d=Drawing(NW,NH)
    d.add(Rect(0,0,NW,NH, fillColor=colors.HexColor("#fffbf0"), strokeColor=MID_GREY, strokeWidth=0.8))
    diag_title(d,NW,NH,"UML 7 — Entity-Relationship (ER) Diagram")

    def ent(cx,cy,w,name,attrs,fc=LIGHT_BLUE,hc=BLUE):
        rh=11; hh=20; bh=len(attrs)*rh+6; tot=hh+bh
        top=cy+tot/2
        d.add(Rect(cx-w/2,top-hh, w,hh, fillColor=hc, strokeColor=DARK_BG, strokeWidth=1.3))
        d.add(String(cx, top-hh/2-3.5, name, fontName="Helvetica-Bold", fontSize=8.5,
                     fillColor=WHITE, textAnchor="middle"))
        d.add(Rect(cx-w/2,top-tot, w,bh, fillColor=fc, strokeColor=DARK_BG, strokeWidth=1.3))
        for i,a in enumerate(attrs):
            d.add(String(cx-w/2+5, top-hh-5-i*rh-8, a, fontName="Helvetica", fontSize=7,
                         fillColor=DARK_BG, textAnchor="start"))
        return top, top-tot

    def rel(x1,y1,x2,y2,c1,c2,label=""):
        d.add(Line(x1,y1,x2,y2, strokeColor=DARK_BG, strokeWidth=1.3))
        if label:
            mx,my=(x1+x2)/2,(y1+y2)/2
            d.add(Rect(mx-24,my-7,48,14, fillColor=LIGHT_AMBER, strokeColor=AMBER,
                       strokeWidth=0.8,rx=3))
            d.add(String(mx,my+2,label,fontName="Helvetica-Bold",fontSize=7,
                         fillColor=DARK_BG,textAnchor="middle"))
        d.add(String(x1+3,y1+3,c1,fontName="Helvetica-Bold",fontSize=8,fillColor=BLUE))
        d.add(String(x2-14,y2+3,c2,fontName="Helvetica-Bold",fontSize=8,fillColor=RED))

    # users
    u_top,u_bot=ent(100,430,168,"users",
        ["+ id:int (PK, auto-increment)","+ full_name:str","+ email:str (UNIQUE)",
         "+ roll_number:str (UNIQUE)","+ hashed_password:str","+ role:{student|teacher|admin}",
         "+ department:str","+ is_active:bool  is_verified:bool","+ face_encoding:float[128]",
         "+ otp_hash:str  preferences:dict","+ last_login_at:str  created_at:str"],
        LIGHT_BLUE,BLUE)

    # attendance
    a_top,a_bot=ent(300,390,165,"attendance",
        ["+ id:int (PK)","+ user_id:int (FK→users.id)","+ date:str (YYYY-MM-DD)",
         "+ check_in:str (HH:MM:SS)","+ status:{Present|Late|Absent}",
         "+ method:{face|manual|System}","+ marked_by_user_id:int",
         "+ latitude:float  longitude:float","+ created_at:str  updated_at:str"],
        LIGHT_GREEN,GREEN)

    # security_logs
    s_top,s_bot=ent(100,190,168,"security_logs",
        ["+ id:int (PK)","+ event_type:str","+ severity:{info|warn|critical}",
         "+ details:str  metadata:dict","+ user_id:int (FK→users.id)",
         "+ target_user_id:int  ip_address:str","+ created_at:str"],
        LIGHT_RED,RED)

    # counters
    c_top,c_bot=ent(490,500,120,"counters",
        ["+ _id:str (PK)","  'users'|'attendance'","  'security_logs'","+ seq:int (auto-inc)"],
        LIGHT_PURPLE,PURPLE)

    # config
    cf_top,cf_bot=ent(490,250,120,"config",
        ["+ _id:'global' (PK)","+ face_tolerance:float","+ campus_lat/lon:float",
         "+ max_distance_km:float","+ late_hour:int","+ absent_notice_hour:int",
         "+ geofencing_enabled:bool"],
        LIGHT_AMBER,AMBER)

    # absent_notification_claims
    ac_top,ac_bot=ent(300,150,165,"absent_notif_claims",
        ["+ id:int (PK)","+ date:str (YYYY-MM-DD)","+ department:str",
         "+ status:{processing|sent|failed}","+ count:int","+ sent_student_ids:list[int]",
         "+ created_at:str"],
        LIGHT_TEAL,DARK_TEAL)

    # Relationships
    rel(100+84, 345, 300-82, 345, "1","*","records")
    rel(100, s_top-10, 100, u_bot+5, "1","*","logs")
    rel(300-82, 330, 100+84, 250, "1","*","marks")
    rel(430, 490, 300+82, 175, "","","provides IDs")
    rel(430, 265, 100+84, 400, "","","configures")

    d.add(Rect(4,4,290,28, fillColor=LIGHT_AMBER, strokeColor=AMBER, strokeWidth=0.6, rx=2))
    d.add(String(8,22,"UNIQUE indexes: users(email), users(roll_number),",
                 fontName="Helvetica",fontSize=7.5,fillColor=BLACK))
    d.add(String(8,10,"attendance(user_id+date),  absent_claims(date+department)",
                 fontName="Helvetica",fontSize=7.5,fillColor=BLACK))
    return d

# ═══════════════════════════════════════════════════════════════════════════════
#  PDF ASSEMBLY
# ═══════════════════════════════════════════════════════════════════════════════
doc = SimpleDocTemplate(OUTPUT_FILE, pagesize=A4,
    rightMargin=18*mm, leftMargin=18*mm,
    topMargin=18*mm,  bottomMargin=18*mm)
el = []

# ── Cover ─────────────────────────────────────────────────────────────────────
el.append(sp(32))
el.append(Paragraph("Smart Attendance System", cover_title))
el.append(Paragraph("Using Face Recognition", cover_title))
el.append(sp(8)); el.append(hr()); el.append(sp(5))
el.append(Paragraph("Project Viva / Review — Complete Q&A + All Diagrams", cover_sub))
el.append(sp(3))
el.append(Paragraph("FastAPI  ·  MongoDB  ·  face_recognition  ·  Vanilla JS / HTML / CSS", cover_meta))
el.append(Paragraph("April 2026", cover_meta))
el.append(sp(22))

toc=[
    ["#","Section"],
    ["Q1","What is your project and why you chose it?"],
    ["Q2","How to implement your project?"],
    ["Q3","What is the Existing System?"],
    ["Q4","Proposed Methods and why?"],
    ["Q5","Data Sets / Sample Inputs and why?"],
    ["Q6","Hardware & Software Requirements — enough?"],
    ["Q7","Why the specific language — advantages?"],
    ["Q8","Testing Methods — enough? Need for testing?"],
    ["Q9","UML Models used and why?"],
    ["Q10","Conclusion and Future Enhancements"],
    ["FC-1A","Flowchart — Student Registration (Part A: Steps 1-10)"],
    ["FC-1B","Flowchart — Student Registration (Part B: Steps 11-20)"],
    ["FC-2","Flowchart — Login / Authentication"],
    ["FC-3","Flowchart — Face-Based Attendance Marking"],
    ["FC-4","Flowchart — Absent Notification Worker"],
    ["UC","UML 1 — Use Case Diagram"],
    ["CD","UML 2 — Class Diagram"],
    ["SD-1","UML 3 — Sequence: Student Registration"],
    ["SD-2","UML 4 — Sequence: Attendance Marking"],
    ["SD-3","UML 5 — Sequence: Login"],
    ["CP","UML 6 — Component Diagram"],
    ["ER","UML 7 — ER Diagram"],
]
el.append(mk_table(toc,[14*mm,150*mm]))
el.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# Q1
# ══════════════════════════════════════════════════════════════════════════════
qt(1,"What is your project and why you chose it?",el)
sec("Project Overview",el)
p("The <b>Smart Attendance System Using Face Recognition</b> is a full-stack web platform that "
  "automates student attendance using biometric facial recognition. It replaces slow, fraud-prone "
  "roll-call methods with an AI-powered camera-based system serving three roles: "
  "<b>Student, Teacher, Admin</b>, each with a dedicated web portal.",el)
sec("Key Features",el)
bl(["Student self-registration with webcam face capture and Gmail OTP verification.",
    "Teacher attendance marking via real-time camera — multiple student faces identified simultaneously.",
    "Manual attendance override, scoped to the teacher's own department.",
    "Student dashboard: monthly attendance calendar, percentage stats, and full history.",
    "Admin portal: user lifecycle management, audit logs, security review, report exports (Excel & PDF).",
    "Optional GPS geofencing — attendance may only be marked within a campus radius (Haversine formula).",
    "Automated daily absent notifications dispatched after a configurable IST cutoff (default 17:00).",
    "Duplicate biometric detection blocks registration fraud and writes a CRITICAL security log entry.",
    "Real-time WebSocket endpoint with polling fallback for live dashboard updates."],el)
sec("Why This Project",el)
bl(["Traditional methods (roll-call, sign sheets) are slow and trivially defeated by proxy signing.",
    "Face recognition is fast (multi-face scan in seconds), objective, and hard to spoof on a live webcam.",
    "Integrates advanced domains: computer vision, REST APIs, async programming, JWT auth, MongoDB — ideal as a capstone.",
    "Immediately deployable in any college with a webcam and internet connection.",
    "face_recognition library achieves 99.38% accuracy on LFW benchmark without a GPU."],el)
el.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# Q2
# ══════════════════════════════════════════════════════════════════════════════
qt(2,"How to implement your project?",el)
sec("Architecture",el)
p("Monolithic full-stack: one FastAPI process serves both the REST API and static frontend via "
  "StaticFiles mounts. Uvicorn (ASGI server) handles all HTTP + WebSocket connections. "
  "MongoDB is the persistence layer via the Motor async driver.",el)
steps=[
    ("Step 1 — Environment Setup","Python 3.11 venv. Install from requirements.txt: FastAPI, Uvicorn, Motor, face_recognition (dlib-bin on Windows), NumPy, OpenCV, ReportLab, Pandas, python-jose, passlib, python-dotenv."),
    ("Step 2 — Configure .env","Fill SECRET_KEY, MONGODB_URI, MAIL_*, CAMPUS_LAT/LON, FACE_TOLERANCE, LATE_HOUR, ABSENT_NOTICE_HOUR, and feature flags."),
    ("Step 3 — Database Setup","mongo.py creates unique indexes on users (id, email, roll_number), attendance (user_id+date), security_logs. Counters collection auto-increments all IDs."),
    ("Step 4 — Seed Accounts","create_admin.py + create_teachers.py populate the initial admin and teacher accounts per department."),
    ("Step 5 — Routes & Services","Routes (auth, teacher, student, attendance, admin) define HTTP endpoints by role. Services (face, attendance, user, email, report, security) contain all business logic."),
    ("Step 6 — Face Recognition Pipeline","Registration: Base64 JPEG → extract 128-D embedding → duplicate check → store in MongoDB. Attendance: classroom frame → multiple face encodings → match against dept students."),
    ("Step 7 — Auth (JWT + OTP)","OTP: 6-digit random → SHA-256+salt hash → email. Login: bcrypt verify → sign JWT (HS256, 60-min expiry). Protected endpoints validate JWT via get_current_user dependency."),
    ("Step 8 — Background Worker","asyncio task polls every 60 s. After cutoff, identifies absent students per dept, emails them, writes claim_doc to prevent double-send."),
    ("Step 9 — Frontend","Static HTML pages + shared JS (api.js auto-injects JWT Bearer) + CSS (glassmorphic design system)."),
    ("Step 10 — Run","uvicorn main:app --host 127.0.0.1 --port 8000 --reload  →  http://127.0.0.1:8000/static/index.html"),
]
for t,d_ in steps: sec(t,el); p(d_,el)
el.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# Q3
# ══════════════════════════════════════════════════════════════════════════════
qt(3,"What is the Existing System of your project?",el)
sec("Traditional Attendance Methods",el)
bl(["<b>Manual Roll-Call:</b> Teacher calls names, marks paper register — 5–10 min/session, no fraud protection.",
    "<b>Paper Sign Sheets:</b> Students sign their names — trivially defeated by proxy signing.",
    "<b>Fingerprint Scanners:</b> Secure but expensive; students must queue; cannot scan many at once.",
    "<b>RFID / Smart Cards:</b> Cards can be lent, lost, or cloned for proxy attendance.",
    "<b>QR Code Check-In:</b> QR screen can be shared remotely, enabling off-campus proxy.",
    "<b>Standalone Desktop Software:</b> Excel/offline tools — no shared DB, no notifications, no analytics."],el)
sec("Limitations",el)
bl(["No biometric binding — all methods susceptible to proxy attendance.",
    "Manual entry wastes instructional class time.",
    "No automated absent notifications to students.",
    "Data silos — no simultaneous access for admin, teacher, and student.",
    "No real-time reporting, trend analytics, or audit trail."],el)
sec("Gap Filled by This Project",el)
p("Every limitation above is directly addressed: face recognition eliminates proxy, camera-based marking "
  "takes seconds, automated emails alert absent students, a shared MongoDB database gives all roles "
  "real-time visibility, and every action is written to an immutable audit log.",el)
el.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# Q4
# ══════════════════════════════════════════════════════════════════════════════
qt(4,"What are the Proposed Methods and why you chose these methods?",el)
methods=[
    ("Face Recognition — HOG + ResNet-34 Embeddings",
     "dlib HOG locates faces; ResNet-34 maps each face to a 128-D float vector. Attendance granted when Euclidean distance ≤ FACE_TOLERANCE (0.5). 99.38% accuracy on LFW, CPU-only, one photo per student."),
    ("JWT Authentication (HS256)",
     "Stateless signed tokens — no session table needed. sub=user email; configurable 60-min expiry. api.js injects Bearer token into every fetch automatically."),
    ("Email OTP Verification",
     "6-digit random OTP, SHA-256+salt hashed (plain OTP never stored), expires in 10 min. Binds account to real Gmail ownership."),
    ("bcrypt Password Hashing",
     "Adaptive, salted hash via passlib. Cost factor raised as hardware improves; rainbow-table attacks infeasible."),
    ("Haversine Geofencing (Optional)",
     "Teacher GPS (navigator.geolocation) compared to campus coordinates via Haversine great-circle formula. Rejects marking if teacher is beyond MAX_DISTANCE_KM."),
    ("Async FastAPI + Motor",
     "asyncio event loop — DB queries and email sends are awaited without blocking; many concurrent sessions on one thread."),
    ("Duplicate Biometric Detection",
     "New face encoding vs. ALL active student encodings at registration. Match → deactivate existing; reject new registration; write CRITICAL security_log."),
    ("Background Absent Notification Worker",
     "asyncio coroutine polls every 60 s. After cutoff: iterate depts, find absent students, email each, write claim_doc to prevent double-send."),
]
for m,d_ in methods: sec(m,el); p(d_,el)
el.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# Q5
# ══════════════════════════════════════════════════════════════════════════════
qt(5,"What are the Data Sets / Sample Inputs and why chosen?",el)
sec("Live / Operational Inputs (Primary Dataset)",el)
bl(["<b>Student Face Images (Registration):</b> Single webcam photo per student. 128-D embedding stored — no offline dataset needed as ResNet-34 is pre-trained.",
    "<b>Teacher Classroom Frame:</b> Webcam frame with multiple faces. All encodings matched against the dept's stored embeddings.",
    "<b>GPS Coordinates:</b> navigator.geolocation provides lat/lon at each attendance event for geofencing and reporting.",
    "<b>IST Timestamps:</b> check_in stored as HH:MM:SS IST. Present vs. Late determined by configurable threshold (default 09:30).",
    "<b>Gmail Addresses + OTPs:</b> Gmail required; 6-digit OTPs bind account to real email ownership."],el)
sec("Seeded / Sample Data (Development & Demo)",el)
bl(["<b>seeded_users_export.csv:</b> 100+ pre-seeded student accounts for demo/testing.",
    "<b>create_teachers.py:</b> Seeds CS, Mechanical, Civil, etc. teacher accounts with known credentials.",
    "<b>create_admin.py:</b> Seeds the single system administrator account.",
    "<b>simulate_duplicate_face_incidents.py:</b> Inserts synthetic CRITICAL security log events for admin demo."],el)
sec("Why This Data Strategy",el)
bl(["Pre-trained ResNet-34 generalizes to any person — only one reference image per student needed.",
    "Storing 128-float embedding (~1 KB) instead of raw images keeps MongoDB compact.",
    "Limiting face comparison to teacher's dept reduces computation and false-positive risk."],el)
el.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# Q6
# ══════════════════════════════════════════════════════════════════════════════
qt(6,"Hardware & Software Requirements — are these enough or not and why?",el)
sec("Hardware Requirements",el)
el.append(mk_table([
    ["Component","Minimum","Recommended"],
    ["CPU","i3 / Ryzen 3, 2 cores, 2 GHz","i5/i7 or Ryzen 5/7, 4+ cores"],
    ["RAM","4 GB","8–16 GB"],
    ["Storage","2 GB free","SSD with 10+ GB free"],
    ["Webcam","720p (1.3 MP)","1080p for reliable face detection"],
    ["Network","Wi-Fi / LAN","Stable LAN for multi-user deployment"],
    ["GPU","Not required (CPU inference)","NVIDIA GPU for 1000+ student scale"],
],[40*mm,57*mm,67*mm]));el.append(sp(6))
sec("Software Requirements",el)
el.append(mk_table([
    ["Category","Technology","Version / Notes"],
    ["Language","Python","3.11 (required for dlib-bin Windows wheel)"],
    ["Web Framework","FastAPI + Uvicorn","Latest stable (with websockets)"],
    ["Database","MongoDB + Motor","6.x Community or Atlas"],
    ["Face Recognition","face_recognition + dlib","1.3.0 / dlib-bin 19.24.6"],
    ["Numerical / Image","NumPy, OpenCV, Pillow","1.24.3 / 4.8.1 / 12.0.0"],
    ["Auth / Security","python-jose, passlib[bcrypt]","JWT HS256 + bcrypt"],
    ["Reports","Pandas, openpyxl, ReportLab","Latest stable"],
    ["Email","smtplib (stdlib)","Gmail SMTP + App Password"],
    ["Frontend","HTML5, CSS3, Vanilla JS","No build step required"],
],[38*mm,52*mm,74*mm]));el.append(sp(6))
sec("Are These Requirements Enough?",el)
p("<b>Yes — for departmental / single-campus deployment.</b> CPU-only face recognition handles "
  "20–40 students/dept in 1–3 s. MongoDB + Motor handles hundreds of concurrent sessions. "
  "FastAPI asyncio serves dozens of browser connections on one thread. "
  "<b>Scale-up path:</b> GPU inference, MongoDB replica set, Nginx + multiple workers, SendGrid/SES.",el)
el.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# Q7
# ══════════════════════════════════════════════════════════════════════════════
qt(7,"Why the specific language was chosen and its advantages?",el)
sec("Backend: Python 3.11",el)
bl(["<b>CV/ML Ecosystem:</b> face_recognition, dlib, NumPy, OpenCV are Python-native — no equivalent one-line embedding API elsewhere.",
    "<b>FastAPI:</b> Highest-performance Python web framework; auto-generates OpenAPI docs; uses type hints for zero-boilerplate validation.",
    "<b>Rapid Development:</b> Concise syntax + rich stdlib cuts boilerplate by 50–70% vs. Java.",
    "<b>Async-First (asyncio):</b> Non-blocking DB queries, email sends, and background worker — all on one thread.",
    "<b>Motor + pymongo:</b> Best-in-class async MongoDB drivers are Python-first.",
    "<b>Platform Portability:</b> Same codebase on Windows (dlib-bin wheel) and Linux without changes.",
    "<b>Readability:</b> Enforced indentation + 'plain English' style — easy to maintain."],el)
sec("Frontend: HTML5 + CSS3 + Vanilla JavaScript",el)
bl(["<b>Zero Build Step:</b> No npm, Webpack, or bundler — immediate development loop.",
    "<b>Full Design Control:</b> Vanilla CSS with custom properties: glassmorphism, animated backgrounds, gradient buttons.",
    "<b>Browser Native APIs:</b> WebRTC (camera), navigator.geolocation (GPS), Fetch API — used directly.",
    "<b>No Framework Lock-In:</b> Plain HTML works in every browser without Node.js tooling.",
    "<b>Lightweight:</b> No JS framework download — faster load on slow networks."],el)
el.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# Q8
# ══════════════════════════════════════════════════════════════════════════════
qt(8,"Testing Methods applied — are they enough? What is the need of testing?",el)
sec("Need for Testing",el)
p("This system handles sensitive academic data (attendance records affecting grades), biometric "
  "information, JWT sessions, SMTP delivery, and security logging. Defects can cause data corruption, "
  "privacy breaches, or denial of service — making rigorous testing essential.",el)
tests=[
    ("1. Module / Unit Smoke Tests","test_import.py: all backend modules import without errors. test_register.py: real POST /register inspects JSON response."),
    ("2. Integration Testing (FastAPI Swagger /docs)","Every endpoint tested in sequence: register → OTP verify → login → mark attendance → export report. Validates full request/response lifecycle including DI, middleware, serialization."),
    ("3. Database State Verification (check_db.py)","Directly queries MongoDB after migrations/seeds — prints security logs, config docs, counter values."),
    ("4. Boundary & Input Validation","Pydantic models enforce: email=EmailStr, password ≥ 6 chars, OTP exactly 6 digits, Base64 image non-empty. FastAPI returns HTTP 422 for violations."),
    ("5. Security / Negative Testing","Duplicate face: simulate_duplicate_face_incidents.py verifies CRITICAL log and account deactivation. Token expiry: confirms HTTP 401. Role guard: student JWT → /admin → HTTP 403."),
    ("6. Email Delivery Testing","Real Gmail SMTP tested live. Console-log fallback verified with MAIL_ENABLED=false. OTP 10-min expiry verified."),
    ("7. Geofencing Edge-Case Testing","Haversine utility tested with coordinates just inside and just outside the allowed radius."),
    ("8. Face Recognition Accuracy Tuning","Multiple registrations under varying lighting/angles. FACE_TOLERANCE tuned 0.6 → 0.5 to reduce false positives."),
]
for t,d_ in tests: sec(t,el); p(d_,el)
sec("Are These Methods Enough?",el)
p("For academic/pilot deployment: <b>Yes</b>. For production: add pytest + mongomock, CI/CD (GitHub Actions), "
  "Locust load testing, and OWASP ZAP pen-testing.",el)
el.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# Q9
# ══════════════════════════════════════════════════════════════════════════════
qt(9,"What type of UML models are used in your project and why?",el)
umls=[
    ("1. Use Case Diagram","Actors: Student, Teacher, Admin, Email Service, MongoDB. Use cases: Register, Login, Mark Attendance (Face/Manual), View Dashboard, Export Reports, Manage Users, Configure Settings, Review Security Logs, Verify OTP, Receive Absent Email. WHY: Captures all actor-system interactions for requirements phase."),
    ("2. Class Diagram","Key Pydantic schemas (UserCreate, UserOut, AttendanceOut, TeacherStats, AdminConfig) and service classes (FaceService, AttendanceService, UserService, EmailService, ReportService). WHY: Documents static data model and inter-class relationships."),
    ("3. Sequence Diagram — Registration","Browser → POST /register → extract_encoding → duplicate check → create_student_user → send_otp_email → POST /verify-otp → mark_verified → success email. WHY: Shows exact temporal order of async calls."),
    ("4. Sequence Diagram — Attendance","Browser (Teacher) → POST /teacher/mark-attendance → geofence check → extract_multiple_encodings → find_matches → insert records → response. WHY: Maps the multi-service call chain clearly."),
    ("5. Sequence Diagram — Login","Browser → POST /login → get_user_by_email → verify_password → create_access_token → GET /users/me → role redirect. WHY: Clarifies the stateless JWT authentication flow."),
    ("6. Component Diagram","Components: FastAPI App, MongoDB, Browser, SMTP Gateway, face_recognition Library, WebSocket Manager. WHY: Shows deployment topology and in-process vs. external services."),
    ("7. ER Diagram","Entities: users, attendance, security_logs, config, counters, absent_notification_claims. Relationships: users 1-to-many attendance (user_id FK), users 1-to-many security_logs. WHY: Documents the MongoDB data model and application-layer referential integrity."),
]
for u,d_ in umls: sec(u,el); p(d_,el)
el.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
# Q10
# ══════════════════════════════════════════════════════════════════════════════
qt(10,"Conclusion and Future Enhancement of the project?",el)
sec("Conclusion",el)
p("The <b>Smart Attendance System Using Face Recognition</b> demonstrates a production-grade, "
  "full-stack solution to a real-world institutional problem. By combining biometric face recognition, "
  "role-based web portals, email-driven OTP verification, optional geofenced attendance, and automated "
  "absence notifications in one FastAPI + MongoDB application, the project eliminates proxy attendance, "
  "reduces administrative overhead, and provides transparent, auditable records to all stakeholders.",el)
p("Security-first design: bcrypt hashes, signed JWTs, duplicate-face detection with CRITICAL audit logging, "
  "and password re-confirmation for all privileged admin actions make the platform suitable for real "
  "institutional deployment. The lean Python + MongoDB + Vanilla JS stack is readable and maintainable.",el)
sec("Future Enhancements",el)
bl(["Liveness Detection (blink/head-pose challenge) to prevent photo/screen spoofing.",
    "Mobile App (Flutter/React Native) — native camera + GPS for teachers without laptops.",
    "GPU-Accelerated Inference (CUDA dlib / InsightFace) — reduce per-frame time from 2–3 s to <200 ms.",
    "Real-Time WebSocket Push — /ws endpoint and ConnectionManager already scaffolded; wire attendance_marked events.",
    "TOTP Multi-Factor Authentication — MFA_ENABLED flag exists; integrate pyotp for admin/teacher 2FA.",
    "Account Lockout Policy — LOCKOUT_ENABLED flag exists; implement 5-attempt lockout for 15 minutes.",
    "Subject-wise / Timetable-Integrated Attendance — per-subject percentage reports.",
    "Advanced Analytics Dashboard — weekly heatmaps, trend charts, early-warning for students below 75%.",
    "Docker + CI/CD Cloud Deployment — containerise, deploy to AWS/GCP/Azure via GitHub Actions + MongoDB Atlas.",
    "PWA / Offline Mode — service worker queues attendance actions when network is intermittent."],el)
sec("Module Assignment",el)
bl(["Module 1 — Authentication & User Management (Registration, OTP, Login, Profile)",
    "Module 2 — Face Recognition Pipeline (Enrollment, Matching, Duplicate Detection)",
    "Module 3 — Attendance Marking & Finalization (Face + Manual, Geofencing, Cutoff Logic)",
    "Module 4 — Student Dashboard & Reporting (Calendar, Stats, History)",
    "Module 5 — Admin Portal (User Lifecycle, Config, Security Logs, Report Exports)",
    "Module 6 — Email & Notification Services (OTP, Absent Notices, Password Alerts)"],el)
el.append(PageBreak())

# ══════════════════════════════════════════════════════════════════════════════
#  DIAGRAMS SECTION
# ══════════════════════════════════════════════════════════════════════════════
el.append(sp(20))
el.append(Paragraph("DIAGRAMS & UML CHARTS",ParagraphStyle("BH",fontSize=16,fontName="Helvetica-Bold",
    textColor=TEAL,alignment=1,spaceAfter=6)))
el.append(Paragraph("All Flowcharts and UML Diagrams — drawn to A4 page scale",
    ParagraphStyle("BS",fontSize=10,fontName="Helvetica",textColor=SLATE,alignment=1,spaceAfter=4)))
el.append(hr()); el.append(PageBreak())

# FC 1A
dh("FLOWCHART 1A — Student Registration Process (Steps 1–10: Validation & Face Check)",el)
p("Input validation (Gmail, email uniqueness, roll uniqueness), webcam face capture, "
  "128-D encoding extraction, and duplicate biometric detection. All error branches shown.",el)
el.append(sp(4)); el.append(sd(fc_reg_a()))
cap("FC-1A: Registration Steps 1–10 — form validation, face capture, and duplication check",el)
el.append(PageBreak())

# FC 1B
dh("FLOWCHART 1B — Student Registration Process (Steps 11–20: OTP & Verification)",el)
p("OTP generation, MongoDB user insertion, SMTP email dispatch, OTP entry, expiry check, "
  "hash verification, account activation, and success email dispatch.",el)
el.append(sp(4)); el.append(sd(fc_reg_b()))
cap("FC-1B: Registration Steps 11–20 — OTP flow and account activation",el)
el.append(PageBreak())

# FC 2
dh("FLOWCHART 2 — Login / Authentication Process",el)
p("Email lookup, account status validation, bcrypt password check, email verification guard, "
  "JWT token creation, last_login_at update, and role-based dashboard redirection.",el)
el.append(sp(4)); el.append(sd(fc_login()))
cap("FC-2: Login and authentication flow with all validation and error branches",el)
el.append(PageBreak())

# FC 3
dh("FLOWCHART 3 — Face-Based Attendance Marking",el)
p("Teacher-initiated flow: webcam capture, optional geofencing, multi-face extraction, "
  "department student matching, and Present/Late status determination by IST check-in time.",el)
el.append(sp(4)); el.append(sd(fc_attend()))
cap("FC-3: Face-based attendance marking with optional geofencing and multi-face match logic",el)
el.append(PageBreak())

# FC 4
dh("FLOWCHART 4 — Absent Notification Background Worker",el)
p("Long-running asyncio task that polls every 60 seconds, checks the IST cutoff, iterates "
  "departments, finds absent students, sends HTML emails, and prevents duplicate sends via "
  "claim documents.",el)
el.append(sp(4)); el.append(sd(fc_absent()))
cap("FC-4: Background asyncio absent notification worker with duplicate-send prevention",el)
el.append(PageBreak())

# UML 1
dh("UML DIAGRAM 1 — Use Case Diagram",el)
p("All actors (Student, Teacher, Admin, Email Service, MongoDB) and their use cases within "
  "the system boundary of the Smart Attendance System.",el)
el.append(sp(4)); el.append(sd(uml_usecase()))
cap("UML 1: Use Case Diagram — actors and their interactions with the system",el)
el.append(PageBreak())

# UML 2
dh("UML DIAGRAM 2 — Class Diagram (Core Classes)",el)
p("MongoDB document classes (User, Attendance, SecurityLog), service classes (FaceService, "
  "AttendanceService, UserService, EmailService), and Settings configuration dataclass, "
  "with attributes, methods, and inter-class relationships.",el)
el.append(sp(4)); el.append(sd(uml_class()))
cap("UML 2: Class Diagram — core data models and service classes with associations",el)
el.append(PageBreak())

# UML 3
dh("UML DIAGRAM 3 — Sequence Diagram: Student Registration",el)
p("Complete temporal sequence of method calls between Browser, auth.py route, face_service, "
  "user_service, email_service, and MongoDB during student registration and OTP verification.",el)
el.append(sp(4)); el.append(sd(uml_seq_reg()))
cap("UML 3: Sequence Diagram — Student registration with all participants and messages",el)
el.append(PageBreak())

# UML 4
dh("UML DIAGRAM 4 — Sequence Diagram: Attendance Marking (Face)",el)
p("Sequence of calls between Browser (Teacher), teacher.py route, attendance_service, "
  "face_service, geo_utils, and MongoDB during a face-based attendance marking event.",el)
el.append(sp(4)); el.append(sd(uml_seq_attend()))
cap("UML 4: Sequence Diagram — Teacher face-based attendance marking process",el)
el.append(PageBreak())

# UML 5
dh("UML DIAGRAM 5 — Sequence Diagram: User Login",el)
p("Sequence during login: email lookup, bcrypt verification, JWT token creation, "
  "last_login_at update, and the GET /users/me call that determines role-based redirect.",el)
el.append(sp(4)); el.append(sd(uml_seq_login()))
cap("UML 5: Sequence Diagram — User login and JWT authentication flow",el)
el.append(PageBreak())

# UML 6
dh("UML DIAGRAM 6 — Component Diagram",el)
p("Major components — Browser (Frontend), FastAPI Application, Static File Mount, MongoDB, "
  "Gmail SMTP, face_recognition Library, WebSocket Manager — with interfaces and protocols.",el)
el.append(sp(4)); el.append(sd(uml_component()))
cap("UML 6: Component Diagram — system components and their interfaces",el)
el.append(PageBreak())

# UML 7
dh("UML DIAGRAM 7 — Entity-Relationship (ER) Diagram",el)
p("All MongoDB collections as entities — users, attendance, security_logs, config, counters, "
  "absent_notification_claims — with all fields, primary keys, foreign key references, "
  "and cardinality relationships.",el)
el.append(sp(4)); el.append(sd(uml_er()))
cap("UML 7: ER Diagram — all MongoDB collections with fields and relationships",el)

# Footer
el.append(sp(14)); el.append(hr())
el.append(Paragraph("<i>End of Document | Smart Attendance System Using Face Recognition | "
    "Project Review Q&amp;A + All Diagrams | April 2026</i>",
    ParagraphStyle("FT",fontSize=8,fontName="Helvetica-Oblique",
                   textColor=SLATE,alignment=1)))

# Build
doc.build(el)
print("PDF generated: " + OUTPUT_FILE)
