from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import io

def generate_pdf(record):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4,
                            rightMargin=15*mm, leftMargin=15*mm,
                            topMargin=15*mm, bottomMargin=15*mm)
    styles = getSampleStyleSheet()
    story  = []

    BLUE  = colors.HexColor("#1a3a5c")
    BLUE2 = colors.HexColor("#2563a8")
    LBLUE = colors.HexColor("#dbeafe")
    LGRAY = colors.HexColor("#f1f5f9")
    WHITE = colors.white

    title_style = ParagraphStyle('title', fontSize=11, textColor=WHITE,
                                  alignment=TA_CENTER, fontName='Helvetica-Bold')
    sub_style   = ParagraphStyle('sub',   fontSize=8,  textColor=WHITE,
                                  alignment=TA_CENTER, fontName='Helvetica')
    label_style = ParagraphStyle('lbl',   fontSize=7,  textColor=colors.HexColor("#1e293b"),
                                  fontName='Helvetica-Bold')
    val_style   = ParagraphStyle('val',   fontSize=8,  textColor=colors.black,
                                  fontName='Helvetica')
    unit_style  = ParagraphStyle('unit',  fontSize=7,  textColor=colors.HexColor("#0369a1"),
                                  fontName='Helvetica-Oblique')

    UNITS = {
        "dtex": "dtex", "total_dtex": "dtex",
        "boiling_shrinkage": "%", "thickness": "µm",
        "tensile": "N", "yarn_wrap": "wraps/m",
        "air_shrinkage": "%", "width": "mm", "elongation": "%",
    }

    # Header
    header_data = [[Paragraph("WILDCAT ENTERPRISE TEXTILES INDUSTRIES", title_style)]]
    header_tbl  = Table(header_data, colWidths=[180*mm])
    header_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BLUE),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
    ]))
    story.append(header_tbl)

    sub_data = [[Paragraph("WC-F-QC-05 Mono Yarn Full Inspection Form  |  Rev.00  |  Date: 02-Jan-2025", sub_style)]]
    sub_tbl  = Table(sub_data, colWidths=[180*mm])
    sub_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), BLUE2),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(sub_tbl)
    story.append(Spacer(1, 4*mm))

    # Info row
    def info_cell(label, value):
        return [Paragraph(label, label_style), Paragraph(str(value), val_style)]

    info_data = [
        [Paragraph("LINE", label_style),     Paragraph(str(record.get("line","")),     val_style),
         Paragraph("SHIFT", label_style),    Paragraph(str(record.get("shift","")),    val_style),
         Paragraph("DATE", label_style),     Paragraph(str(record.get("date","")),     val_style),
         Paragraph("TIME", label_style),     Paragraph(str(record.get("time","")),     val_style)],
        [Paragraph("WO", label_style),       Paragraph(str(record.get("wo","")),       val_style),
         Paragraph("ITEM", label_style),     Paragraph(str(record.get("item","")),     val_style),
         Paragraph("ITEM NAME", label_style),Paragraph(str(record.get("item_name","")),val_style),
         Paragraph("OPERATOR", label_style), Paragraph(str(record.get("operator","")), val_style)],
    ]
    info_tbl = Table(info_data, colWidths=[22*mm,30*mm,22*mm,20*mm,20*mm,30*mm,28*mm,28*mm])
    info_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,-1), LGRAY),
        ('BACKGROUND', (2,0), (2,-1), LGRAY),
        ('BACKGROUND', (4,0), (4,-1), LGRAY),
        ('BACKGROUND', (6,0), (6,-1), LGRAY),
        ('GRID',   (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(info_tbl)
    story.append(Spacer(1, 4*mm))

    colors_list = record.get("colors", [])
    positions   = record.get("positions", [])
    test_data   = record.get("test_data", {})

    TESTS_LEFT  = [("dtex","DTEX"), ("total_dtex","TOTAL DTEX"),
                   ("boiling_shrinkage","BOILING SHRINKAGE (AVE)"),
                   ("thickness","THICKNESS"), ("tensile","TENSILE (AVE)")]
    TESTS_RIGHT = [("yarn_wrap","YARN WRAP PER METER"), ("air_shrinkage","AIR SHRINKAGE"),
                   ("width","WIDTH"), ("elongation","ELONGATION (AVE)")]

    for pos in positions:
        pd = test_data.get(pos, {})
        story.append(Paragraph(f"Position: {pos}", ParagraphStyle('pos', fontSize=9,
                     fontName='Helvetica-Bold', textColor=BLUE, spaceAfter=2*mm)))

        # Build test table
        col_w = [40*mm] + [28*mm]*len(colors_list)
        header_row = [Paragraph("TEST", label_style)] + \
                     [Paragraph(c, label_style) for c in colors_list]

        rows = [header_row]
        for key, label in TESTS_LEFT:
            unit = UNITS.get(key, "")
            lbl  = Paragraph(f"{label}\n{unit}", label_style)
            if key in ("total_dtex", "yarn_wrap"):
                val = pd.get(key, "")
                row = [lbl] + [Paragraph(str(val) if val is not None else "-", val_style)] + \
                      [""] * (len(colors_list)-1)
            else:
                d = pd.get(key, {})
                row = [lbl] + [Paragraph(str(d.get(c,"") if d.get(c) is not None else "-"), val_style)
                               for c in colors_list]
            rows.append(row)

        # Separator
        rows.append([Paragraph("RIGHT SIDE TESTS", label_style)] + [""]*len(colors_list))

        for key, label in TESTS_RIGHT:
            unit = UNITS.get(key, "")
            lbl  = Paragraph(f"{label}\n{unit}", label_style)
            if key == "yarn_wrap":
                val = pd.get(key, "")
                row = [lbl] + [Paragraph(str(val) if val is not None else "-", val_style)] + \
                      [""] * (len(colors_list)-1)
            else:
                d = pd.get(key, {})
                row = [lbl] + [Paragraph(str(d.get(c,"") if d.get(c) is not None else "-"), val_style)
                               for c in colors_list]
            rows.append(row)

        tbl = Table(rows, colWidths=col_w)
        tbl.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BLUE2),
            ('TEXTCOLOR',  (0,0), (-1,0), WHITE),
            ('BACKGROUND', (0,6), (-1,6), LGRAY),
            ('GRID',   (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING',    (0,0), (-1,-1), 3),
            ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ('FONTSIZE', (0,0), (-1,-1), 8),
        ]))
        story.append(tbl)
        story.append(Spacer(1, 4*mm))

    # SCI/SCE
    sci = record.get("sci", {})
    spool = record.get("spool_no", "")
    if sci:
        story.append(Paragraph(f"SCI / SCE  (Spool #: {spool})", ParagraphStyle('sci',
                     fontSize=9, fontName='Helvetica-Bold', textColor=BLUE, spaceAfter=2*mm)))
        sci_row = [[Paragraph(c, label_style),
                    Paragraph(str(sci.get(c,"-")), val_style)] for c in colors_list]
        if sci_row:
            flat = []
            for pair in sci_row:
                flat.extend(pair)
            sci_tbl = Table([flat], colWidths=[25*mm,30*mm]*len(colors_list))
            sci_tbl.setStyle(TableStyle([
                ('GRID',   (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
                ('BACKGROUND', (0,0), (0,-1), LGRAY),
                ('TOPPADDING',    (0,0), (-1,-1), 3),
                ('BOTTOMPADDING', (0,0), (-1,-1), 3),
            ]))
            story.append(sci_tbl)
        story.append(Spacer(1, 4*mm))

    # Comments
    comments = record.get("comments", "")
    if comments:
        story.append(Paragraph("Comments", ParagraphStyle('cmtlbl', fontSize=9,
                     fontName='Helvetica-Bold', textColor=BLUE, spaceAfter=2*mm)))
        story.append(Paragraph(comments, val_style))
        story.append(Spacer(1, 4*mm))

    # Tolerance check / verified
    tol_data = [[
        Paragraph("TOLERANCE VALUE CHECK", label_style),
        Paragraph("All tests conducted per standard procedure. Results verified for accuracy and compliance.", val_style),
        Paragraph(f"Verified by: {record.get('verified_by','')}", label_style),
    ]]
    tol_tbl = Table(tol_data, colWidths=[45*mm, 100*mm, 35*mm])
    tol_tbl.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (0,0), LGRAY),
        ('BACKGROUND', (2,0), (2,0), LGRAY),
        ('GRID',   (0,0), (-1,-1), 0.5, colors.HexColor("#e2e8f0")),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('TOPPADDING',    (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(tol_tbl)

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()
