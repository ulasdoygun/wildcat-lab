from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

BLUE  = colors.HexColor("#1a3a5c")
BLUE2 = colors.HexColor("#2563a8")
LBLUE = colors.HexColor("#dbeafe")
LGRAY = colors.HexColor("#f1f5f9")
LGRAY2= colors.HexColor("#e2e8f0")
WHITE = colors.white
YELLOW= colors.HexColor("#fef9c3")

UNITS = {
    "dtex": "dtex", "total_dtex": "dtex",
    "boiling_shrinkage": "%", "thickness": "µm",
    "tensile": "N", "yarn_wrap": "wraps/m",
    "air_shrinkage": "%", "width": "mm", "elongation": "%",
}

def P(text, size=8, bold=False, color=colors.black, align=TA_LEFT):
    style = ParagraphStyle('x', fontSize=size,
                           fontName='Helvetica-Bold' if bold else 'Helvetica',
                           textColor=color, alignment=align,
                           leading=size*1.3)
    return Paragraph(str(text) if text is not None else "-", style)

def fmt(val):
    if val is None: return "-"
    try:
        f = float(val)
        return f"{f:.1f}" if f != int(f) else str(int(f))
    except: return str(val)

def generate_pdf(record):
    buffer  = io.BytesIO()
    doc     = SimpleDocTemplate(buffer, pagesize=landscape(A4),
                                rightMargin=10*mm, leftMargin=10*mm,
                                topMargin=10*mm, bottomMargin=10*mm)
    story   = []
    colors_list = record.get("colors", [])
    positions   = record.get("positions", [])
    test_data   = record.get("test_data", {})
    nc          = len(colors_list)

    # ── Header ────────────────────────────────────────────────────────────────
    hdr = Table([[P("WILDCAT ENTERPRISE TEXTILES INDUSTRIES", 12, True, WHITE, TA_CENTER)]],
                colWidths=[277*mm])
    hdr.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),BLUE),
                              ('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    story.append(hdr)

    sub = Table([[P("WC-F-QC-05  Mono Yarn Full Inspection Form  |  Rev.00  |  Date: 02-Jan-2025",
                    8, False, WHITE, TA_CENTER)]], colWidths=[277*mm])
    sub.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),BLUE2),
                              ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4)]))
    story.append(sub)
    story.append(Spacer(1,3*mm))

    # ── Info row ──────────────────────────────────────────────────────────────
    info_data = [[
        P("LINE",7,True), P(record.get("line",""),8),
        P("SHIFT",7,True), P(record.get("shift",""),8),
        P("DATE",7,True), P(record.get("date",""),8),
        P("TIME",7,True), P(record.get("time",""),8),
        P("WO",7,True), P(record.get("wo",""),8),
        P("ITEM",7,True), P(record.get("item",""),8),
        P("OPERATOR",7,True), P(record.get("operator",""),8),
    ]]
    info_tbl = Table(info_data, colWidths=[x*mm for x in [16,22,14,14,14,26,13,16,16,26,14,22,18,37]])
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
    story.append(Spacer(1,4*mm))

    # ── Test rows — 2 positions side by side ─────────────────────────────────
    TESTS = [
        ("dtex",             "DTEX"),
        ("total_dtex",       "TOTAL DTEX"),
        ("boiling_shrinkage","BOILING SHRINKAGE (AVE)"),
        ("thickness",        "THICKNESS"),
        ("tensile",          "TENSILE (AVE)"),
        ("yarn_wrap",        "YARN WRAP PER METER"),
        ("air_shrinkage",    "AIR SHRINKAGE"),
        ("width",            "WIDTH"),
        ("elongation",       "ELONGATION (AVE)"),
    ]

    # Column widths for one position block
    # test_label | unit | color1 | color2 | ... (max 4 colors)
    lw  = 32*mm   # label
    uw  = 12*mm   # unit
    cvw = 14*mm   # color value
    sep = 6*mm    # separator between two pos blocks

    one_block_w = lw + uw + nc*cvw
    total_w     = 277*mm
    # We can fit 2 positions side by side
    pairs = [(positions[i], positions[i+1] if i+1 < len(positions) else None)
             for i in range(0, len(positions), 2)]

    for pos_left, pos_right in pairs:
        # Header for this pair
        def make_pos_header(pos):
            if pos is None: return []
            row = [P(f"Pos: {pos}", 8, True, WHITE, TA_CENTER)]
            row += [P("Unit", 7, False, WHITE, TA_CENTER)]
            for c in colors_list:
                row.append(P(c, 7, True, WHITE, TA_CENTER))
            return row

        header_left  = make_pos_header(pos_left)
        header_right = make_pos_header(pos_right) if pos_right else []

        if header_right:
            combined_header = header_left + [P("")] + header_right
        else:
            combined_header = header_left

        col_widths = [lw, uw] + [cvw]*nc
        if pos_right:
            col_widths += [sep] + [lw, uw] + [cvw]*nc

        rows = [combined_header]

        pd_l = test_data.get(pos_left, {})
        pd_r = test_data.get(pos_right, {}) if pos_right else {}

        for key, label in TESTS:
            unit = UNITS.get(key,"")
            # left side
            row = [P(label, 7, True), P(unit, 7, False, colors.HexColor("#0369a1"))]
            if key in ("total_dtex", "yarn_wrap"):
                val = pd_l.get(key)
                row.append(P(fmt(val), 8))
                row += [P("")] * (nc-1)
            else:
                d = pd_l.get(key, {})
                for c in colors_list:
                    row.append(P(fmt(d.get(c) if isinstance(d,dict) else None), 8))
            # right side
            if pos_right:
                row.append(P(""))  # separator
                row.append(P(label, 7, True))
                row.append(P(unit, 7, False, colors.HexColor("#0369a1")))
                if key in ("total_dtex", "yarn_wrap"):
                    val = pd_r.get(key)
                    row.append(P(fmt(val), 8))
                    row += [P("")] * (nc-1)
                else:
                    d = pd_r.get(key, {})
                    for c in colors_list:
                        row.append(P(fmt(d.get(c) if isinstance(d,dict) else None), 8))
            rows.append(row)

        tbl = Table(rows, colWidths=col_widths)
        style = [
            ('BACKGROUND',(0,0),(1+nc,0),BLUE2),
            ('TEXTCOLOR',(0,0),(1+nc,0),WHITE),
            ('GRID',(0,0),(1+nc,-1),0.4,LGRAY2),
            ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
            ('TOPPADDING',(0,0),(-1,-1),2),('BOTTOMPADDING',(0,0),(-1,-1),2),
            ('FONTSIZE',(0,0),(-1,-1),8),
        ]
        if pos_right:
            right_start = 2+nc+1  # after separator
            style += [
                ('BACKGROUND',(right_start,0),(-1,0),BLUE2),
                ('TEXTCOLOR',(right_start,0),(-1,0),WHITE),
                ('GRID',(right_start,0),(-1,-1),0.4,LGRAY2),
                ('BACKGROUND',(2+nc,0),(2+nc,-1),colors.white),  # separator col
                ('GRID',(2+nc,0),(2+nc,-1),0,colors.white),
            ]
            # Alternate row shading
            for ri in range(1, len(rows)):
                if ri % 2 == 0:
                    style.append(('BACKGROUND',(0,ri),(1+nc,ri),LGRAY))
                    style.append(('BACKGROUND',(right_start,ri),(-1,ri),LGRAY))
        else:
            for ri in range(1, len(rows)):
                if ri % 2 == 0:
                    style.append(('BACKGROUND',(0,ri),(1+nc,ri),LGRAY))

        tbl.setStyle(TableStyle(style))
        story.append(tbl)
        story.append(Spacer(1,3*mm))

    # ── SCI/SCE ───────────────────────────────────────────────────────────────
    sci   = record.get("sci", {})
    spool = record.get("spool_no", "")
    if sci:
        sci_row  = [P(f"SCI/SCE  (Spool: {spool})", 7, True)] 
        sci_vals = [P(f"{c}: {sci.get(c,'-')}", 8) for c in colors_list]
        sci_data_tbl = Table([sci_row + sci_vals],
                              colWidths=[50*mm] + [40*mm]*nc)
        sci_data_tbl.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(0,0),LGRAY),
            ('GRID',(0,0),(-1,-1),0.4,LGRAY2),
            ('TOPPADDING',(0,0),(-1,-1),3),('BOTTOMPADDING',(0,0),(-1,-1),3),
        ]))
        story.append(sci_data_tbl)
        story.append(Spacer(1,3*mm))

    # ── Comments ──────────────────────────────────────────────────────────────
    comments = record.get("comments","")
    if comments:
        cmt = Table([[P("Comments:", 7, True), P(comments, 8)]],
                     colWidths=[25*mm, 252*mm])
        cmt.setStyle(TableStyle([
            ('BACKGROUND',(0,0),(0,0),LGRAY),
            ('GRID',(0,0),(-1,-1),0.4,LGRAY2),
            ('VALIGN',(0,0),(-1,-1),'TOP'),
            ('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ]))
        story.append(cmt)
        story.append(Spacer(1,3*mm))

    # ── Tolerance / Verified ──────────────────────────────────────────────────
    tol = Table([[
        P("TOLERANCE VALUE CHECK", 7, True),
        P("All tests conducted per standard procedure. Results verified for accuracy and compliance.", 7),
        P(f"Verified by: {record.get('verified_by','')}", 8, True),
    ]], colWidths=[45*mm, 190*mm, 42*mm])
    tol.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(0,0),LGRAY),('BACKGROUND',(2,0),(2,0),LGRAY),
        ('GRID',(0,0),(-1,-1),0.4,LGRAY2),
        ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
        ('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),
    ]))
    story.append(tol)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
