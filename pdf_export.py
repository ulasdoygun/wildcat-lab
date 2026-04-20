from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, KeepTogether
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

def initials(name):
    """FIELD GREEN -> FG, OLIVE GREEN -> OG, etc."""
    words = name.strip().split()
    return "".join(w[0].upper() for w in words if w)

BLUE  = colors.HexColor("#1a3a5c")
BLUE2 = colors.HexColor("#2563a8")
LGRAY = colors.HexColor("#f1f5f9")
LGRAY2= colors.HexColor("#e2e8f0")
WHITE = colors.white

UNITS = {
    "dtex":"dtex","total_dtex":"dtex","boiling_shrinkage":"%",
    "thickness":"µm","tensile":"N","yarn_wrap":"wraps/m",
    "air_shrinkage":"%","width":"mm","elongation":"%",
}
TESTS = [
    ("dtex","DTEX"),("total_dtex","TOTAL DTEX"),
    ("boiling_shrinkage","BOILING SHRINKAGE"),
    ("thickness","THICKNESS"),("tensile","TENSILE (AVE)"),
    ("yarn_wrap","YARN WRAP/M"),
    ("air_shrinkage","AIR SHRINKAGE"),
    ("width","WIDTH"),("elongation","ELONGATION"),
]

def P(text, size=8, bold=False, color=colors.black, align=TA_LEFT):
    s = ParagraphStyle('x', fontSize=size,
                       fontName='Helvetica-Bold' if bold else 'Helvetica',
                       textColor=color, alignment=align,
                       leading=max(size+2, 10), wordWrap='CJK')
    return Paragraph(str(text) if text is not None else "-", s)

def fmt(val):
    if val is None: return "-"
    try:
        f = float(val)
        if f == 0: return "-"
        return f"{f:.1f}" if f != int(f) else str(int(f))
    except: return str(val) if val else "-"

def make_pos_table(pos, pd, colors_list, block_w_mm=93):
    nc = len(colors_list)
    # Column widths: label=38mm, unit=9mm, each color=min(18,170/(nc) mm
    avail = 170
    # label=28, unit=8, color cols as narrow as possible
    lw = 28; uw = 7
    cvw = 10  # FG/OG/LG initials are short, 10mm is enough
    col_w = [lw*mm, uw*mm] + [cvw*mm]*nc

    # Header row
    hdr = [P(f"Pos: {pos}", 8, True, WHITE, TA_CENTER),
           P("Unit", 7, False, WHITE, TA_CENTER)]
    for c in colors_list:
        hdr.append(P(initials(c), 7, True, WHITE, TA_CENTER))

    rows = [hdr]
    for key, label in TESTS:
        unit = UNITS.get(key,"")
        row  = [P(label, 6, True), P(unit, 6, False, colors.HexColor("#0369a1"))]
        if key in ("total_dtex","yarn_wrap"):
            val = pd.get(key)
            row.append(P(fmt(val), 8))
            row += [P("-")]*( nc-1)
        else:
            d = pd.get(key, {})
            for c in colors_list:
                v = d.get(c) if isinstance(d,dict) else None
                row.append(P(fmt(v), 8))
        rows.append(row)

    style = [
        ('BACKGROUND',(0,0),(-1,0),BLUE2),
        ('TEXTCOLOR',(0,0),(-1,0),WHITE),
        ('GRID',(0,0),(-1,-1),0.4,LGRAY2),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),1),
        ('BOTTOMPADDING',(0,0),(-1,-1),1),
        ('FONTSIZE',(0,0),(-1,-1),7),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[WHITE,LGRAY]),
    ]
    t = Table(rows, colWidths=col_w, splitByRow=1)
    t.setStyle(TableStyle(style))
    return t

def generate_pdf(record):
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(buffer, pagesize=A4,
                               rightMargin=10*mm, leftMargin=10*mm,
                               topMargin=10*mm, bottomMargin=10*mm)
    story  = []
    colors_list = record.get("colors",[])
    positions   = record.get("positions",[])
    test_data   = record.get("test_data",{})

    # ── Header ────────────────────────────────────────────────────────────────
    for text, bg, fsize in [
        ("WILDCAT ENTERPRISE TEXTILES INDUSTRIES", BLUE, 11),
        ("WC-F-QC-05  Mono Yarn Full Inspection Form  |  Rev.00  |  02-Jan-2025", BLUE2, 8),
    ]:
        t = Table([[P(text, fsize, fsize>9, WHITE, TA_CENTER)]], colWidths=[190*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(-1,-1),bg),
            ('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6),
        ]))
        story.append(t)
    story.append(Spacer(1,3*mm))

    # ── Info ──────────────────────────────────────────────────────────────────
    fields = [
        ("LINE",record.get("line","")),("SHIFT",record.get("shift","")),
        ("DATE",record.get("date","")),("TIME",record.get("time","")),
        ("WO",record.get("wo","")),("ITEM",record.get("item","")),
        ("OPERATOR",record.get("operator","")),
    ]
    info_row  = []
    info_cw   = []
    for lbl, val in fields:
        info_row += [P(lbl,6,True), P(str(val),7)]
        info_cw  += [12*mm, 15*mm]
    # trim to 190mm
    info_tbl = Table([info_row], colWidths=info_cw)
    info_tbl.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(0,0),LGRAY),('BACKGROUND',(2,0),(2,0),LGRAY),
        ('BACKGROUND',(4,0),(4,0),LGRAY),('BACKGROUND',(6,0),(6,0),LGRAY),
        ('BACKGROUND',(8,0),(8,0),LGRAY),('BACKGROUND',(10,0),(10,0),LGRAY),
        ('BACKGROUND',(12,0),(12,0),LGRAY),
        ('GRID',(0,0),(-1,-1),0.4,LGRAY2),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1,3*mm))

    # ── Positions — 2 per row ─────────────────────────────────────────────────
    pairs = [(positions[i], positions[i+1] if i+1<len(positions) else None)
             for i in range(0,len(positions),2)]

    for pos_l, pos_r in pairs:
        block_w = 93  # mm per block when 2 side by side (190 - 4 sep) / 2
        tbl_l = make_pos_table(pos_l, test_data.get(pos_l,{}), colors_list, block_w)
        if pos_r:
            tbl_r = make_pos_table(pos_r, test_data.get(pos_r,{}), colors_list, block_w)
            combined = Table([[tbl_l, Spacer(4*mm,1), tbl_r]],
                              colWidths=[93*mm, 4*mm, 93*mm],
                              splitByRow=0)
            combined.setStyle(TableStyle([
                ('VALIGN',(0,0),(-1,-1),'TOP'),
                ('TOPPADDING',(0,0),(-1,-1),0),
                ('BOTTOMPADDING',(0,0),(-1,-1),0),
                ('LEFTPADDING',(0,0),(-1,-1),0),
                ('RIGHTPADDING',(0,0),(-1,-1),0),
            ]))
            story.append(KeepTogether(combined))
        else:
            tbl_l = make_pos_table(pos_l, test_data.get(pos_l,{}), colors_list, 190)
            story.append(KeepTogether(tbl_l))
        story.append(Spacer(1,3*mm))

    # ── SCI/SCE ───────────────────────────────────────────────────────────────
    sci   = record.get("sci",{})
    spool = record.get("spool_no","")
    if any(sci.values()):
        row = [P(f"SCI/SCE (Spool: {spool})",7,True)]
        cw  = [45*mm]
        for c in colors_list:
            row.append(P(f"{c}: {sci.get(c,'-')}",7))
            cw.append(35*mm)
        t = Table([row], colWidths=cw)
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(0,0),LGRAY),
            ('GRID',(0,0),(-1,-1),0.4,LGRAY2),
            ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
        ]))
        story.append(t)
        story.append(Spacer(1,3*mm))

    # ── Comments ──────────────────────────────────────────────────────────────
    comments = record.get("comments","")
    if comments:
        t = Table([[P("Comments:",7,True), P(comments,7)]],
                   colWidths=[22*mm,168*mm])
        t.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(0,0),LGRAY),
            ('GRID',(0,0),(-1,-1),0.4,LGRAY2),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ]))
        story.append(t)
        story.append(Spacer(1,3*mm))

    # ── Tolerance / Verified ──────────────────────────────────────────────────
    t = Table([[
        P("TOLERANCE VALUE CHECK",7,True),
        P("All tests conducted per standard procedure. Verified for accuracy and compliance.",7),
        P(f"Verified by:\n{record.get('verified_by','')}",7,True),
    ]], colWidths=[40*mm,110*mm,40*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(0,0),LGRAY),('BACKGROUND',(2,0),(2,0),LGRAY),
        ('GRID',(0,0),(-1,-1),0.4,LGRAY2),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]))
    story.append(t)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
