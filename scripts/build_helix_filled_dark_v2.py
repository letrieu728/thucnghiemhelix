# -*- coding: utf-8 -*-
"""16-slide academic template: replication + extension report.
16:9, Navy #0F2C59 / White / Accent #0284C7. Placeholders only, no fabricated data."""
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE, MSO_CONNECTOR
from pptx.oxml.ns import qn
import os

BG_DARK = RGBColor(0x0A, 0x1A, 0x30)
CARD = RGBColor(0x12, 0x29, 0x4A)
CARD2 = RGBColor(0x0F, 0x24, 0x40)
CARD3 = RGBColor(0x14, 0x36, 0x5C)
ROW = RGBColor(0x0F, 0x24, 0x40)
TEXT = RGBColor(0xE2, 0xE8, 0xF0)
MUTED = RGBColor(0x94, 0xA3, 0xB8)
CARDLINE = RGBColor(0x2A, 0x4E, 0x7E)
BLOCK = RGBColor(0x1B, 0x4A, 0x8A)
PANEL = RGBColor(0x13, 0x2F, 0x58)
SKYBLUE = RGBColor(0x38, 0xBD, 0xF8)
PHOLDER = RGBColor(0x0D, 0x20, 0x38)
ACCENT = RGBColor(0x02, 0x84, 0xC7)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
SKY = RGBColor(0xBA, 0xE6, 0xFD)
AMBER_BG = RGBColor(0xFE, 0xF3, 0xC7)
FONT = "Be Vietnam Pro"

W, H = 13.33, 7.5
ML = 0.55  # left margin
CW = 12.23  # content width

prs = Presentation()
prs.slide_width = Inches(W)
prs.slide_height = Inches(H)
BLANK = prs.slide_layouts[6]


def slide_new(variant="chip"):
    s = prs.slides.add_slide(BLANK)
    s.background.fill.solid()
    s.background.fill.fore_color.rgb = BG_DARK
    BG_VARIANTS[variant](s)
    return s


def rect(s, x, y, w, h, fill, line=None, line_w=1.0, shape=MSO_SHAPE.RECTANGLE, radius=None):
    sp = s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.fill.solid()
    sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(line_w)
    sp.shadow.inherit = False
    if radius is not None and shape == MSO_SHAPE.ROUNDED_RECTANGLE:
        try:
            sp.adjustments[0] = radius
        except Exception:
            pass
    sp.text_frame.word_wrap = True
    return sp


def _set_runs(p, runs, align):
    p.alignment = align
    for text, size, bold, color in runs:
        r = p.add_run()
        r.text = text
        r.font.size = Pt(size)
        r.font.bold = bold
        r.font.color.rgb = color
        r.font.name = FONT


def txt(s, x, y, w, h, paras, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, space_after=6, line_spacing=1.05):
    """paras: list of paragraphs; each paragraph is list of (text,size,bold,color) runs,
    or a plain string (default 16/TEXT)."""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, para in enumerate(paras):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_after = Pt(space_after)
        p.line_spacing = line_spacing
        if isinstance(para, str):
            _set_runs(p, [(para, 16, False, TEXT)], align)
        else:
            _set_runs(p, para, align)
    return tb


def header(s, kicker, title, num):
    txt(s, ML, 0.38, CW, 0.3, [[(kicker.upper(), 11, True, SKYBLUE)]])
    txt(s, ML, 0.66, CW, 0.6, [[(title, 27, True, WHITE)]])
    rect(s, ML, 1.32, CW, 0.045, ACCENT)
    c = rect(s, 12.45, 6.95, 0.36, 0.36, ACCENT, shape=MSO_SHAPE.OVAL)
    tf = c.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = str(num)
    r.font.size = Pt(12); r.font.bold = True; r.font.color.rgb = WHITE; r.font.name = FONT


def placeholder(s, x, y, w, h, label, sub=""):
    sp = rect(s, x, y, w, h, PHOLDER, line=ACCENT, line_w=1.25,
              shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
    paras = [[(label, 15, True, WHITE)]]
    if sub:
        paras.append([(sub, 11, False, MUTED)])
    txt(s, x + 0.25, y + h / 2 - 0.35, w - 0.5, 0.7, paras, align=PP_ALIGN.CENTER, space_after=2)
    return sp


def card(s, x, y, w, h, fill=CARD, line=CARDLINE):
    return rect(s, x, y, w, h, fill, line=line, line_w=1.0,
                shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.07)


def bullets(s, x, y, w, h, items, size=15, gap=8):
    paras = []
    for it in items:
        paras.append([("•  ", size, True, SKYBLUE), (it, size, False, TEXT)])
    txt(s, x, y, w, h, paras, space_after=gap)


def style_table(table, col_widths, header=True, font_size=13):
    for j, cw in enumerate(col_widths):
        table.columns[j].width = Inches(cw)
    for i, row in enumerate(table.rows):
        for cell in row.cells:
            cell.margin_left = Inches(0.12)
            cell.margin_right = Inches(0.12)
            cell.margin_top = Inches(0.06)
            cell.margin_bottom = Inches(0.06)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            if header and i == 0:
                cell.fill.solid(); cell.fill.fore_color.rgb = BLOCK
            elif i % 2 == 0:
                cell.fill.solid(); cell.fill.fore_color.rgb = CARD
            else:
                cell.fill.solid(); cell.fill.fore_color.rgb = ROW
            for p in cell.text_frame.paragraphs:
                p.line_spacing = 1.0
                for r in p.runs:
                    r.font.name = FONT
                    r.font.size = Pt(font_size)
                    r.font.bold = (header and i == 0)
                    r.font.color.rgb = WHITE if (header and i == 0) else TEXT


def add_table(s, x, y, w, h, data, col_widths, font_size=13):
    rows, cols = len(data), len(data[0])
    gf = s.shapes.add_table(rows, cols, Inches(x), Inches(y), Inches(w), Inches(h))
    table = gf.table
    for i, row in enumerate(data):
        for j, val in enumerate(row):
            table.cell(i, j).text = val
    style_table(table, col_widths, font_size=font_size)
    return gf

# ------- Native editable-shape backgrounds (Canva-friendly) -------
# Every motif is a real PowerPoint shape / text box (named "BG ..."), so after
# importing the PPTX into Canva each element can be moved, recoloured or
# deleted individually. No flat background picture is used.
# All background text uses only characters present in Be Vietnam Pro
# (verified against the font cmap: no Greek, no arrows, no check glyphs).
import math as _math
import random as _random

TINT = RGBColor(0xE9, 0xEF, 0xF6)      # light navy tint for content slides
NAVY2 = RGBColor(0x12, 0x29, 0x4A)     # cover glow outer
NAVY3 = RGBColor(0x1A, 0x46, 0x8A)     # cover glow inner
CHIPFILL = RGBColor(0x13, 0x36, 0x6A)  # cover MODEL/HARNESS chips
COVERBG = BG_DARK                      # cover background, for the BUILD tag backing
FAINT = RGBColor(0x2A, 0x4E, 0x7E)     # faint dots on navy
LINEC = RGBColor(0x2A, 0x4E, 0x7E)     # motif lines on tint
NODEC = RGBColor(0x7D, 0xD3, 0xFC)     # motif nodes on tint
TRACEC = RGBColor(0x4A, 0x6F, 0xA5)    # circuits on navy
CODEBG = RGBColor(0x0D, 0x20, 0x38)    # code window on navy
PILLBG = RGBColor(0x0D, 0x2A, 0x52)    # preset pills on navy
MOTIFBG = RGBColor(0x12, 0x29, 0x4A)   # chip / code window on tint


def _name(sp, name):
    try:
        sp.name = name
    except Exception:
        pass
    return sp


def bg_rect(s, x, y, w, h, fill, line=None, line_w=1.0, shape=MSO_SHAPE.RECTANGLE, radius=None, name="BG shape"):
    return _name(rect(s, x, y, w, h, fill, line=line, line_w=line_w, shape=shape, radius=radius), name)


def bg_line(s, x1, y1, x2, y2, color, w_pt, name="BG line"):
    conn = s.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    conn.line.color.rgb = color
    conn.line.width = Pt(w_pt)
    conn.shadow.inherit = False
    return _name(conn, name)


def bg_oval(s, cx, cy, d, fill=None, line=None, line_w=1.0, name="BG node"):
    sp = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(cx - d / 2), Inches(cy - d / 2), Inches(d), Inches(d))
    if fill is None:
        sp.fill.background()
    else:
        sp.fill.solid()
        sp.fill.fore_color.rgb = fill
    if line is None:
        sp.line.fill.background()
    else:
        sp.line.color.rgb = line
        sp.line.width = Pt(line_w)
    sp.shadow.inherit = False
    return _name(sp, name)


def bg_diamond(s, cx, cy, d, line, line_w=1.25, name="BG diamond"):
    sp = s.shapes.add_shape(MSO_SHAPE.DIAMOND, Inches(cx - d / 2), Inches(cy - d / 2), Inches(d), Inches(d))
    sp.fill.background()
    sp.line.color.rgb = line
    sp.line.width = Pt(line_w)
    sp.shadow.inherit = False
    return _name(sp, name)


def bg_tri(s, cx, cy, w, h, fill, rotation, name="BG arrowhead"):
    sp = s.shapes.add_shape(MSO_SHAPE.ISOSCELES_TRIANGLE, Inches(cx - w / 2), Inches(cy - h / 2), Inches(w), Inches(h))
    sp.fill.solid()
    sp.fill.fore_color.rgb = fill
    sp.line.fill.background()
    sp.shadow.inherit = False
    sp.rotation = rotation
    return _name(sp, name)


def bg_arc(s, x, y, w, h, start, end, color, w_pt, name="BG arc"):
    sp = s.shapes.add_shape(MSO_SHAPE.ARC, Inches(x), Inches(y), Inches(w), Inches(h))
    try:
        sp.adjustments[0] = start
        sp.adjustments[1] = end
    except Exception:
        pass
    sp.fill.background()
    sp.line.color.rgb = color
    sp.line.width = Pt(w_pt)
    sp.shadow.inherit = False
    return _name(sp, name)


def bg_text(s, x, y, w, h, text, size, color, bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.TOP, name="BG text"):
    return _name(txt(s, x, y, w, h, [[(text, size, bold, color)]], align=align, anchor=anchor, space_after=0), name)


def arc_head(s, cx, cy, rx, ry, deg, color, size=0.17, name="BG arrowhead"):
    th = _math.radians(deg)
    px = cx + rx * _math.cos(th)
    py = cy + ry * _math.sin(th)
    tx = rx * _math.sin(th)
    ty = -ry * _math.cos(th)
    rot = _math.degrees(_math.atan2(tx, -ty))
    return bg_tri(s, px, py, size, size * 0.85, color, rot, name)


def bg_check(s, cx, cy, size, color, w_pt=2.25, name="BG check"):
    bg_line(s, cx - size * 0.45, cy + size * 0.05, cx - size * 0.12, cy + size * 0.38, color, w_pt, name)
    bg_line(s, cx - size * 0.12, cy + size * 0.38, cx + size * 0.5, cy - size * 0.38, color, w_pt, name)


def bg_bottom_strip(s, text, x0=ML, x1=12.20, cx=6.67):
    bg_line(s, x0, 7.33, x1, 7.33, LINEC, 1.5, "BG bottom line")
    n = 5
    for i in range(n):
        nx = x0 + 0.3 + (x1 - x0 - 0.6) * i / (n - 1)
        bg_oval(s, nx, 7.33, 0.09, fill=None, line=NODEC, line_w=1.25, name="BG bottom node")
    bg_text(s, cx - 3.6, 7.02, 7.2, 0.26, text, 10, SKYBLUE, name="BG bottom text")


def bg_left_trace(s, style="oval"):
    bg_line(s, 0.30, 1.60, 0.30, 6.80, LINEC, 1.5, "BG left trace")
    for ny in (2.6, 4.2, 5.8):
        if style == "diamond":
            bg_diamond(s, 0.30, ny, 0.13, NODEC, name="BG left node")
        elif style == "check":
            bg_check(s, 0.30, ny, 0.17, SKYBLUE, name="BG left check")
        elif style == "square":
            bg_rect(s, 0.24, ny - 0.06, 0.12, 0.12, None if False else MOTIFBG, line=NODEC, line_w=1.25, name="BG left node")
        else:
            bg_oval(s, 0.30, ny, 0.11, fill=None, line=NODEC, line_w=1.25, name="BG left node")
        bg_line(s, 0.37, ny, 0.47, ny, LINEC, 1.25, "BG left tick")


def bg_chip(s, cx=12.05, cy=0.62):
    bx, by, bw, bh = cx - 0.42, cy - 0.37, 0.84, 0.74
    for i in range(3):
        px = bx + 0.18 + i * 0.24
        bg_rect(s, px - 0.017, by - 0.09, 0.035, 0.09, NODEC, name="BG chip pin")
        bg_rect(s, px - 0.017, by + bh, 0.035, 0.09, NODEC, name="BG chip pin")
        py = by + 0.17 + i * 0.20
        bg_rect(s, bx - 0.09, py - 0.017, 0.09, 0.035, NODEC, name="BG chip pin")
        bg_rect(s, bx + bw, py - 0.017, 0.09, 0.035, NODEC, name="BG chip pin")
    bg_rect(s, bx, by, bw, bh, MOTIFBG, line=NODEC, line_w=1.5, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.10, name="BG chip")
    bg_text(s, bx, by + 0.17, bw, 0.4, "</>", 16, WHITE, name="BG chip text")
    # mini network, far top-right corner (fully inside the slide)
    pts = [(12.72, 0.30), (12.95, 0.55), (12.68, 0.82), (13.02, 0.98), (12.85, 0.18)]
    for (ax, ay), (bx2, by2) in [((12.72, 0.30), (12.95, 0.55)), ((12.95, 0.55), (12.68, 0.82)),
                                 ((12.68, 0.82), (13.02, 0.98)), ((12.72, 0.30), (12.85, 0.18))]:
        bg_line(s, ax, ay, bx2, by2, LINEC, 1.0, "BG network line")
    for (px, py) in pts:
        bg_oval(s, px, py, 0.08, fill=NODEC, name="BG network node")
    # circuit traces
    bg_rect(s, 12.60, 1.06, 0.55, 0.03, LINEC, name="BG circuit")
    bg_rect(s, 12.60, 0.86, 0.03, 0.23, LINEC, name="BG circuit")
    bg_oval(s, 12.615, 0.86, 0.09, fill=None, line=NODEC, line_w=1.25, name="BG circuit pad")


def bg_code(s, x=10.55, y=0.28, w=2.45, h=0.82, dark=False):
    fill = CODEBG if dark else MOTIFBG
    line = RGBColor(0x3B, 0x5B, 0x82) if dark else NODEC
    bg_rect(s, x, y, w, h, fill, line=line, line_w=1.25, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.10, name="BG code window")
    for i, dc in enumerate([RGBColor(0xF8, 0x71, 0x71), RGBColor(0xFB, 0xBF, 0x24), RGBColor(0x34, 0xD3, 0x99)]):
        bg_oval(s, x + 0.16 + i * 0.17, y + 0.13, 0.08, fill=dc, name="BG code dot")
    bg_text(s, x + 0.10, y + 0.30, 0.40, 0.26, ">_", 10, SKY if dark else SKYBLUE, name="BG code prompt")
    bars = [(1.40, SKY if dark else RGBColor(0x93, 0xC5, 0xE8)),
            (0.95, ACCENT),
            (1.60, SKY if dark else RGBColor(0x93, 0xC5, 0xE8)),
            (0.75, NODEC)]
    for i, (bw, bc) in enumerate(bars):
        bg_rect(s, x + 0.52, y + 0.32 + i * 0.13, bw, 0.05, bc, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5, name="BG code line")


def bg_pipeline(s, x0=10.55, y=0.42):
    for i in range(4):
        px = x0 + i * 0.62
        bg_rect(s, px, y, 0.34, 0.34, BLOCK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.18, name="BG pipeline step")
        bg_text(s, px, y + 0.045, 0.34, 0.26, str(i + 1), 12, WHITE, name="BG pipeline number")
        if i < 3:
            bg_tri(s, px + 0.48, y + 0.17, 0.15, 0.13, SKYBLUE, 90, "BG pipeline arrow")
    bg_line(s, x0 + 2.34, y + 0.17, 13.12, y + 0.17, LINEC, 1.5, "BG pipeline line")
    bg_oval(s, 13.06, y + 0.17, 0.10, fill=None, line=NODEC, line_w=1.25, name="BG pipeline node")


def bg_branch(s):
    bg_line(s, 10.15, 0.95, 13.05, 0.95, LINEC, 1.75, "BG branch main")
    bg_line(s, 10.15, 0.95, 10.75, 0.40, LINEC, 1.75, "BG branch fork")
    bg_line(s, 10.75, 0.40, 13.05, 0.40, LINEC, 1.75, "BG branch line")
    bg_line(s, 12.35, 0.40, 12.90, 0.95, LINEC, 1.75, "BG branch merge")
    for (px, py) in [(10.15, 0.95), (11.50, 0.95), (12.90, 0.95), (11.50, 0.40), (12.35, 0.40)]:
        bg_oval(s, px, py, 0.14, fill=BG_DARK, line=NODEC, line_w=1.5, name="BG branch node")


def bg_miniloop(s, cx=12.05, cy=0.68, rx=0.85, ry=0.42):
    bx, by = cx - rx, cy - ry
    bg_arc(s, bx, by, 2 * rx, 2 * ry, 100, 260, NODEC, 1.75, "BG loop arc")
    bg_arc(s, bx, by, 2 * rx, 2 * ry, 280, 360, NODEC, 1.75, "BG loop arc")
    bg_arc(s, bx, by, 2 * rx, 2 * ry, 0, 80, NODEC, 1.75, "BG loop arc")
    arc_head(s, cx, cy, rx, ry, 260, NODEC, 0.15, "BG loop arrowhead")
    arc_head(s, cx, cy, rx, ry, 80, NODEC, 0.15, "BG loop arrowhead")
    bg_text(s, cx - 0.4, cy - 0.13, 0.8, 0.26, "M-H", 11, WHITE, name="BG loop label")


def bg_cover(s):
    # Wide loop frame: a rounded-rectangle outline around the MODEL/HARNESS
    # chips, wider than the chips, so no line or arrowhead ever passes under
    # a chip's text box.
    bg_oval(s, 10.35, 3.62, 5.4, fill=NAVY2, name="BG glow outer")
    sp = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(8.15), Inches(1.55), Inches(4.40), Inches(4.10))
    sp.fill.solid(); sp.fill.fore_color.rgb = NAVY3; sp.line.fill.background(); sp.shadow.inherit = False
    _name(sp, "BG glow inner")
    # node network, right zone (deterministic; skips chip rectangles)
    rnd = _random.Random(7)
    keep_out = [(8.70, 1.40, 3.30, 1.15), (8.70, 4.80, 3.30, 1.15), (10.60, 0.17, 2.65, 1.10)]
    pts = []
    while len(pts) < 13:
        px, py = rnd.uniform(8.0, 13.10), rnd.uniform(0.35, 7.05)
        if any(kx - 0.1 <= px <= kx + kw + 0.1 and ky - 0.1 <= py <= ky + kh + 0.1 for (kx, ky, kw, kh) in keep_out):
            continue
        pts.append((px, py))
    pairs = []
    for i in range(len(pts)):
        for j in range(i + 1, len(pts)):
            d = _math.hypot(pts[i][0] - pts[j][0], pts[i][1] - pts[j][1])
            if d < 1.9:
                pairs.append((d, i, j))
    pairs.sort()
    for _, i, j in pairs[:16]:
        bg_line(s, pts[i][0], pts[i][1], pts[j][0], pts[j][1], TRACEC, 0.75, "BG network line")
    for (px, py) in pts:
        bg_oval(s, px, py, rnd.choice([0.06, 0.08, 0.10]), fill=SKY, name="BG network node")
    # circuit trace, bottom-right corner (fully inside the slide)
    bg_rect(s, 12.87, 6.00, 0.30, 0.03, TRACEC, name="BG circuit")
    bg_rect(s, 12.87, 5.60, 0.03, 0.43, TRACEC, name="BG circuit")
    bg_oval(s, 12.885, 5.60, 0.10, fill=None, line=SKY, line_w=1.25, name="BG circuit pad")
    # loop frame: rounded-rectangle OUTLINE, wider than the chips, so no line
    # ever passes under a MODEL/HARNESS chip. (ARC shapes with 0/360-degree
    # adjustments render unreliably in LibreOffice, so no arcs are used here.)
    fr = s.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(7.75), Inches(1.25), Inches(5.20), Inches(4.85))
    fr.fill.background()
    fr.line.color.rgb = SKY
    fr.line.width = Pt(3.0)
    fr.shadow.inherit = False
    try:
        fr.adjustments[0] = 0.20
    except Exception:
        pass
    _name(fr, "BG loop frame")
    # 3 arrowheads, one per phase (BUILD -> UPDATE -> REBUILD), all clockwise:
    # left edge up, bottom edge left, right edge down. Each sits centred on
    # the frame line, clear of the chips and of the BUILD tag.
    bg_tri(s, 7.75, 2.75, 0.30, 0.26, SKY, 0, "BG loop arrowhead")
    bg_tri(s, 9.30, 6.10, 0.30, 0.26, SKY, 270, "BG loop arrowhead")
    bg_tri(s, 12.95, 4.50, 0.30, 0.26, SKY, 180, "BG loop arrowhead")
    bg_text(s, 7.80, 3.42, 0.95, 0.4, "UPDATE", 12, SKY, name="BG loop label")
    bg_text(s, 11.95, 3.42, 0.95, 0.4, "REBUILD", 12, SKY, name="BG loop label")
    # BUILD tag centred on the bottom edge (cycle order: BUILD -> UPDATE -> REBUILD);
    # the tag's backing fill matches the slide background so it sits cleanly on the frame line
    bg_rect(s, 9.90, 5.98, 0.90, 0.26, COVERBG, name="BG loop BUILD tag")
    bg_text(s, 9.90, 5.99, 0.90, 0.24, "BUILD", 11, SKY, name="BG loop BUILD label")
    for (cy, name, sub) in [(1.55, "MODEL", "M_t  —  weights"), (4.95, "HARNESS", "Phi_t  —  96 ports")]:
        bg_rect(s, 8.85, cy, 3.00, 0.85, CHIPFILL, line=SKY, line_w=1.5, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12, name="BG chip " + name)
        _name(txt(s, 8.85, cy + 0.10, 3.00, 0.65,
                  [[(name, 20, True, WHITE)], [(sub, 10.5, False, SKY)]],
                  align=PP_ALIGN.CENTER, space_after=2, line_spacing=1.0), "BG chip text " + name)
    # code window, top-right
    bg_code(s, 10.75, 0.28, 2.35, 0.80, dark=True)
    # harness preset pills (Builder preset names; the 4 used in the experiments)
    pills = [("Minimal", 1.05), ("Pi Mono", 1.00), ("Hermes", 1.00), ("OpenCode", 1.15)]
    total = sum(w for _, w in pills) + 0.13 * (len(pills) - 1)
    px = 10.35 - total / 2
    for label, pw in pills:
        bg_rect(s, px, 6.32, pw, 0.34, PILLBG, line=SKY, line_w=1.0, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5, name="BG preset pill")
        bg_text(s, px, 6.36, pw, 0.26, label, 10.5, RGBColor(0xDB, 0xEA, 0xFE), name="BG preset text")
        px += pw + 0.13
    bg_text(s, 7.95, 6.82, 4.90, 0.3, "BUILD / UPDATE / REBUILD  —  model-harness co-evolution", 10.5, SKY, name="BG cover caption")
    # sparse faint dots, left zone
    for (dx, dy, dd) in [(1.20, 0.70, 0.06), (2.80, 1.10, 0.08), (0.80, 4.20, 0.07), (3.60, 5.90, 0.06),
                         (1.90, 6.60, 0.08), (4.40, 3.00, 0.05), (0.60, 2.20, 0.06), (5.20, 6.90, 0.07)]:
        bg_oval(s, dx, dy, dd, fill=FAINT, name="BG dot")

def bg_variant_chip(s):
    bg_chip(s)
    bg_left_trace(s, "oval")
    bg_bottom_strip(s, "BUILD / UPDATE / REBUILD")


def bg_variant_code(s):
    bg_code(s)
    bg_left_trace(s, "square")
    bg_bottom_strip(s, "Z_t = (M_t, Phi_t)")


def bg_variant_pipeline(s):
    bg_pipeline(s)
    bg_left_trace(s, "check")
    bg_bottom_strip(s, "REPLICATE / VERIFY / COMPARE")


def bg_variant_branch(s):
    bg_branch(s)
    bg_left_trace(s, "diamond")
    bg_bottom_strip(s, "BRANCH / TEST / MERGE")


def bg_variant_loop(s):
    bg_miniloop(s)
    bg_left_trace(s, "oval")
    bg_bottom_strip(s, "BUILD / UPDATE / REBUILD")


def bg_variant_closing(s):
    bg_chip(s)
    bg_bottom_strip(s, "BUILD / UPDATE / REBUILD", x0=6.30, x1=12.20, cx=9.25)


BG_VARIANTS = {
    "cover": bg_cover,
    "chip": bg_variant_chip,
    "code": bg_variant_code,
    "pipeline": bg_variant_pipeline,
    "branch": bg_variant_branch,
    "loop": bg_variant_loop,
    "closing": bg_variant_closing,
}


# Filled HELIX deck: same 16-slide blueprint + backgrounds as
# build_blueprint_pptx_v3.py, with real verified HELIX numbers, tables and
# images. Framing (Triệu, 16/11): replication = rerunning the AUTHORS'
# artifacts (CLI assembly, Builder, real-harness runs); LoRA = the group's
# extension (the part the authors never did, §9.5). Every number comes from
# the slide kit (06_Dung-rieng-cho-slide/), the evidence pack, or MEMORY.md
# rebuild-step records. Combined with the v3 head+helpers.
from PIL import Image as _PILImage

KIT = os.path.expanduser("~/workspace/helix-slide-kit/02_Bieu-do-va-anh")
KIT6 = os.path.expanduser("~/workspace/helix-slide-kit/06_Dung-rieng-cho-slide/bieu-do")
CH = os.path.expanduser("~/workspace/your_files/blueprint-16-slide/charts-helix-toi")
EV = os.path.expanduser("~/workspace/your_files/bang-chung-thuc-nghiem-helix/01_anh")
PAPERFIG = os.path.expanduser("~/workspace/goals/helix-and-ai-copy-course-reports/files/blueprint-16-slide/paper-figs")


def add_pic(s, path, x, y, w, h, caption=None, frame=True):
    if frame:
        card(s, x, y, w, h)
    im = _PILImage.open(path)
    iw, ih = im.size
    pad = 0.08
    ah = h - 2 * pad - (0.30 if caption else 0)
    aw = w - 2 * pad
    scale = min(aw / iw, ah / ih)
    pw, ph = iw * scale, ih * scale
    px = x + (w - pw) / 2
    py = y + pad + (ah - ph) / 2
    s.shapes.add_picture(path, Inches(px), Inches(py), Inches(pw), Inches(ph))
    if caption:
        txt(s, x + 0.15, y + h - 0.32, w - 0.3, 0.28, [[(caption, 11, False, MUTED)]],
            align=PP_ALIGN.CENTER)


def notes(s, text):
    s.notes_slide.notes_text_frame.text = text


def flow3(s, x, y, w, labels, highlight=-1):
    cw3 = (w - 2 * 0.35) / 3
    for i, lab in enumerate(labels):
        cx = x + i * (cw3 + 0.35)
        fill = ACCENT if i == highlight else CARD
        tcol = WHITE if i == highlight else TEXT
        card(s, cx, y, cw3, 1.2, fill=fill, line=ACCENT if i == highlight else CARDLINE)
        txt(s, cx + 0.08, y + 0.18, cw3 - 0.16, 0.85, [[(lab, 12.5, True, tcol)]],
            align=PP_ALIGN.CENTER, line_spacing=1.05)
        if i < 2:
            txt(s, cx + cw3, y + 0.35, 0.35, 0.4, [[("→", 18, True, ACCENT)]],
                align=PP_ALIGN.CENTER)


# ======================================================================
# REBUILD 17/11/2026 (Triệu) — DARK-ONLY: whole deck restructured per the
# teacher's slide rules (inferred from feedback on HTTT groups 3+4):
# context -> problem statement -> related work -> gap -> RQs -> original
# method -> method limits -> proposal -> verification design -> replication
# experiments -> comparison -> extension results -> deep analysis ->
# limits/future -> conclusion. 22 slides since 20/11/2026 (v2 + O6 sync: +1 slide 18
# EVOLUTION (6 buoc + chuong trinh $6), LIEN HE -> 19, limits -> 20, conclusion -> 21,
# thanks -> 22; totals 1,262 -> 1,581, 3 -> 4 LoRA, 25 -> 74 record, 50 -> 65 bai;
# filenames keep "...16-slide...".
# NOT in the light deck (still 16 slides). Do not regenerate this file
# from build_helix_filled.py / build_dark_filled.py without re-applying.
# Every number below is reused from the previous verified deck / Speaker
# Notes / evidence pack; no new numbers. Related work: paper §8 only
# (verified against the fresh arXiv HTML, 17/11/2026).
# ======================================================================

def add_pic_rect(s, path, x, y, w, h, caption=None, frame=True):
    """Like add_pic, but returns the placed image rect (px, py, pw, ph) so
    slide-shape annotations can point at features inside the image."""
    if frame:
        card(s, x, y, w, h)
    im = _PILImage.open(path)
    iw, ih = im.size
    pad = 0.08
    ah = h - 2 * pad - (0.30 if caption else 0)
    aw = w - 2 * pad
    scale = min(aw / iw, ah / ih)
    pw, ph = iw * scale, ih * scale
    px = x + (w - pw) / 2
    py = y + pad + (ah - ph) / 2
    s.shapes.add_picture(path, Inches(px), Inches(py), Inches(pw), Inches(ph))
    if caption:
        txt(s, x + 0.15, y + h - 0.32, w - 0.3, 0.28, [[(caption, 11, False, MUTED)]],
            align=PP_ALIGN.CENTER)
    return (px, py, pw, ph)


def formula(s, x, y, w, h, lines, align=PP_ALIGN.CENTER, space_after=8, line_spacing=1.15):
    """Retyped formulas as native text (never screenshots). Each line is a
    list of (text, size, bold, color, base); base is None | 'sub' | 'sup'."""
    tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        p.line_spacing = line_spacing
        for (text, size, bold, color, base) in line:
            r = p.add_run()
            r.text = text
            r.font.size = Pt(size)
            r.font.bold = bold
            r.font.color.rgb = color
            r.font.name = FONT
            if base:
                rPr = r._r.get_or_add_rPr()
                rPr.set('baseline', '-25000' if base == 'sub' else '30000')
    return tb


def marker(s, cx, cy, n, d=0.3):
    """Numbered pointer placed ON an image by the group (a slide shape, not
    part of the image) so the audience knows where to look."""
    c = rect(s, cx - d / 2, cy - d / 2, d, d, RGBColor(0xF5, 0x9E, 0x0B), shape=MSO_SHAPE.OVAL)
    tf = c.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = str(n)
    r.font.size = Pt(13)
    r.font.bold = True
    r.font.color.rgb = WHITE
    r.font.name = FONT
    return c


def arrow_shape(s, x, y, w, h, fill=ACCENT):
    sp = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x), Inches(y), Inches(w), Inches(h))
    sp.fill.solid()
    sp.fill.fore_color.rgb = fill
    sp.line.fill.background()
    sp.shadow.inherit = False
    return sp


def num_disc(s, x, y, d, text, fill=ACCENT, size=15):
    c = rect(s, x, y, d, d, fill, shape=MSO_SHAPE.OVAL)
    tf = c.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    r = p.add_run()
    r.text = text
    r.font.size = Pt(size)
    r.font.bold = True
    r.font.color.rgb = WHITE
    r.font.name = FONT
    return c


AMBER = RGBColor(0xF5, 0x9E, 0x0B)
AMBER_LT = RGBColor(0xFB, 0xBF, 0x24)

# ---------------- Slide 1: Cover ----------------
s = slide_new("cover")
txt(s, ML, 1.55, 6.8, 0.35, [[("BÁO CÁO TÁI THỰC NGHIỆM VÀ MỞ RỘNG  •  KHAI PHÁ DỮ LIỆU", 11, True, SKY)]])
txt(s, ML, 2.0, 6.8, 1.9, [[("HELIX:\nĐồng tiến hóa\nmodel–harness", 36, True, WHITE)]], line_spacing=1.05)
txt(s, ML, 4.1, 6.8, 0.7, [[("HELIX — Model–Harness Co-evolution", 20, False, WHITE)], [("arXiv:2608.13951  •  Chủ đề 1 – Bài 9", 14, False, SKY)]])
rect(s, ML, 4.9, 0.7, 0.05, ACCENT)
txt(s, ML, 5.15, 6.8, 0.9, [[("Nhóm 19: Nguyễn Sỹ Việt — 24022758  •  Lê Quốc Triệu — 24022750", 14, True, WHITE)], [("Khai phá dữ liệu  •  PGS.TS Hà Quang Thụy  •  Học kỳ I, 2026–2027", 13, False, SKY)]])
txt(s, ML, 6.25, 6.8, 0.3, [[("Sơ đồ vòng lặp bên phải: nhóm tự vẽ theo §2 của bài báo (không phải hình gốc).", 11, False, MUTED)]])
notes(s, "Nguồn: bài báo HELIX (arXiv:2608.13951). Nhóm 19, môn Khai phá dữ liệu, "
         "thầy Hà Quang Thụy. Khung phân biệt: tái thực nghiệm = chạy lại đồ của tác giả "
         "(lắp ghép CLI, Builder, chạy qua harness thật); mở rộng = train LoRA, phần tác giả "
         "chưa làm (§9.5). Mọi số đều có nguồn trong ghi chú từng slide.")

# ---------------- Slide 2: Roadmap ----------------
s = slide_new("chip")
header(s, "Tổng quan", "Lộ trình báo cáo", 2)
steps = [("01", "Bối cảnh &\nbài toán", "Vì sao cặp\nmodel–harness?"),
         ("02", "Nghiên cứu liên quan\n→ khoảng trống → RQ", "4 hướng; 4 khoảng\ntrống; 3 RQ của nhóm"),
         ("03", "Phương pháp\ngốc", "4 bước; Fig. 2;\ngiới hạn §9"),
         ("04", "Tái lập &\nmở rộng", "CLI + Builder +\n1.581 lượt; LoRA"),
         ("05", "Kết quả &\nkết luận", "Trả lời từng RQ;\nđóng góp của nhóm")]
cw_, gap = 2.30, 0.18
for i, (num, t, d) in enumerate(steps):
    x = ML + i * (cw_ + gap)
    card(s, x, 1.75, cw_, 3.15, fill=CARD2, line=CARDLINE)
    num_disc(s, x + 0.3, 2.05, 0.62, num, fill=BLOCK, size=16)
    txt(s, x + 0.3, 2.95, cw_ - 0.6, 0.9, [[(t, 17, True, WHITE)]], line_spacing=1.05)
    txt(s, x + 0.3, 3.95, cw_ - 0.6, 0.7, [[(d, 12.5, False, MUTED)]], line_spacing=1.05)
    if i < 4:
        txt(s, x + cw_ - 0.05, 3.05, 0.3, 0.4, [[("›", 22, True, SKYBLUE)]], align=PP_ALIGN.CENTER)
rect(s, ML, 5.35, CW, 0.85, BLOCK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.25)
txt(s, ML + 0.4, 5.35, CW - 0.8, 0.85,
    [[("Phần 1: bài toán → khoảng trống → RQ     •     Phần 2: phương pháp gốc và giới hạn     •     Phần 3: tái lập + mở rộng     •     Phần 4: kết quả và kết luận", 13.5, True, WHITE)]],
    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "Thứ tự theo luật của thầy: bối cảnh → phát biểu bài toán → nghiên cứu liên quan → "
         "khoảng trống → câu hỏi nghiên cứu → phương pháp gốc → giới hạn → đề xuất → kiểm chứng "
         "→ kết quả → kết luận. 1.581 lượt = 555 lượt trước evolution + 707 lượt evolution + 319 lượt chương trình $6 (135 O2 + 30 O3 + 90 O1 + 64 O5) qua harness thật, lệnh run của CLI tác giả, 15–20/11/2026. LoRA: 520 trace "
         "live vòng 1+2 qua harness mô phỏng prompt.")

# ---------------- Slide 3: Background ----------------
s = slide_new("chip")
header(s, "Phần 1 — Bối cảnh", "Bối cảnh: năng lực agent nằm ở cặp model–harness", 3)
blocks = [("Vấn đề", "Agent = model + harness (runtime). Harness quyết định model thấy gì, được làm gì, phục hồi lỗi ra sao và dừng khi nào."),
          ("Bằng chứng của tác giả", "Cùng một model, chỉ đổi harness: Pi đạt 50/100, harness tốt nhất 52/100, hợp tập portfolio 79/100."),
          ("Vì sao đáng nghiên cứu", "Harness vừa quyết định thực thi hôm nay, vừa tạo ra quỹ đạo để model học ngày mai — hai vai trò trong một vòng lặp.")]
for i, (t, d) in enumerate(blocks):
    y = 1.7 + i * 1.72
    card(s, ML, y, 5.3, 1.52)
    rect(s, ML, y, 0.07, 1.52, ACCENT)
    txt(s, ML + 0.3, y + 0.18, 4.8, 0.35, [[(t, 16, True, WHITE)]])
    txt(s, ML + 0.3, y + 0.58, 4.8, 0.8, [[(d, 13.5, False, TEXT)]])
rect(s, 6.25, 1.7, 6.53, 5.08, BLOCK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.05)
txt(s, 6.6, 1.9, 5.83, 0.3, [[("SỐ LIỆU CỦA TÁC GIẢ — MỐC ĐỐI CHIẾU", 11, True, SKY)]])
add_pic(s, os.path.join(PAPERFIG, "fig3-candidate-distribution.png"), 6.45, 2.22, 6.13, 2.18, frame=False)
txt(s, 6.6, 4.42, 5.83, 0.3, [[("Hình 3 (§6.1): phân bố 65 ứng viên — chỉ 2 vượt Pi; 23 ứng viên đạt 0. Nguồn: Fan & Huang (2026), Fig. 3.", 10.5, False, MUTED)]], align=PP_ALIGN.CENTER, line_spacing=1.05)
for j, (v, lab) in enumerate([("50/100", "Pi — baseline"), ("52/100", "Tốt nhất (+4,0%)"), ("79/100", "Hợp tập (post-hoc)")]):
    x = 6.6 + j * 2.02
    txt(s, x, 4.78, 1.9, 0.35, [[(v, 19, True, WHITE)]], align=PP_ALIGN.CENTER)
    txt(s, x, 5.14, 1.9, 0.28, [[(lab, 10.5, False, SKY)]], align=PP_ALIGN.CENTER)
formula(s, 6.6, 5.5, 5.83, 0.32,
        [[("Cov", 13, True, WHITE, None), ("K", 9, False, MUTED, 'sub'),
          ("(H)  =  (1/|D|) · Σ", 13, True, WHITE, None), ("x", 9, False, MUTED, 'sub'),
          (" 1[ max", 13, True, WHITE, None), ("1≤k≤K", 9, False, MUTED, 'sub'),
          (" v(τ) = 1 ]", 13, True, WHITE, None)]], space_after=0)
txt(s, 6.6, 5.84, 5.83, 0.26, [[("(9) Độ phủ: K: số lần thử • v: bộ kiểm chứng nhị phân • 52/100 là (9) với K = 1", 10.5, False, MUTED)]], align=PP_ALIGN.CENTER)
formula(s, 6.6, 6.12, 5.83, 0.32,
        [[("OracleCov", 13, True, WHITE, None), ("K", 9, False, MUTED, 'sub'),
          ("(C)  =  (1/|D|) · Σ", 13, True, WHITE, None), ("x", 9, False, MUTED, 'sub'),
          (" 1[ max", 13, True, WHITE, None), ("H∈C, 1≤k≤K", 9, False, MUTED, 'sub'),
          (" v(τ) = 1 ]", 13, True, WHITE, None)]], space_after=0)
txt(s, 6.6, 6.46, 5.83, 0.26, [[("(10) Độ phủ tiên tri: C: danh mục ứng viên • 79/100 là (10), không phải điểm của một khung chạy", 10.5, False, MUTED)]], align=PP_ALIGN.CENTER)
notes(s, "Nguồn: HELIX §§6–7, đối chiếu trong bang-so-lieu-cho-slide.md §2: 65 ứng viên × 100 bài "
         "LiveCodeBench, model cố định MiniMax-M2.7-highspeed (§6.1). Pi 50/100, tốt nhất 52/100 "
         "(+4,0%), hợp tập post-hoc 79/100 (+58%) — chênh 27 điểm giữa harness tốt nhất và hợp tập. §9.3: độ bao phủ oracle tính sau khi thấy mọi "
         "kết quả nên không đại diện cho lựa chọn harness trước khi triển khai. Hình 3 (§6.1) là hình "
         "kết quả quan trọng nhất của bài báo: 23 ứng viên ngoài baseline đạt 0 — ghép bừa phần lớn "
         "đều tệ, tiến hóa cần chọn lọc. Công thức (9) độ phủ Cov_K(H) và (10) độ phủ tiên tri "
         "OracleCov_K(C), gõ lại từ §2.4 của bài báo: 52/100 là (9) với K = 1; 79/100 là (10), không "
         "phải điểm của một harness cố định.")

# ---------------- Slide 4: Problem statement (NEW) ----------------
s = slide_new("code")
header(s, "Phần 1 — Bài toán", "Phát biểu bài toán: chọn harness tốt nhất", 4)
boxes4 = [("ĐẦU VÀO", "Tập bài toán D (sửa code)  •  Thư viện atom từ 4 harness nguồn  •  Model cố định M_t  •  Bộ kiểm chứng (test suite)", CARD2),
          ("QUÁ TRÌNH", "BUILD: lắp ghép và đánh giá ứng viên  →  UPDATE: rút sibling record  →  REBUILD: lắp lại cho model mới", BLOCK),
          ("ĐẦU RA", "Harness cố định tốt nhất cho M_t  •  Sibling record đã kiểm chứng  •  Danh mục mới cho vòng sau", CARD2)]
bw4, gap4 = 3.79, 0.43
for i, (t, d, fill) in enumerate(boxes4):
    x = ML + i * (bw4 + gap4)
    card(s, x, 1.55, bw4, 1.7, fill=fill, line=ACCENT if i == 1 else CARDLINE)
    txt(s, x + 0.25, 1.72, bw4 - 0.5, 0.3, [[(t, 11, True, SKYBLUE)]])
    txt(s, x + 0.25, 2.08, bw4 - 0.5, 1.05, [[(d, 13, False, WHITE)]], line_spacing=1.12)
    if i < 2:
        txt(s, x + bw4, 2.2, gap4, 0.4, [[("→", 22, True, SKYBLUE)]], align=PP_ALIGN.CENTER)
txt(s, ML, 3.28, CW, 0.16, [[("Nhóm dùng 50 bài tự viết thay cho 100 bài LiveCodeBench của bài báo (xem slide 12).", 10.5, False, MUTED)]], align=PP_ALIGN.CENTER)
card(s, ML, 3.45, CW, 2.05, fill=CARD, line=SKYBLUE)
txt(s, ML + 0.3, 3.58, CW - 0.6, 0.3, [[("MỤC TIÊU KÉP (§2.2, GÕ LẠI) — DẠNG LƯỢC ĐỒ, KHÔNG GỘP THÀNH MỘT SỐ", 11, True, SKYBLUE)]])
formula(s, ML + 0.3, 3.9, CW - 0.6, 0.45,
        [[("C*", 17, True, WHITE, None), ("  =  argmax", 17, True, WHITE, None),
          ("C", 12, False, MUTED, 'sub'),
          ("  [  α · max ", 17, True, WHITE, None),
          ("H", 12, False, MUTED, 'sub'),
          (" J", 17, True, WHITE, None),
          ("deploy", 12, False, MUTED, 'sub'),
          ("(M", 17, True, WHITE, None),
          ("t", 12, False, MUTED, 'sub'),
          (", H)  +  β · Q", 17, True, WHITE, None),
          ("data", 12, False, MUTED, 'sub'),
          ("(S)  −  γ · C", 17, True, WHITE, None),
          ("build", 12, False, MUTED, 'sub'),
          ("(C)  ]", 17, True, WHITE, None)]])
txt(s, ML + 0.3, 4.38, CW - 0.6, 0.3,
    [[("Q_data: giá trị dữ liệu học từ sibling  •  C_build: chi phí xây dựng  •  α, β, γ: trọng số", 11.5, False, MUTED)]],
    align=PP_ALIGN.CENTER)
txt(s, ML + 0.3, 4.68, CW - 0.6, 0.26, [[("CÔNG THỨC (3) — ĐỊNH NGHĨA J_deploy DÙNG TRONG (5):", 10.5, True, SKYBLUE)]], align=PP_ALIGN.CENTER)
formula(s, ML + 0.3, 4.94, CW - 0.6, 0.35,
        [[("J", 14, True, WHITE, None), ("deploy", 10, False, MUTED, 'sub'),
          ("(M", 14, True, WHITE, None), ("t", 10, False, MUTED, 'sub'),
          (", H", 14, True, WHITE, None), ("φ", 10, False, MUTED, 'sub'),
          (")  =  E", 14, True, WHITE, None), ("x,k", 10, False, MUTED, 'sub'),
          ("[ R(y, τ) − λC(τ) − μP(τ) ]", 14, True, WHITE, None)]])
txt(s, ML + 0.3, 5.28, CW - 0.6, 0.26,
    [[("R: phần thưởng đã kiểm chứng  •  C: chi phí chạy  •  P: rủi ro chính sách  •  λ, μ: trọng số", 10.5, False, MUTED)]],
    align=PP_ALIGN.CENTER)
card(s, ML, 5.65, 6.02, 1.15)
txt(s, ML + 0.3, 5.76, 5.42, 0.3, [[("TIÊU CHÍ THÀNH CÔNG (CỦA BÀI BÁO, §2)", 11, True, SKYBLUE)]])
bullets(s, ML + 0.3, 6.04, 5.42, 0.7,
        ["Harness cố định vượt baseline Pi theo Pass@1",
         "Sibling record vật chất hóa được (SFT / critic / filter / preference)",
         "Mọi kết quả chấm bằng test suite, không tự chấm"], size=12, gap=2)
card(s, 6.76, 5.65, 6.02, 1.15)
txt(s, 7.06, 5.76, 5.42, 0.3, [[("GIẢ ĐỊNH & RÀNG BUỘC (CỦA BÀI BÁO, §2, §6.1)", 11, True, SKYBLUE)]])
bullets(s, 7.06, 6.04, 5.42, 0.7,
        ["Model cố định, rất mạnh (MiniMax-M2.7-highspeed)",
         "Harness lắp từ thư viện atom của tác giả",
         "Ma trận 65 × 100: mỗi cặp ứng viên–bài 1 lần chạy"], size=12, gap=2)
notes(s, "Phát biểu theo đúng bản chất framework của paper (§2): bài toán là chọn danh mục ứng viên "
         "C tối ưu cả hai đầu ra — thực thi và dữ liệu học — chứ không phải một thuật toán đơn lẻ. "
         "Hàm mục tiêu là Eq. (5) của paper, dạng lược đồ: paper nói rõ không gộp các số hạng "
         "thành một scalar đã tinh chỉnh mà đo các proxy quan sát được riêng biệt. Pass@1: tỉ lệ "
         "bài pass test. 1 lần chạy/cặp trong ma trận 65×100 theo §9.3. Công thức (3) J_deploy gõ "
         "lại từ §2.2: kỳ vọng của phần thưởng đã kiểm chứng trừ chi phí chạy và rủi ro chính sách "
         "(R: phần thưởng đã kiểm chứng; C: chi phí; P: rủi ro; λ, μ: trọng số).")

# ---------------- Slide 5: Related work (NEW) ----------------
s = slide_new("chip")
header(s, "Phần 1 — Nghiên cứu liên quan", "Nghiên cứu liên quan: bốn hướng hội tụ về một bàn giao", 5)
add_table(s, ML, 1.6, CW, 4.45,
          [["Hướng nghiên cứu", "Công trình tiêu biểu (§8 của paper)", "Đã đạt được", "Còn thiếu — HELIX bổ sung (diễn giải của nhóm)"],
           ["Tự cải thiện đệ quy",
            "Gödel Machine (Schmidhuber, 2003); Darwin Gödel Machine (Zhang và cộng sự, 2025); Recursive Harness Self-Improvement (Lee và cộng sự, 2026); HarnessX v3 (Chen và cộng sự, 2026)",
            "Hệ thống tự sửa mã / harness theo chứng minh, benchmark, phản hồi theo cặp",
            "Chưa có bàn giao truy vết nguồn qua các harness không đồng nhất"],
           ["Harness là giao diện tác tử–máy tính",
            "ReAct (Yao và cộng sự, 2023); Toolformer; SWE-agent (Yang và cộng sự, 2024)",
            "Hành vi agent phụ thuộc giao diện, không chỉ dự đoán token tiếp theo",
            "Can thiệp mới dừng ở prompt / công cụ, chưa tới toàn bộ runtime"],
           ["Tiến hóa harness và quy trình tự động",
            "AutoFlow; ADAS (Meta Agent Search); AFlow",
            "Tối ưu lặp / MCTS tìm được quy trình và tác tử tốt hơn",
            "Chỉ báo cáo ứng viên thắng; quỹ đạo ứng viên thua bị bỏ"],
           ["Dữ liệu tương tác và benchmark",
            "LiveCodeBench (Jain và cộng sự, 2025); SWE-bench (Jimenez và cộng sự, 2024); SWE-Gym; SWE-smith; Learn-by-Interact",
            "Đánh giá và dữ liệu huấn luyện từ tương tác thực thi",
            "Chưa nối dữ liệu tương tác với cập nhật model qua sibling"]],
          [2.5, 3.5, 3.35, 2.88], font_size=12.5)
rect(s, ML, 6.15, CW, 0.7, BLOCK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.3)
txt(s, ML + 0.3, 6.15, CW - 0.6, 0.7,
    [[("Tổng hợp của paper (§8): các hướng trước cải thiện giao diện, tiến hóa quy trình, hoặc học từ tương tác — HELIX nối chúng bằng bàn giao build → update truy vết được nguồn. Dựa trực tiếp nhất: HarnessX v3 (lớp gần nhất); nền tảng đệ quy: Darwin Gödel Machine, Recursive Harness Self-Improvement.", 12, True, WHITE)]],
    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "Toàn bộ nội dung slide này chỉ lấy từ §8 Related Work của paper (đối chiếu bản arXiv HTML "
         "tươi ngày 17/11/2026): §8.1 tự cải thiện đệ quy và đồng tiến hóa (Gödel Machine, Darwin "
         "Gödel Machine, Recursive Harness Self-Improvement, HarnessX v3); §8.2 harness là giao "
         "diện tác tử–máy tính (ReAct, Toolformer, SWE-agent); §8.3 tiến hóa tự động (AutoFlow, "
         "ADAS/Meta Agent Search, AFlow); §8.4 dữ liệu tương tác và benchmark (LiveCodeBench, "
         "SWE-bench, SWE-Gym, SWE-smith, Learn-by-Interact). Câu tổng hợp cuối là diễn giải đoạn "
         "tổng hợp của §8, không thêm trích dẫn ngoài paper.")

# ---------------- Slide 6: Research gap (NEW) ----------------
s = slide_new("code")
header(s, "Phần 1 — Khoảng trống", "Khoảng trống: vòng lặp chưa từng khép kín", 6)
gaps = [("G1 — Chưa train model nào", "§9.5 tự nhận: paper chỉ vật chất hóa dữ liệu cập nhật, không huấn luyện một model đã cập nhật.", "→ RQ3"),
        ("G2 — Model cố định, rất mạnh", "Tìm kiếm dùng MiniMax-M2.7-highspeed. Chưa biết vòng lặp có chạy với model nhỏ, mở (7B) hay không.", "→ RQ1"),
        ("G3 — Hợp tập là post-hoc", "§9.3: 79/100 tính sau khi thấy mọi kết quả; không phải lựa chọn harness trước khi triển khai.", "→ RQ2"),
        ("G4 — Chưa đo Rebuild", "§2.3: harness tốt cho model cũ chưa chắc tốt cho model mới — nhưng chưa ai đo điều này.", "→ RQ2")]
for i, (t, d, tag) in enumerate(gaps):
    y = 1.6 + i * 1.32
    card(s, ML, y, 6.0, 1.2)
    rect(s, ML, y, 0.07, 1.2, AMBER)
    txt(s, ML + 0.3, y + 0.14, 5.45, 0.32, [[(t, 15, True, WHITE)]])
    txt(s, ML + 0.3, y + 0.5, 5.45, 0.6, [[(d, 12.5, False, TEXT)]], line_spacing=1.05)
    # DARK-ONLY bridge 18/11/2026 (Triệu): gap → RQ tag, same mapping as slide 7
    txt(s, ML + 4.35, y + 0.16, 1.4, 0.3, [[(tag, 11, True, SKYBLUE)]], align=PP_ALIGN.RIGHT)
add_pic(s, os.path.join(CH, "paper_fig_438.png"), 6.75, 1.6, 6.03, 2.8,
        "Nguồn: Fan & Huang (2026), Fig. 4 — 200 slot → 438 record")
txt(s, 6.75, 4.48, 6.03, 0.52,
    [[("63 tinh chỉnh sạch • 56 cần dọn • 52 mẫu phủ định • 113 mẫu lọc • 154 cặp ưu tiên", 11, True, WHITE)],
     [("438 là số hàng đã suy ra (Bảng 3), không phải 438 lượt chạy độc lập.", 11, False, MUTED)]],
    align=PP_ALIGN.CENTER, space_after=2, line_spacing=1.05)
card(s, 6.75, 5.05, 6.03, 1.71)
txt(s, 6.75, 5.18, 6.03, 0.5, [[("438  →  0", 26, True, WHITE)]], align=PP_ALIGN.CENTER)
txt(s, 7.05, 5.74, 5.43, 0.55,
    [[("438 hàng đã suy ra — số của bài báo (Bảng 3)", 12, False, TEXT)],
     [("0 model được train từ đó — số của nhóm (§9.5)", 12, False, MUTED)]],
    align=PP_ALIGN.CENTER, space_after=2)
notes(s, "G1: §9.5 — 'This paper materializes model-update data but does not train an updated "
         "model.' G2: model cố định MiniMax-M2.7-highspeed (§6.1). G3: §9.3 — oracle coverage tính "
         "sau khi thấy mọi kết quả. G4: §2.3 — argmax theo phi của J(M_{t+1}, H_phi) không nhất "
         "thiết bằng argmax của J(M_t, H_phi). Hình: Figure 4 của bài báo — Clean SFT 63, "
         "Cleanup-needed SFT 56, Critic negatives 52, Filter samples 113, Preference pairs 154 "
         "(file gốc harnesslego-training-data.pdf, chuyển PNG 300 dpi, không sửa nội dung). Mỗi thẻ "
         "ghi tag → RQ theo mapping ở slide 7 (G1→RQ3; G2→RQ1; G3→RQ2; G4→RQ2). RQ1 nối với G2 "
         "(chưa biết vòng lặp có chạy với model nhỏ, mở hay không), không nối với G1 nữa — G1 dẫn "
         "thẳng tới RQ3 (train LoRA). Bảng 1 (§4.3): 4 mẫu đã kiểm chứng cho ra 4 loại dữ liệu "
         "(tinh chỉnh sạch; phê bình/ưu tiên; lọc; thay thế/tối giản) — nói thêm khi thuyết trình.")

# ---------------- Slide 7: Research questions (NEW) ----------------
s = slide_new("pipeline")
header(s, "Phần 1 — Câu hỏi nghiên cứu", "Câu hỏi nghiên cứu: mỗi RQ nảy ra từ một khoảng trống", 7)
rqs = [("RQ1", "Từ G2",
        "Đồ của tác giả có chạy lại được ở quy mô nhỏ không?",
        "H1: CLI lắp đúng 4 harness — verification đạt, đủ 96 cổng, fingerprint khớp Builder.",
        "Kiểm chứng: lắp ghép CLI + Helix Builder."),
       ("RQ2", "Từ G3, G4",
        "Harness lắp thật có chạy được bài và chấm ngoài được không?",
        "H2: Chạy 1.581 lượt qua 3 harness thật bằng lệnh run, chấm bằng test suite độc lập.",
        "Kiểm chứng: driver + test suite, 0 lỗi hạ tầng."),
       ("RQ3", "Từ G1",
        "LoRA có cải thiện Pass@1 và chuyển sang harness thật không?",
        "H3: LoRA cải thiện Pass@1 qua mô phỏng (H3a) và giữ được cải thiện trên harness thật (H3b).",
        "Kiểm chứng: 2 vòng closed-loop + rebuild + fix + khái quát hóa.")]
for i, (rq, src, q, h, v) in enumerate(rqs):
    y = 1.6 + i * 1.65
    card(s, ML, y, CW, 1.5)
    rect(s, ML + 0.25, y + 0.44, 1.0, 0.62, ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.2)
    txt(s, ML + 0.25, y + 0.44, 1.0, 0.62, [[(rq, 15, True, WHITE)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    txt(s, ML + 1.45, y + 0.18, 7.6, 0.32, [[(q, 15.5, True, WHITE)]])
    txt(s, ML + 1.45, y + 0.58, 7.6, 0.65, [[(h, 13, False, TEXT)]], line_spacing=1.05)
    txt(s, ML + 1.45, y + 1.18, 7.6, 0.28, [[(src, 11, True, SKYBLUE)]])
    rect(s, 9.35, y + 0.25, 0.02, 1.0, CARDLINE)
    txt(s, 9.6, y + 0.25, 2.95, 1.0, [[(v, 12.5, False, SKY)]], anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.1)
txt(s, ML, 6.6, CW, 0.35,
    [[("Phân biệt: RQ1–RQ3 của paper (§6) hỏi về thực thi và dữ liệu học; RQ1–RQ3 của nhóm hỏi về tái lập và mở rộng.", 12, False, MUTED)]],
    align=PP_ALIGN.CENTER)
notes(s, "RQ của paper (§6.2): RQ1 thực thi có vượt baseline; RQ2 độ rộng thực thi của portfolio; "
         "RQ3 dữ liệu học tập cho lần cập nhật tiếp theo. RQ của nhóm khác: RQ1/RQ2 là tái thực "
         "nghiệm đồ của tác giả (lắp ghép + chạy thật); RQ3 là mở rộng (LoRA), tách H3a (mô phỏng) "
         "và H3b (chuyển sang harness thật) vì hai khẳng định này được kiểm chứng bằng hai thực "
         "nghiệm khác nhau và cho kết quả khác nhau.")

# ---------------- Slide 8: Original method ----------------
s = slide_new("code")
header(s, "Phần 2 — Phương pháp gốc", "Phương pháp gốc: vòng build–update–rebuild", 8)
steps8 = [("Bước 1\nAtom hóa harness", "Tách thành atom"),
          ("Bước 2\nLắp ghép", "Recipe → runtime"),
          ("Bước 3\nTìm kiếm", "65 ứng viên, Pass@1"),
          ("Bước 4\nRút sibling", "438 record / 200 slot")]
for i, (t, d) in enumerate(steps8):
    x = ML + i * (2.72 + 0.45)
    card(s, x, 1.5, 2.72, 1.5, fill=CARD2, line=ACCENT)
    txt(s, x + 0.2, 1.65, 2.32, 0.8, [[(t, 14, True, WHITE)]], align=PP_ALIGN.CENTER, line_spacing=1.1)
    txt(s, x + 0.2, 2.55, 2.32, 0.35, [[(d, 11.5, False, MUTED)]], align=PP_ALIGN.CENTER)
    if i < 3:
        txt(s, x + 2.72, 2.05, 0.45, 0.4, [[("→", 20, True, WHITE)]], align=PP_ALIGN.CENTER)
txt(s, ML, 3.08, CW, 0.2, [[("Đầu vào → đầu ra (xem slide 4): tập bài + atom + model cố định  →  harness tốt nhất + sibling record.", 10.5, False, MUTED)]], align=PP_ALIGN.CENTER)
card(s, ML, 3.35, 6.4, 3.45, fill=CARD, line=SKYBLUE)
txt(s, ML + 0.3, 3.5, 5.8, 0.3, [[("CÔNG THỨC GỐC — PAPER §2 (GÕ LẠI)", 11, True, SKYBLUE)]])
txt(s, ML + 0.3, 3.82, 5.8, 0.24, [[("BỘ KIỂM CHỨNG (2) — ĐỊNH NGHĨA “ĐÃ KIỂM CHỨNG”:", 10.5, True, SKYBLUE)]])
formula(s, ML + 0.3, 4.06, 5.8, 0.3,
        [[("y", 13, True, WHITE, None), ("t,i,x,k", 9, False, MUTED, 'sub'),
          ("  =  V(x, τ, ΔW, T, P)", 13, True, WHITE, None)]], space_after=0)
txt(s, ML + 0.3, 4.38, 5.8, 0.34,
    [[("τ: quỹ đạo • ΔW: chênh lệch workspace • T: bằng chứng kiểm tra • P: bằng chứng chính sách • nhãn y không nhất thiết nhị phân", 10.5, False, MUTED)]],
    align=PP_ALIGN.CENTER, line_spacing=1.05)
txt(s, ML + 0.3, 4.76, 5.8, 0.24, [[("NHÓM ANH EM (4) — BƯỚC 4 RÚT SIBLING:", 10.5, True, SKYBLUE)]])
formula(s, ML + 0.3, 5.0, 5.8, 0.3,
        [[("S", 13, True, WHITE, None), ("t,x", 9, False, MUTED, 'sub'),
          ("  =  { (H", 13, True, WHITE, None), ("φi", 9, False, MUTED, 'sub'),
          (", τ, y) }", 13, True, WHITE, None), ("i,k", 9, False, MUTED, 'sub')]], space_after=0)
txt(s, ML + 0.3, 5.32, 5.8, 0.26, [[("Cùng một bài, mọi harness × mọi lần thử — giàu thông tin hơn bộ nhớ phát lại không phân biệt.", 10.5, False, MUTED)]], align=PP_ALIGN.CENTER)
formula(s, ML + 0.3, 5.62, 5.8, 0.55,
        [[("D", 13, True, WHITE, None), ("t", 9, False, MUTED, 'sub'),
          ("  =  G(E", 13, True, WHITE, None), ("t", 9, False, MUTED, 'sub'),
          (")    θ", 13, True, WHITE, None), ("t+1", 9, False, MUTED, 'sub'),
          ("  =  U(θ", 13, True, WHITE, None), ("t", 9, False, MUTED, 'sub'),
          (", D", 13, True, WHITE, None), ("t", 9, False, MUTED, 'sub'), (")", 13, True, WHITE, None)],
         [("Φ", 13, True, WHITE, None), ("t+1", 9, False, MUTED, 'sub'),
          ("  =  B(Φ", 13, True, WHITE, None), ("t", 9, False, MUTED, 'sub'),
          (", E", 13, True, WHITE, None), ("t", 9, False, MUTED, 'sub'),
          ("; M", 13, True, WHITE, None), ("t+1", 9, False, MUTED, 'sub'),
          (")    Z", 13, True, WHITE, None), ("t+1", 9, False, MUTED, 'sub'),
          ("  =  R(Z", 13, True, WHITE, None), ("t", 9, False, MUTED, 'sub'), (")", 13, True, WHITE, None)]],
        space_after=4)
txt(s, ML + 0.3, 6.28, 5.8, 0.45,
    [[("E_t: bằng chứng đã kiểm chứng • G: xây dữ liệu • U: cập nhật • B: xây lại • R: chuyển trạng thái", 10.5, False, MUTED)],
     [("Hệ quả (§2.3): harness tốt nhất có thể đổi sau mỗi lần cập nhật model — vì vậy phải Rebuild.", 10.5, True, SKY)]],
    align=PP_ALIGN.CENTER, space_after=2, line_spacing=1.05)
card(s, 7.15, 3.35, 5.63, 3.45, fill=CARD)
txt(s, 7.45, 3.5, 5.03, 0.3, [[("HÌNH 1 — HAI THANG THỜI GIAN (§2, BÀI BÁO)", 11, True, SKYBLUE)]])
add_pic(s, os.path.join(PAPERFIG, "fig1-two-timescales.png"), 7.45, 3.82, 5.03, 2.5, frame=False)
txt(s, 7.45, 6.36, 5.03, 0.4,
    [[("Nguồn: Fan & Huang (2026), Fig. 1. Đường quay lại ở tầng dưới phân biệt cải tiến đệ quy với một lần tinh chỉnh.", 10.5, False, MUTED)]],
    align=PP_ALIGN.CENTER, line_spacing=1.05)
notes(s, "Công thức là Eq. (6) và phương trình cập nhật hệ thống của paper §2.3, gõ lại bằng text "
         "(không chụp ảnh), ký hiệu giữ nguyên: D_t = G(E_t); theta_{t+1} = U(theta_t, D_t); "
         "Phi_{t+1} = B(Phi_t, E_t; M_{t+1}); Z_{t+1} = R(Z_t). Kiến trúc HELIX theo Figure 2 của "
         "paper: atomization → recipe → assembled runtime (hình gốc ở slide 9). Định nghĩa Harness "
         "Gap theo REBUILD_REPORT của nhóm (claim-va-caveat.md, claim 4) — đây là định nghĩa của "
         "nhóm, không phải của paper. Pi-mono lắp thật: 303 atom, 96/96 port, fingerprint "
         "f87e68defe775bb6.")

# ---------------- Slide 9: Paper Figure 2, dedicated ----------------
s = slide_new("code")
header(s, "Phần 2 — Phương pháp gốc", "Hình gốc: kiến trúc HELIX", 9)
add_pic(s, os.path.join(CH, "paper_fig_architecture.png"), ML, 1.5, 8.7, 5.4,
        "Nguồn: Fan & Huang (2026), arXiv:2608.13951, Fig. 2")
card(s, 9.45, 1.5, 3.33, 5.4, fill=CARD)
txt(s, 9.7, 1.7, 2.83, 0.3, [[("ĐỌC HÌNH NHƯ THẾ NÀO", 11, True, SKYBLUE)]])
bullets(s, 9.7, 2.1, 2.83, 3.2,
        ["4 harness nguồn → atom hóa → catalog atom + recipe → runtime đã lắp ghép",
         "Hợp đồng lắp ghép 96 cổng: bindings, resources, lockfile, provenance",
         "Evidence plane: runtime trace, workspace diff, verifier status"],
        size=13.5, gap=12)
# DARK-ONLY bridge 18/11/2026 (Triệu): group link in the free space below the reading guide
txt(s, 9.7, 4.3, 2.83, 1.0, [[("→ Nhóm kiểm chứng bằng chính CLI + Builder này: lắp ghép 4 harness và chạy thật (slide 13–14).", 12.5, True, SKYBLUE)]], line_spacing=1.1)
rect(s, 9.7, 5.5, 2.83, 0.02, CARDLINE)
txt(s, 9.7, 5.62, 2.83, 1.15, [[("Quy mô trong hình: 631 atom ID duy nhất; 1.332 kể cả hợp đồng Minimal. Nét liền: luồng dữ liệu. Nét đứt: artifact phái sinh.", 11.5, False, MUTED)]], line_spacing=1.1)
notes(s, "Hình: Figure 2 của bài báo (file gốc harnesslego-architecture.pdf, chuyển PNG 300 dpi, "
         "không sửa nội dung). Đọc từ trên xuống: 4 harness nguồn (OpenCode, Pi Mono, Nanobot, "
         "Hermes Agent) → atom hóa theo 8 loại (shell, session/hooks, config, prompt, tools, turn "
         "loop, acceptance, runtime policy) → catalog atom + lựa chọn recipe → compiler + assembler "
         "kiểm tra tương thích → runtime đã lắp ghép và các mặt sản phẩm → evidence plane. Hợp đồng "
         "lắp ghép 96 cổng và kiểm tra conformance/audit là artifact phái sinh hoặc áp dụng riêng "
         "(nét đứt), không phải cổng chặn runtime tự động. Quy mô hệ thống ghi trong hình: 631 atom "
         "ID duy nhất, 1.156 lần xuất hiện, 1.332 kể cả hợp đồng Minimal trung tính. Cột phải có dòng "
         "cầu nối: nhóm kiểm chứng bằng chính CLI + Builder này — lắp ghép 4 harness và chạy thật "
         "(slide 13–14).")

# ---------------- Slide 10: Limits of the original method ----------------
s = slide_new("branch")
header(s, "Phần 2 — Phân tích", "Phân tích phê bình: giới hạn của phương pháp gốc", 10)
lims = [("Giới hạn 1 — Chưa khép vòng (§9.5)",
         "438 sibling record chưa từng dùng để train. Tác giả dừng ở dữ liệu, không đo Rebuild bằng model mới.",
         "→ Nhóm lấp đúng chỗ này: train LoRA thật."),
        ("Giới hạn 2 — Model cố định, rất mạnh (§6.1)",
         "Tìm kiếm dùng MiniMax-M2.7-highspeed. Chưa biết vòng lặp có chạy với model nhỏ, mở (7B) hay không.",
         "→ Nhóm kiểm chứng với Qwen 7B mở."),
        ("Giới hạn 3 — Chi phí tìm kiếm lớn (§6, §9.3)",
         "6.500 slot + 3.000 lặp lại + 550 SWE-bench; mỗi cặp ứng viên–bài chỉ 1 lần chạy trong ma trận.",
         "→ Nhóm thu nhỏ còn 65 bài, 1.581 lượt chạy thật."),
        ("Giới hạn 4 — Không có harness vô địch (§9.3)",
         "Harness tốt nhất chỉ 52/100, hợp tập post-hoc 79/100: harness tốt phụ thuộc từng bài.",
         "→ Nhóm đo riêng từng harness, không gộp post-hoc.")]
for i, (t, d, c) in enumerate(lims):
    x = ML + (i % 2) * (6.02 + 0.19)
    y = 1.7 + (i // 2) * (2.15 + 0.18)
    card(s, x, y, 6.02, 2.15)
    txt(s, x + 0.3, y + 0.22, 5.42, 0.35, [[("⚠  ", 14, True, SKYBLUE), (t, 16, True, WHITE)]])
    txt(s, x + 0.3, y + 0.65, 5.42, 0.85, [[(d, 13.5, False, TEXT)]], line_spacing=1.1)
    txt(s, x + 0.3, y + 1.6, 5.42, 0.35, [[(c, 13, True, SKYBLUE)]])
rect(s, ML, 6.35, CW, 0.5, BLOCK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
txt(s, ML, 6.35, CW, 0.5, [[("Tác giả tự nhận thêm (§9.2): đổi nhiều thành phần cùng lúc nên không quy cải thiện cho thành phần nào — nhóm không tách ablation, chỉ đo toàn bộ harness", 13, True, WHITE)]],
    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "§9.5 là giới hạn tác giả tự nhận — điểm nhóm vượt paper ở đúng một trục: train LoRA thật "
         "và đánh giá lại (claim 6). Mọi trục còn lại nhóm đều nhỏ hơn paper nhiều. §9.2: mỗi "
         "harness tiến hóa đổi nhiều thành phần cùng lúc nên không tách được nguyên nhân — nhóm "
         "giữ nguyên thiết kế này và không gọi phân tích của mình là ablation. §9.1: ma trận chính "
         "dùng 100 bài AtCoder đầu tiên đủ điều kiện (không phải mẫu ngẫu nhiên), chỉ kiểm tra test "
         "công khai.")

# ---------------- Slide 11: Group proposal ----------------
s = slide_new("branch")
header(s, "Phần 3 — Đề xuất", "Đề xuất của nhóm: khép vòng bằng LoRA thật", 11)
add_table(s, ML, 1.6, CW, 2.5,
          [["Hạn chế thực sự", "Thay đổi của nhóm", "Giả thuyết", "Metric kiểm chứng"],
           ["§9.5: chưa train model nào từ sibling record",
            "Train LoRA (SFT + DPO) từ trace sibling live",
            "H3a: LoRA cải thiện Pass@1 qua harness mô phỏng",
            "Pass@1 vòng 2 + held-out v2; McNemar"],
           ["Chưa đo Rebuild trên harness thật",
            "Chạy base so với LoRA qua 3 harness thật (lệnh run)",
            "H3b: cải thiện chuyển được sang harness thật",
            "Pass@1 + tỉ lệ dùng tool; 35 bài × 3 harness"],
           ["LoRA vòng 2 ít dùng tool trên harness thật (14/35)",
            "Train LoRA mới từ trace harness thật (SFT 40 + DPO 9)",
            "H3b (sửa): dữ liệu trace thật khôi phục hành vi dùng tool",
            "Text-only ≤ 7/35; Pass@1; kiểm tra 15 bài mới"]],
          [2.9, 3.1, 3.3, 2.93], font_size=13)
card(s, ML, 4.25, CW, 1.45, fill=CARD, line=AMBER)
txt(s, ML + 0.3, 4.4, CW - 0.6, 0.3, [[("ĐIỀU KIỆN ĐỂ ĐỀ XUẤT CÓ TÁC DỤNG", 11, True, AMBER_LT)]])
bullets(s, ML + 0.3, 4.75, CW - 0.6, 0.85,
        ["Dữ liệu sibling phải dạy được hành vi dùng tool trong harness thật — nếu chỉ dạy viết code, LoRA sẽ không chuyển được.",
         "Model cập nhật không được hồi quy năng lực chung — held-out v2 (15 bài mới) làm kiểm chứng."],
        size=13.5, gap=6)
rect(s, ML, 5.85, CW, 0.8, BLOCK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
txt(s, ML + 0.3, 5.85, CW - 0.6, 0.8,
    [[("Giữ nguyên: ý tưởng vòng lặp, test suite chấm ngoài, CLI của tác giả.   Thay đổi duy nhất: train thật + đo lại.", 14.5, True, WHITE)]],
    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "Mở rộng = vòng closed-loop 2 lần (12/11, 520 trace live qua harness mô phỏng prompt) + "
         "kiểm tra chuyển sang harness thật (rebuild bước 1–3, 15–16/11). Điểm mới duy nhất so với "
         "paper: train thật + đo lại; mọi thành phần khác giữ nguyên ý tưởng của tác giả. Kết quả: "
         "H3a tăng nhẹ nhưng chưa có ý nghĩa thống kê; H3b KHÔNG được ủng hộ với LoRA vòng 2 — xem "
         "slide 15 và 17. Fix từ trace thật (18/11): H3b được ủng hộ có điều kiện — xem slide 16. "
         "25 sibling record của nhóm làm từ trace của nhóm theo ý tưởng paper, KHÔNG qua pipeline "
         "của tác giả.")

# ---------------- Slide 12: Verification design ----------------
s = slide_new("pipeline")
header(s, "Phần 3 — Thiết kế kiểm chứng", "Thiết kế kiểm chứng: của paper, nhóm làm lại, nhóm tự làm", 12)
add_table(s, ML, 1.55, CW, 2.55,
          [["Hạng mục", "Của paper", "Nhóm làm lại", "Nhóm tự cải tiến"],
           ["Lắp ghép", "CLI + Builder, 65 ứng viên", "CLI upstream, 4 harness, git clean", "—"],
           ["Chạy bài", "6.500 lượt, MiniMax", "1.581 lượt, Qwen 7B, lệnh run", "—"],
           ["Sibling record", "438 từ 200 slot", "74 từ trace nhóm, theo ý tưởng", "—"],
           ["Train model", "Không (§9.5)", "—", "4 LoRA (vòng 2 + trace-thật + SFT-only + sạch), Modal A100"],
           ["Tìm kiếm harness", "Chọn theo từng bài", "Mini-search 9 recipe (runner.mts): R4 7/10 vs R0 6/10", "—"]],
          [2.2, 3.35, 3.35, 3.33], font_size=12.5)
add_table(s, ML, 4.3, CW, 1.85,
          [["Tài nguyên", "Paper có", "Nhóm có / không có"],
           ["Model", "MiniMax-M2.7-highspeed (đóng, rất mạnh)", "Qwen2.5-Coder-7B-Instruct (mở)"],
           ["Bài và lượt chạy", "100 bài LCB + 55 SWE-bench; 6.500 + 3.000 + 550 lượt", "65 bài tự viết; 1.581 lượt thật + 520 trace mô phỏng"],
           ["Dữ liệu và công cụ", "438 record; CLI + Builder + fixture đầy đủ", "74 record; cùng CLI + Builder; 94 fixture tái tạo (nhóm tự làm)"]],
          [2.2, 5.0, 5.03], font_size=12.5)
rect(s, ML, 6.35, CW, 0.5, BLOCK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
txt(s, ML, 6.35, CW, 0.5, [[("Baseline: base model + harness Minimal / Pi-mono  •  Metric: Pass@1, McNemar, tỉ lệ dùng tool  •  Mỗi ô 2 lần chạy (mới + base)  •  Chấm ngoài bằng test suite", 13, True, WHITE)]],
    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "Tài nguyên paper: model MiniMax-M2.7-highspeed (§6.1); 100 bài LCB + 55 SWE-bench "
         "Verified; 6.500 slot ma trận + 3.000 lượt lặp lại (3 thành viên × 1.000) + 550 slot SWE "
         "(55 bài × 2 lượt × 5 thành viên). Paper không nêu GPU nên slide không ghi. Tài nguyên "
         "nhóm: Qwen2.5-Coder-7B-Instruct, Modal A100, 65 bài tự viết (20 train + 15 held-out v2 + 15 khái quát hóa held3 + 15 held4), 1.581 lượt qua harness thật (555 trước evolution + 707 evolution + 319 chương trình $6: 135 O2 + 30 O3 + 90 O1 + 64 O5) "
         "+ 520 trace live qua harness mô phỏng prompt (vòng 1: 160, vòng 2: 360), 74 record tự rút. "
         "101 symlink gãy ban đầu (điểm tới máy tác giả, kiểm tra 2 lần); nhóm tái tạo 94 fixture, 6 loại ra. CLI upstream kiểm tra "
         "15/11: chỉ có run/assemble/validate/compose/task-parity, không có lệnh tìm kiếm/evolve. "
         "upstream_git_status_after.txt rỗng — không sửa code tác giả.")

# ---------------- Slide 13: Replication experiments ----------------
s = slide_new("pipeline")
header(s, "Phần 3 — Tái thực nghiệm", "Thực nghiệm tái lập: lắp ghép và chạy thật", 13)
phases = ["1. Lấy code tác giả (git clean)", "2. Lắp ghép CLI (4 harness)",
          "3. Chạy harness thật (210 lượt)", "4. Đối chiếu và nêu ranh giới"]
pw13, gap13 = 2.92, 0.18
for i, ph in enumerate(phases):
    x = ML + i * (pw13 + gap13)
    rect(s, x, 1.5, pw13, 0.42, BLOCK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.5)
    txt(s, x, 1.5, pw13, 0.42, [[(ph, 12, True, WHITE)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    if i < 3:
        txt(s, x + pw13 - 0.05, 1.5, 0.3, 0.42, [[("›", 16, True, SKYBLUE)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
add_pic(s, os.path.join(CH, "builder_ghep_2buoc.png"), ML, 2.1, 6.02, 2.3,
        "Helix Builder — chọn base (trái) → lắp ghép (phải), ảnh chụp thật")
add_pic(s, os.path.join(EV, "05_driver-harness-that.png"), 6.76, 2.1, 6.02, 2.3,
        "Driver: 35 bài qua harness pi-mono thật (trích log)")
add_pic(s, os.path.join(CH, "lap-ghep-cli-4-harness.png"), ML, 4.55, 6.02, 2.3,
        "Lắp ghép CLI: trích trường chính từ JSON gốc")
add_pic(s, os.path.join(EV, "16_file-truoc-sau.png"), 6.76, 4.55, 6.02, 2.3,
        "File trước/sau khi harness sửa (rebuild bước 1)")
notes(s, "Nguồn lắp ghép: assemble_opencode.json + assemble_hermes-agent.json (15/11/2026, gói bằng "
         "chứng 02_file-goc/); pi-mono + minimal lắp đạt 08/11 (303/176 atom, 96 cổng). Ảnh Builder "
         "là ảnh GHÉP từ 2 lần chụp thật 16/11/2026 bằng Playwright, mở file "
         "docs/site/harness-builder.html của repo upstream (bản sao local, không sửa), nối cạnh "
         "nhau, không sửa pixel nội dung nào. 210 lượt = bước 2 (70 lượt pi-mono) + bước 3 (140 "
         "lượt opencode + hermes-agent), lệnh run của CLI tác giả, chấm ngoài bằng test suite, 0 "
         "lỗi hạ tầng. Tổng lượt nhóm nay là 1.581 (xem slide 12); 210 lượt ở đây chỉ là pha tái lập bước 2–3. Bước 1 ghép nối: 1 bài bug-fix đạt cả 4 tiêu chí cam kết trước, transcript "
         "tool-call read + edit thật. Ảnh log trình bày lại từ file thật — không phải screenshot "
         "gốc. Lệnh assemble chính xác không file nào ghi lại nên slide không bịa.")

# ---------------- Slide 14: Quantitative comparison ----------------
s = slide_new("pipeline")
header(s, "Phần 3 — Tái thực nghiệm", "Đối chiếu định lượng: tác giả và nhóm", 14)
add_table(s, ML, 1.7, CW, 3.3,
          [["Hạng mục", "Tác giả (paper)", "Nhóm (đo thật)", "Đối chiếu"],
           ["Lắp ghép harness", "CLI + Builder, 65 ứng viên", "CLI upstream, 4 harness", "Cùng công cụ"],
           ["Chạy benchmark", "6.500 lượt, MiniMax", "1.581 lượt, Qwen 7B", "Nhỏ hơn nhiều"],
           ["Sibling record", "438 từ 200 slot", "74 từ trace nhóm", "Theo ý tưởng"],
           ["Train model", "Không (§9.5)", "LoRA SFT + DPO", "Mở rộng"],
           ["Tìm kiếm harness", "Chọn theo từng bài", "CLI không có lệnh search", "Mini-search 9 recipe (runner.mts)"]],
          [4.4, 2.6, 2.6, 2.63], font_size=13.5)
card(s, ML, 5.3, 6.02, 1.55, line=ACCENT)
txt(s, ML + 0.3, 5.5, 5.42, 0.3, [[("✓  KHỚP", 13, True, SKYBLUE)]])
txt(s, ML + 0.3, 5.85, 5.42, 0.8, [[("Lắp ghép + chạy qua CLI tác giả khớp: verification đạt, fingerprint khớp Builder, transcript tool-call thật.", 13.5, False, TEXT)]])
card(s, 6.76, 5.3, 6.02, 1.55, line=AMBER)
txt(s, 7.06, 5.5, 5.42, 0.3, [[("!  LỆCH", 13, True, AMBER_LT)]])
txt(s, 7.06, 5.85, 5.42, 0.8, [[("Quy mô nhỏ hơn nhiều; benchmark lớn chưa chạy lại — 94 fixture đã tái tạo; MiniMax không có.", 13.5, False, TEXT)]])
notes(s, "Số tác giả: bang-so-lieu-cho-slide.md §2 (§§6–7, Table 3). Số nhóm: log 12–20/11/2026 (1.581 lượt = 555 trước evolution + 707 evolution + 319 chương trình $6). 74 "
         "sibling record của nhóm làm từ trace của nhóm theo ý tưởng paper — KHÔNG qua pipeline của "
         "tác giả. CLI upstream kiểm tra 15/11: chỉ có run/assemble/validate/compose/task-parity, "
         "không có lệnh tìm kiếm/evolve.")

# ---------------- Slide 15: Extension results ----------------
s = slide_new("branch")
header(s, "Phần 3 — Mở rộng", "Kết quả mở rộng (1): LoRA vòng 2 tăng nhẹ, chưa có ý nghĩa", 15)
for i, (v, lab) in enumerate([("66/80 – 60/80", "Vòng 2: LoRA – base, bài đã học (p = 0,0703)"),
                              ("53/60 – 50/60", "Held-out v2: LoRA – base (p = 0,4531)"),
                              ("15/35 – 25/35", "Harness thật pi-mono: LoRA – base (p = 0,0063)")]):
    x = ML + i * (3.95 + 0.19)
    card(s, x, 1.6, 3.95, 1.0)
    rect(s, x, 1.6, 3.95, 0.07, ACCENT)
    txt(s, x + 0.3, 1.74, 3.35, 0.45, [[(v, 24, True, WHITE)]])
    txt(s, x + 0.3, 2.22, 3.35, 0.3, [[(lab, 11.5, False, MUTED)]])
card(s, ML, 2.72, 8.3, 3.28)
txt(s, ML + 0.3, 2.87, 7.7, 0.35, [[("Biểu đồ: Pass@1 vòng 2 theo từng harness mô phỏng (nhóm tự vẽ)", 14.5, True, WHITE)]])
px, py, pw, ph = add_pic_rect(s, os.path.join(CH, "round2_comparison_plot_toi.png"),
                              ML + 0.2, 3.27, 7.9, 2.63, frame=False)
# Numbered pointers (group annotations, slide shapes on top of the image):
# 1 = overlapping Wilson 95% CIs in the left panel; 2 = a LoRA bar (right panel).
marker(s, px + 0.30 * pw, py + 0.30 * ph, 1)
marker(s, px + 0.72 * pw, py + 0.42 * ph, 2)
rect(s, 8.75, 2.87, 0.02, 2.95, CARDLINE)
txt(s, 9.0, 2.87, 3.55, 0.35, [[("ĐỌC BIỂU ĐỒ", 11, True, SKYBLUE)]])
txt(s, 9.0, 3.27, 3.55, 2.55,
    [[("1. ", 13, True, AMBER_LT), ("Khoảng tin cậy 95% chồng lấn → chênh lệch chưa có ý nghĩa thống kê.", 13, False, TEXT)],
     [("2. ", 13, True, AMBER_LT), ("LoRA cao hơn nhẹ ở cả 4 harness mô phỏng, nhưng chưa chứng minh khái quát hóa.", 13, False, TEXT)],
     [("Khi có ghi file: LoRA 15/21 (71%), base 25/31 (81%) — khoảng cách nằm ở hành vi dùng tool.", 13, False, TEXT)]],
    space_after=8, line_spacing=1.1)
add_pic(s, os.path.join(CH, "train_excerpt_vong2.png"), ML, 6.12, 6.2, 0.78, frame=False)
txt(s, 6.5, 6.12, 6.28, 0.78,
    [[("Huấn luyện vòng 2 — chỉ trace live: LoRA r=16, α=32; SFT 9 bước 1,00→0,49; DPO 3 bước 0,693→0,660; seed 42.", 11.5, False, MUTED)]],
    anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.1)
notes(s, "Vòng 2 (12/11): 60/80 → 66/80, McNemar 7 thắng/1 thua, p = 0,0703; held-out v2 50/60 → "
         "53/60, p = 0,4531 — chưa chứng minh khái quát hóa. Qua harness thật (15–16/11): base "
         "thắng LoRA 25/35 so với 15/35, p = 0,0063; opencode 0/35 cả hai, hermes 0/35 so với 1/35. "
         "Caveat: mỗi ô 1 lần chạy — không kết luận LoRA nhìn chung kém hơn. Biểu đồ: Pass@1 + "
         "Wilson 95% CI, temp 0.0 baseline cells only, nhóm tự vẽ từ số vòng 2. Ảnh trích log "
         "train: các dòng mốc chính nguyên văn từ train_round2.log (12/11/2026, train "
         "20261112T082610, Modal A100); log đầy đủ là ảnh 03 trong gói bằng chứng. Sampling temp "
         "0,7 tạo cặp đối lập cho 4 bài (ROUND2_DESIGN.md). Fix từ trace thật + kiểm tra khái quát hóa: "
         "slide 16. Base pi-mono tự trôi 25→20→22→23/35 qua 4 lần chạy cùng giao thức (bước 2, fix, lặp lại bước 1, ablation bước 3) — chênh lệch dưới ~5 bài nằm trong nhiễu. Ablation SFT-only (bước 3): base 23/35, SFT-only 30/35, realtool 25/35, p = 0,1797 — không kết luận được; phát hiện sạch: sửa hành vi không cần DPO.")

# ---------------- Slide 16: Extension results (2) — fix + generalisation ----------------
# SYNC 18/11/2026: fix experiment (C1+C2 met) + generalisation check (G1+G2 met).
# Numbers from rebuild-fix-lora-tooluse/summary.json + generalisation-check-2026-11-18/summary.json.
s = slide_new("branch")
header(s, "Phần 3 — Mở rộng", "Kết quả mở rộng (2): fix từ trace thật, giữ được trên bài mới", 16)
for i, (v, lab) in enumerate([("0/35 • 0/15", "Text-only pi-mono, LoRA mới: 35 bài fix + 15 bài mới (C1, G1)"),
                              ("28/35 – 15/35", "Fix pi-mono: mới – cũ (p = 0,001)"),
                              ("13/15 – 10/15", "Bài mới pi-mono: mới – cũ (n = 15)")]):
    x = ML + i * (3.95 + 0.19)
    card(s, x, 1.6, 3.95, 1.0)
    rect(s, x, 1.6, 3.95, 0.07, ACCENT)
    txt(s, x + 0.3, 1.74, 3.35, 0.45, [[(v, 24, True, WHITE)]])
    txt(s, x + 0.3, 2.22, 3.35, 0.3, [[(lab, 11.5, False, MUTED)]])
card(s, ML, 2.72, 7.3, 3.28)
txt(s, ML + 0.3, 2.87, 6.7, 0.35, [[("Biểu đồ: Pass@1 sau fix, 3 harness thật (nhóm tự vẽ)", 14.5, True, WHITE)]])
add_pic(s, os.path.join(CH, "fix_passat1_3harness_toi.png"), ML + 0.2, 3.27, 6.9, 2.63, frame=False)
card(s, 8.04, 2.72, 4.74, 3.28)
txt(s, 8.34, 2.87, 4.14, 0.3, [[("BÀI MỚI (n = 15) — PASS@1", 11, True, SKYBLUE)]])
add_table(s, 8.34, 3.22, 4.14, 1.35,
          [["Harness", "Base", "Cũ", "Mới"],
           ["Pi Mono", "11", "10", "13"],
           ["OpenCode", "0", "0", "5"],
           ["Hermes", "1", "1", "6"]],
          [1.5, 0.82, 0.82, 1.0], font_size=12.5)
txt(s, 8.34, 4.7, 4.14, 0.55, [[("Text-only (base / cũ / mới): pi-mono 1 / 3 / 0; opencode 15 / 15 / 10; hermes 7 / 13 / 6.", 12, False, TEXT)]], line_spacing=1.1)
txt(s, 8.34, 5.28, 4.14, 0.65, [[("LoRA mới: SFT 40 + DPO 9 từ trace thật; SFT 1,15→0,40; DPO 0,69→0,57.", 11.5, False, MUTED)],
     [("G1 + G2 đạt trên pi-mono (tiêu chí đăng ký trước).", 11.5, True, SKYBLUE)]], space_after=4, line_spacing=1.1)
rect(s, ML, 6.12, CW, 0.78, CARD2, line=AMBER, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
rect(s, ML, 6.12, 0.07, 0.78, AMBER)
txt(s, ML + 0.3, 6.12, CW - 0.6, 0.78,
    [[("Gộp n = 30 (held3+held4): mới 26/30 vs cũ 17/30 (p = 0,0039). Adapter sạch (O2): 24/30 → 26/30 qua 2 lượt, text-only 0/30 — phán quyết ổn định.", 12.5, True, WHITE)]],
    anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.1)
notes(s, "Fix (18/11, thiết kế đăng ký trước, config A): adapter helix-lora-realtool, SFT 40 + DPO 9 "
         "từ trace harness thật (tool call viết lại dạng Hermes <tool_call>, tool_result bỏ — ghi "
         "chú §3 DESIGN.md sai về '[tool:...]', xem RUN_LOG); train SFT 15 bước 1,15→0,40, DPO 6 "
         "bước 0,69→0,57. Đánh giá 210 lượt: pi-mono mới 28/35 so với cũ 15/35 (McNemar p = 0,001) "
         "và base 20/35 (p = 0,0386); text-only 0/35 (C1 đạt); opencode 7/35, hermes 13/35. Caveat: "
         "dữ liệu train là trace của đúng 35 bài đánh giá. Khái quát hóa (18/11, G-đủ, 15 bài mới "
         "held3, kiểm tra test trước khi chạy GPU, không trùng 35 bài cũ; 135 lượt, 1 lần chạy lại "
         "do lỗi hạ tầng): G1 đạt — text-only pi-mono 0/15 (≤ 3/15) và thấp hơn LoRA cũ 3/15; G2 "
         "đạt — 13/15 so với 10/15 (McNemar p = 0,25, chưa có ý nghĩa; CI chồng lấn). Opencode mới "
         "5/15 (base/cũ 0/15); hermes mới 6/15 (base/cũ 1/15). LoRA cũ text-only 3/15 trên bài mới "
         "so với 14/35 trên bài đã thấy — không được nói khoảng cách 0-với-3 bằng 0-với-14. Gộp n = 30 (held3+held4): mới 26/30 vs cũ 17/30 (p = 0,0039); base 23/30. Chương trình $6 (20/11): adapter sạch (24 SFT + 5 DPO từ 20 bài train), 24/30 → 26/30 qua 2 lượt, text-only 0/30 cả hai; base 21/30 cả hai — phán quyết ổn định. Chi phí: "
         "fix +$2,45, khái quát hóa +$1,12; billed $0,00 cả hai.")

# ---------------- Slide 17: Deep analysis + negative results ----------------
s = slide_new("branch")
header(s, "Phần 3 — Phân tích sâu", "Phân tích sâu: cơ chế text-only và kết quả âm tính", 17)
for i, (t, img) in enumerate([("(a)  Cơ chế: LoRA ít dùng tool hơn", "helix_khong_dung_tool.png"),
                              ("(b)  Khi có ghi file, chênh lệch thu hẹp", "helix_pass_khi_ghi_file.png")]):
    x = ML + i * (6.02 + 0.19)
    card(s, x, 1.6, 6.02, 2.85)
    txt(s, x + 0.3, 1.78, 5.42, 0.35, [[(t, 15, True, WHITE)]])
    add_pic(s, os.path.join(CH, img), x + 0.3, 2.2, 5.42, 2.15, frame=False)
card(s, ML, 4.6, 7.3, 2.15)
add_pic(s, os.path.join(EV, "19_bang-ket-qua-3-harness.png"), ML + 0.1, 4.7, 7.1, 1.95, frame=False)
rect(s, 8.04, 4.6, 4.74, 2.15, CARD2, line=AMBER, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
rect(s, 8.04, 4.6, 0.07, 2.15, AMBER)
txt(s, 8.34, 4.78, 4.14, 0.3, [[("H3b: TỪ ÂM TÍNH ĐẾN FIX CÓ ĐIỀU KIỆN", 11, True, AMBER_LT)]])
txt(s, 8.34, 5.12, 4.14, 1.5,
    [[("Bước 2–3: H3b KHÔNG ủng hộ với LoRA vòng 2 (p = 0,0063; cả hai chạm sàn).", 12.5, True, WHITE)],
     [("Fix từ trace thật: H3b ủng hộ có điều kiện — 0/35, 28/35; bài mới 0/15, 13/15 (p = 0,25; n nhỏ). Cơ chế: dữ liệu sibling dạy viết code, không dạy hành vi tool.", 12.5, False, TEXT)]],
    space_after=6, line_spacing=1.1)
notes(s, "Cơ chế bước 2: LoRA không dùng tool ở 14/35 bài (text-only, file giữ nguyên seed → FAIL) "
         "so với base 4/35. Khi có ghi file: LoRA 15/21, base 25/31. Bước 3: cơ chế text-only tái "
         "lập và nặng hơn ở CẢ hai model — lựa chọn harness chi phối khác biệt model (opencode "
         "không-dùng-tool 35/35 cả hai; hermes 24/35 base, 29/35 LoRA; lần lật duy nhất là lcb_016, "
         "đã kiểm chứng). Bảng 3 harness: tổng hợp từ summary.json bước 2 (pi-mono) và bước 3 "
         "(opencode + hermes-agent) — ảnh 19 gói bằng chứng; không-dùng-tool của pi-mono đếm từ "
         "result.json, của 2 harness kia lấy từ no_tool_mechanism trong summary.json. Bảng này là số "
         "bước 2–3 (LoRA vòng 2); số sau fix và khái quát hóa ở slide 16. Tiến hóa (18/11): tách hành vi/chất lượng +37,14pp = 71% hành vi / 29% chất lượng (quan sát, không nhân quả); chẩn đoán harness — opencode text-only 169/185 do prompt, hermes 41% 'script fantasy', shim hiếm khi nút thắt (4/310); mini-search prompt opencode 0/10, prompt pi 4–7/10; SFT-only 30/35 vs realtool 25/35 (p = 0,1797, DPO chưa chứng minh); v6: hành vi không chuyển sang bài sửa lỗi (base 0/16, realtool 1/16; 30/32 file nguyên seed).")

# ---------------- Slide 18: Evolution (O6 sync 20/11/2026) ----------------
# New slide per O6-SYNC-PLAN.md §2 (+ $6 program results). Numbers recomputed
# 20/11/2026 from summary.json files: EVOLUTION_REPORT.md (18/11) +
# improvement-6usd-2026-11-20/{o2-clean-retrain,o3-opencode-prompt,
# o1-repeats,o5-v6-probe}/summary.json. Order per form: results -> evolution
# -> LIEN HE -> limits -> conclusion.
s = slide_new("branch")
header(s, "Phần 3 — Mở rộng", "Tiến hóa 6 bước: lặp lại được, khái quát hóa lên n = 30", 18)
for i, (v, lab) in enumerate([("26/30 – 17/30", "Bài mới gộp n = 30, pi-mono: mới – cũ (p = 0,0039)"),
                              ("4/4", "Phán quyết fix + gen lặp lại được (bước 1)"),
                              ("71% / 29%", "Tăng fix: hành vi / chất lượng (quan sát)")]):
    x = ML + i * (3.95 + 0.19)
    card(s, x, 1.6, 3.95, 1.0)
    rect(s, x, 1.6, 3.95, 0.07, ACCENT)
    txt(s, x + 0.3, 1.74, 3.35, 0.45, [[(v, 24, True, WHITE)]])
    txt(s, x + 0.3, 2.22, 3.35, 0.3, [[(lab, 11.5, False, MUTED)]])
card(s, ML, 2.72, 7.3, 3.28)
txt(s, ML + 0.3, 2.87, 6.7, 0.35, [[("TIẾN HÓA 6 BƯỚC (18/11)", 11, True, SKYBLUE)]])
bullets(s, ML + 0.3, 3.25, 6.7, 2.6,
        ["Lặp lại bước 1: cả 4 phán quyết đều lặp lại được — C2 29/35 vs 15/35 (p = 0,0005); G2 13/15 vs 9/15 (p = 0,2188).",
         "Gộp n = 30 (held3+held4): mới 26/30 vs cũ 17/30 (p = 0,0039); base 23/30 — nhánh cũ trôi 10/15→7/15 giữa hai cohort.",
         "Tách hành vi/chất lượng: +37,14pp = 71% hành vi / 29% chất lượng (quan sát, không nhân quả).",
         "Chẩn đoán harness: opencode text-only 169/185 do prompt; hermes 41% 'script fantasy'; shim hiếm khi nút thắt (4/310). Mini-search: prompt opencode 0/10, prompt pi 4–7/10."], size=12.5, gap=7)
card(s, 8.04, 2.72, 4.74, 3.28)
txt(s, 8.34, 2.87, 4.14, 0.3, [[("CHƯƠNG TRÌNH $6 (20/11)", 11, True, SKYBLUE)]])
bullets(s, 8.34, 3.25, 4.14, 2.6,
        ["Adapter sạch (O2): 24/30 → 26/30 qua 2 lượt, text-only 0/30 cả hai; base 21/30 cả hai.",
         "Opencode (O3): chỉ dẫn tường minh cứu hành vi (10/10 → 0/10) nhưng Pass vẫn 1/10.",
         "v6 (O5): V1 cứu tham gia 13–14/16, Pass 0/16; V2 không cứu (1–2/16)."], size=12.5, gap=7)
rect(s, ML, 6.12, CW, 0.78, CARD2, line=AMBER, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.1)
rect(s, ML, 6.12, 0.07, 0.78, AMBER)
txt(s, ML + 0.3, 6.12, CW - 0.6, 0.78,
    [[("Giới hạn: base trôi 25→20→22→23/35; nhánh cũ chưa lặp lại (O1 cắt realtool) — mọi so sánh một-lần-chạy chỉ mô tả.", 12.5, True, WHITE)]],
    anchor=MSO_ANCHOR.MIDDLE, line_spacing=1.1)
notes(s, "Tiến hóa 6 bước (18/11, EVOLUTION_REPORT.md): (1) lặp lại 345 lượt — cả 4 phán quyết "
         "lặp lại được (C1 0/35; C2 29/35 vs 15/35, p = 0,0005; G1 0/15 vs 5/15; G2 13/15 vs 9/15, "
         "p = 0,2188); base trôi 25→20→22/35. (2) Chẩn đoán harness offline — opencode do prompt "
         "8,9KB không nhắc công cụ sửa file; hermes 41% 'script fantasy'; shim là đường tool-call "
         "duy nhất (429 lượt, 0 native) nhưng hiếm khi nút thắt (4/310 lỗi parser). (3) Ablation "
         "SFT-only: base 23/35, SFT-only 30/35, realtool 25/35, p = 0,1797 — không kết luận được; "
         "sửa hành vi không cần DPO. (4a) Tách hành vi/chất lượng: +37,14pp = 71% hành vi / 29% "
         "chất lượng (quan sát, không nhân quả, không trích riêng); 0/336 lượt không-ghi-file nào "
         "pass. (4b) Mở rộng gen: held4 13/15 vs 7/15 (p = 0,0312); gộp n = 30: 26/30 vs 17/30 "
         "(p = 0,0039); nhánh cũ trôi 10/15→7/15 giữa hai cohort. (5) v6: base 0/16, realtool 1/16 "
         "(p = 1,0); 30/32 file nguyên seed — hành vi không chuyển sang bài sửa lỗi; fixture nhóm "
         "tái tạo, chỉ chấm public case. (6) Mini-search 9 recipe: R4 7/10 vs R0 6/10 (p = 1,0, "
         "nhiễu); mọi recipe prompt opencode 0/10, prompt pi 4–7/10; oracle 8/10 post-hoc. Chương "
         "trình $6 (20/11, logs improvement-6usd-2026-11-20/): O2 adapter sạch (24 SFT + 5 DPO từ "
         "20 bài train) 24/30 → 26/30 qua 2 lượt, text-only 0/30 cả hai, base 21/30 cả hai, "
         "McNemar p = 0,4531 rồi 0,0625 (khám phá); O3 chỉ dẫn opencode cứu hành vi (B1 0/10, B2 "
         "3/10 text-only so với R8 10/10) nhưng Pass 1/10 và 2/10; O1 lặp lại 90 ô (nhánh cũ cắt "
         "theo luật billing): mới gộp 50/60 vs base 42/60; base trôi 14/45 ô giữa hai lượt; O5 V1 "
         "cứu tham gia 13–14/16 (baseline bước 5: base 2/16, realtool 4/16 theo định nghĩa tham "
         "gia) nhưng Pass 0/16; V2 1–2/16. Tổng lượt nhóm nay là 1.581; chi phí $6: +$4,52, "
         "billed $0,00.")

# ---------------- Slide 19: LIEN HE (P8 — Trieu duyet 20/11/2026) ----------------
# P8 as drafted in de-xuat-chinh-slide-helix-theo-form-2026-11-19.md; citations
# verified 20/11/2026 via Semantic Scholar API (12 entries, 11 distinct titles,
# all 2026). No absolute total (citationCount endpoint rate-limited) — the slide
# says only "theo Semantic Scholar, tinh den 20/11/2026".
s = slide_new("chip")
header(s, "Liên hệ", "Liên hệ: HELIX dựa vào đâu, và ai đã dùng HELIX", 19)
card(s, ML, 1.6, 6.02, 4.5)
txt(s, ML + 0.3, 1.78, 5.42, 0.3, [[("HELIX DỰA VÀO ĐÂU (§8 + TÀI LIỆU THAM KHẢO)", 11, True, SKYBLUE)]])
bullets(s, ML + 0.3, 2.2, 5.42, 3.7,
        ["HarnessX v3 (Chen và cộng sự, 2026) + Recursive Harness Self-Improvement (Lee và cộng sự, 2026) — hai công trình gần nhất, cùng hỏi về cặp harness–model",
         "CLI-Anything — harness CLI (§8)",
         "SWE-agent (Yang và cộng sự, 2024) / ReAct (Yao và cộng sự, 2023) — giao diện tác tử–máy tính (§8.2)",
         "LiveCodeBench (Jain và cộng sự, 2025) + SWE-bench (Jimenez và cộng sự, 2024) — benchmark thực thi (§8.4)"], size=13, gap=10)
card(s, 6.76, 1.6, 6.02, 4.5)
txt(s, 7.06, 1.78, 5.42, 0.3, [[("AI ĐÃ TRÍCH DẪN HELIX", 11, True, SKYBLUE)]])
bullets(s, 7.06, 2.2, 5.42, 3.1,
        ["CoHARL — Co-Evolving Agent Policies and Executable Harnesses with RL (Jian-Wen Chen, 2026)",
         "Harnesses That Improve Themselves (D. Shah, 2026)",
         "Harness²: Recursive Agent Harnessing for an Open World (Rui-Yao Xu, 2026)",
         "Self-Evolving Coding Agents via Harness-Policy Optimization (Zhepei Wei, 2026)"], size=13, gap=10)
txt(s, 7.06, 5.35, 5.42, 0.55, [[("Theo Semantic Scholar, tính đến 20/11/2026 (không ghi tổng số tuyệt đối).", 11.5, False, MUTED)]], line_spacing=1.1)
rect(s, ML, 6.3, CW, 0.55, BLOCK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.3)
txt(s, ML, 6.3, CW, 0.55, [[("Tất cả đều là bài 2026 — ảnh hưởng tiếp theo của HELIX còn rất sớm (paper tháng 8/2026).", 13, True, WHITE)]],
    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "Vị trí theo form đã chốt: sau kết quả/phân tích, trước giới hạn/kết luận. Cột trái chỉ từ §8 + "
         "References của paper. Cột phải đã kiểm chứng 20/11/2026 qua Semantic Scholar API (citations "
         "endpoint, arXiv:2608.13951): 12 mục trả về, 11 tựa đề khác nhau, tất cả 2026; mục thứ 12 trùng "
         "tựa đề 'Self-Evolving Coding Agents', không tác giả/năm — có thể là bản trùng, không đếm riêng. "
         "Số citationCount chính thức chưa lấy được (endpoint paper bị giới hạn lượt, 'Too Many Requests') "
         "nên slide không ghi tổng số tuyệt đối. 7 bài còn lại (để trong ghi chú, không lên slide): "
         "'Auditing the Product, Not the Recursion'; 'More Programs or More Rolls?'; 'ScienceBuddy'; "
         "'RobustSGPO'; 'Aspire'; 'Recursive Self-Improvement through Multi-Agent Self-Supervision'; "
         "'Self-Evolving Coding Agents' (Hao Zhou, 2026). Tựa đề/năm/tác giả đầu lấy từ API, chưa mở từng "
         "bài kiểm chứng nội dung; tất cả đều là bài 2026, khả năng cao là preprint.")

# ---------------- Slide 20: Limits & future work ----------------
s = slide_new("loop")
header(s, "Phần 4 — Giới hạn", "Giới hạn của nhóm và hướng phát triển", 20)
lims17 = [("Mỗi ô 2 lần chạy (mới + base; cũ 1 lần)",
           "Ảnh hưởng: base trôi 14/45 ô giữa 2 lượt (O1); gen gộp 26/30 vs 17/30, p = 0,0039; lặp lại: mới 50/60 vs base 42/60."),
          ("Chỉ 1–3 harness thật",
           "Ảnh hưởng: lựa chọn harness chi phối kết quả — chưa khái quát hóa sang harness khác được."),
          ("Model 7B, bài tự viết",
           "Ảnh hưởng: khác xa MiniMax + 100 bài LCB của paper; số tuyệt đối không so trực tiếp được."),
          ("Judge cùng họ 7B",
           "Ảnh hưởng: kiểm tra 169 ô pass (167 sạch, 2 không đọc được) không chứng minh được không có test-fitting."),
          ("DPO 6 → 19 cặp không tăng",
           "Ảnh hưởng: bổ sung hàng 5 (65/80; 51/60) cho thấy thêm cặp DPO không cứu được chuyển giao."),
          ("Chưa chạy benchmark lớn",
           "Ảnh hưởng: V1 cứu tham gia v6 (13–14/16) nhưng Pass vẫn 0/16; V2 không cứu (1–2/16); MiniMax không có; benchmark lớn chưa chạy lại.")]
for i, (t, d) in enumerate(lims17):
    x = ML + (i % 2) * (6.02 + 0.19)
    y = 1.6 + (i // 2) * (1.42 + 0.12)
    card(s, x, y, 6.02, 1.42)
    rect(s, x, y, 0.07, 1.42, AMBER)
    txt(s, x + 0.3, y + 0.14, 5.42, 0.32, [[(t, 14.5, True, WHITE)]])
    txt(s, x + 0.3, y + 0.52, 5.42, 0.75, [[(d, 12.5, False, TEXT)]], line_spacing=1.05)
rect(s, ML, 6.3, CW, 0.55, BLOCK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.3)
txt(s, ML, 6.3, CW, 0.55, [[("Hướng phát triển:  mở rộng bài mới (held5)  •  đo chất lượng code tách khỏi hành vi  •  can thiệp sâu prompt v6", 13.5, True, WHITE)]],
    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "Mỗi giới hạn đều liên hệ trực tiếp tới một kết quả của nhóm (luật của thầy). Judge: rubric "
         "viết trước + heuristic trên 520 trace (0 hardcode/constant/placeholder trong các ô pass) + "
         "base-7B judge trên 169 ô pass (167 sạch, 0 nghi ngờ, 0 suy biến, 2 không đọc được; nhất "
         "trí 100% trên các ô đọc được) — judge cùng họ 7B nên KHÔNG phải bằng chứng không có "
         "test-fitting; không có double-rating của người. Bổ sung hàng 5 (15/11, commit 9e345eea): "
         "DPO 6→19 cặp theo luật đăng ký trước, retrain 20261115T114301 (DPO 9 bước 0,693→0,592), "
         "không tăng Pass@1: train 65/80 (so với 66/80, p = 1,0), held-out 51/60 (so với 53/60, "
         "p = 0,5) — adapter vòng 2 giữ nguyên là bản chính thức. Fix train từ trace của đúng 35 bài "
         "đánh giá nên không tự khẳng định khái quát hóa; kiểm tra khái quát hóa dựa vào 30 bài mới "
         "(held3 + held4, gộp 26/30 vs 17/30, p = 0,0039 trên pi-mono). Chương trình $6 (20/11): adapter sạch train từ 20 bài train (24 SFT + 5 DPO), 24/30 → 26/30 qua 2 lượt, text-only 0/30 cả hai; base 21/30 cả hai lượt; base trôi 14/45 ô giữa hai lượt; nhánh cũ chưa lặp lại (O1 cắt theo luật billing).")

# ---------------- Slide 21: Conclusion ----------------
s = slide_new("loop")
header(s, "Phần 4 — Kết luận", "Kết luận: trả lời từng câu hỏi nghiên cứu", 21)
concs = [("RQ1", "Tái lập lắp ghép: ĐƯỢC ỦNG HỘ", "CLI tác giả lắp đúng 4 harness: verification đạt, 96/96 cổng, fingerprint khớp Builder."),
         ("RQ2", "Chạy thật: ĐƯỢC ỦNG HỘ, có ranh giới", "1.581 lượt qua 3 harness thật bằng lệnh run; benchmark 6.500 lượt chưa chạy lại."),
         ("RQ3", "Mở rộng LoRA: CHỈ MỘT PHẦN", "H3a tăng nhẹ, chưa có ý nghĩa (p = 0,07; 0,45). H3b: không ủng hộ (LoRA vòng 2); ủng hộ có điều kiện (LoRA trace-thật: 28/35; bài mới gộp 26/30 vs 17/30).")]
for i, (n, t, d) in enumerate(concs):
    y = 1.7 + i * 1.35
    card(s, ML, y, 7.1, 1.17)
    rect(s, ML + 0.22, y + 0.3, 0.62, 0.56, ACCENT, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.2)
    txt(s, ML + 0.22, y + 0.3, 0.62, 0.56, [[(n, 12, True, WHITE)]], align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
    txt(s, ML + 1.05, y + 0.16, 5.8, 0.3, [[(t, 14, True, WHITE)]])
    txt(s, ML + 1.05, y + 0.5, 5.8, 0.55, [[(d, 12.5, False, TEXT)]], line_spacing=1.05)
card(s, 8.0, 1.7, 4.78, 3.87, fill=CARD2)
txt(s, 8.3, 1.9, 4.18, 0.3, [[("ĐÓNG GÓP CỦA NHÓM", 11, True, SKYBLUE)]])
bullets(s, 8.3, 2.3, 4.18, 3.0,
        ["Chạy lại được đồ của tác giả ở quy mô nhỏ, có bằng chứng đầy đủ",
         "Train LoRA thật — phần paper chưa làm (§9.5)",
         "Phát hiện mới: dữ liệu mô phỏng không chuyển sang harness thật — sửa được bằng dữ liệu trace thật (0/35; 0/15 bài mới)",
         "Báo cáo đầy đủ kết quả âm tính và giới hạn"], size=13.5, gap=10)
rect(s, ML, 5.85, CW, 0.8, BLOCK, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.12)
txt(s, ML, 5.85, CW, 0.8, [[("Take-home:  với model nhỏ, đơn vị chọn lọc là cặp model–harness — dữ liệu train phải khớp harness triển khai", 16, True, WHITE)]],
    align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE)
notes(s, "Trả lời từng RQ của nhóm (slide 7): RQ1 ủng hộ; RQ2 ủng hộ trong ranh giới đã nêu; RQ3 "
         "chỉ một phần — H3a chưa có ý nghĩa thống kê; H3b bị bác bỏ với LoRA vòng 2 nhưng được ủng hộ "
         "có điều kiện với LoRA trace-thật (slide 16). Câu trả lời cho "
         "'model có giỏi lên thật không?': trên dữ liệu hiện có, chưa kết luận được "
         "(claim-va-caveat.md). Điều chứng minh được: đồ của tác giả chạy lại được ở quy mô nhỏ, và "
         "phát hiện mới — dữ liệu mô phỏng không chuyển sang harness thật. Chương trình $6 (20/11): adapter sạch khái quát hóa ổn định qua 2 lượt (24/30 → 26/30, text-only 0/30); opencode: chỉ dẫn cứu hành vi nhưng Pass vẫn thấp (1/10); v6: V1 cứu tham gia, Pass 0/16.")

# ---------------- Slide 22: Thanks / References ----------------
s = slide_new("closing")
rect(s, 0, 0, 5.7, H, PANEL)
rect(s, 5.7, 0, 0.06, H, ACCENT)
txt(s, ML, 2.5, 4.7, 1.2, [[("Cảm ơn", 44, True, WHITE)], [("Q&A", 44, True, SKY)]])
txt(s, ML, 4.3, 4.7, 0.9, [[("Nhóm 19: Nguyễn Sỹ Việt — 24022758  •  Lê Quốc Triệu — 24022750", 14, True, WHITE)], [("24022750@vnu.edu.vn", 13, False, SKY)]])
txt(s, 6.3, 0.55, 6.48, 0.4, [[("TÀI LIỆU THAM KHẢO", 12, True, SKYBLUE)]])
refs = ["[1]  HELIX — Model–Harness Co-evolution, Fan & Huang (2026), arXiv:2608.13951",
        "[2]  HarnessX v3 (Chen và cộng sự, 2026) — công trình gần nhất về harness",
        "[3]  Recursive Harness Self-Improvement (Lee và cộng sự, 2026)",
        "[4]  SWE-agent (Yang và cộng sự, 2024) • ReAct (Yao và cộng sự, 2023)",
        "[5]  Repo nhóm: github.com/letrieu728/thucnghiemhelix (patch v2, 16 file)",
        "[6]  Gói bằng chứng: 19 ảnh + file gốc (lắp ghép CLI, transcript, log)"]
txt(s, 6.3, 1.05, 6.48, 2.6, [[(r, 13, False, TEXT)] for r in refs], space_after=10)
card(s, 6.3, 3.95, 6.48, 1.7, fill=CARD2, line=ACCENT)
txt(s, 6.6, 4.15, 5.88, 0.3, [[("PHỤ LỤC — DỮ LIỆU & CODE", 11, True, SKYBLUE)]])
txt(s, 6.6, 4.5, 5.88, 0.9, [[("Gói bằng chứng (19 ảnh + 16 file gốc): log deploy/train/đánh giá, lắp ghép CLI, transcript tool-call — xem trong thư mục bang-chung-thuc-nghiem-helix.", 13.5, False, TEXT)]])
txt(s, 6.3, 5.95, 6.48, 0.6, [[("Báo cáo HELIX (bản tối) v2  •  Vòng 2 (12/11) + rebuild (15–16/11) + fix, khái quát hóa & evolution (18/11) + chương trình $6 (20/11/2026)  •  Nguồn: xem Speaker Notes.", 11, False, MUTED)]])
notes(s, "Gói bằng chứng đầy đủ nằm trong thư mục bang-chung-thuc-nghiem-helix (19 ảnh + 16 file "
         "gốc + PDF 20 trang): ảnh 14 lắp ghép CLI, ảnh 15 transcript tool-call, ảnh 05 log driver, "
         "ảnh 19 bảng 3 harness. Kết quả fix + khái quát hóa: logs rebuild-fix-lora-tooluse/ và "
         "generalisation-check-2026-11-18/. Evolution: logs evolution-2026-11-18/ (EVOLUTION_REPORT.md). Chương trình $6: logs improvement-6usd-2026-11-20/ (O2/O3/O1/O5). Gói slide-kit vẫn ở chế độ riêng tư.")

outdir = os.path.expanduser("~/workspace/your_files/blueprint-16-slide")
os.makedirs(outdir, exist_ok=True)
out = os.path.join(outdir, "HELIX-16-slide_dien-du-lieu-that-toi-v2.pptx")
prs.save(out)
print(f"Saved {out} with {len(prs.slides.__iter__.__self__._sldIdLst)} slides")
