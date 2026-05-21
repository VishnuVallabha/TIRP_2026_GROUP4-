"""SACA — PIL card-drawing helpers used by S4_Questions.
   mk_when_card, mk_sev_card, mk_temp_card, mk_pain_card, mk_yn_card
"""
import tkinter as tk
from tkinter import Canvas, Frame, Label, Entry, StringVar, BooleanVar, IntVar
from PIL import Image, ImageDraw, ImageTk, ImageFilter
from constants import *
from helpers  import mkcard, pill, h2r, r2h, lerp
from widgets  import SF, NavBar, voice_bar, progress_timeline
from tts      import speak

def _draw_card(w, h, fill_col, border_col, radius=18, selected=False):
    img = Image.new("RGBA",(w,h),(0,0,0,0))
    dr  = ImageDraw.Draw(img)
    bw  = 4 if selected else 2
    dr.rounded_rectangle([2,2,w-3,h-3], radius=radius,
                          fill=fill_col, outline=border_col, width=bw)
    return img


# ══════════════════════════════════════════════════════════════════
# PROFESSIONAL PIL CARD DRAWERS — no emoji, pure vector drawing
# ══════════════════════════════════════════════════════════════════

def _card_base(w, h, fill_rgba, border_rgba, radius=20, selected=False):
    img = Image.new("RGBA",(w,h),(0,0,0,0))
    dr  = ImageDraw.Draw(img)
    # shadow
    if selected:
        sh = Image.new("RGBA",(w,h),(0,0,0,0))
        sh_dr = ImageDraw.Draw(sh)
        for i in range(6):
            a = int(40*(1-i/6))
            sh_dr.rounded_rectangle([i,i,w-1-i,h-1-i],radius=radius+2,
                                     outline=(0,0,0,a),width=1)
        img = Image.alpha_composite(img, sh)
        dr  = ImageDraw.Draw(img)
    bw = 3 if selected else 1
    dr.rounded_rectangle([2,2,w-3,h-3], radius=radius,
                          fill=fill_rgba, outline=border_rgba, width=bw)
    return img, dr

def _draw_face_pil(dr, cx, cy, expr, size=56):
    """Draw expressive face using PIL only."""
    r = size//2
    FACE_COLS = {
        "ok":       ((74,222,128),  (22,101,52)),
        "mild":     ((134,239,172), (22,101,52)),
        "moderate": ((253,224,71),  (133,77,14)),
        "bad":      ((251,146,60),  (154,52,18)),
        "severe":   ((248,113,113), (185,28,28)),
        "extreme":  ((220,38,38),   (127,29,29)),
    }
    fill, outline = FACE_COLS.get(expr, ((200,200,200),(100,100,100)))
    # head
    dr.ellipse([cx-r,cy-r,cx+r,cy+r], fill=fill+(255,), outline=outline+(255,), width=3)
    # eyebrows (angry for bad/severe)
    if expr in ("bad","severe","extreme"):
        dr.line([(cx-r//2,cy-r//3-4),(cx-r//6,cy-r//3)], fill=outline+(255,), width=3)
        dr.line([(cx+r//6,cy-r//3),(cx+r//2,cy-r//3-4)], fill=outline+(255,), width=3)
    # eyes
    er = max(4, r//6)
    for ex in [cx-r//3, cx+r//3]:
        if expr in ("severe","extreme"):
            # X eyes
            dr.line([(ex-er,cy-er-r//8),(ex+er,cy+er-r//8)], fill=outline+(255,), width=3)
            dr.line([(ex+er,cy-er-r//8),(ex-er,cy+er-r//8)], fill=outline+(255,), width=3)
        elif expr == "bad":
            dr.arc([ex-er,cy-r//4,ex+er,cy+er-r//8], 0,180, fill=outline+(255,), width=3)
        else:
            dr.ellipse([ex-er,cy-r//4,ex+er,cy-r//4+er*2],fill=outline+(255,))
    # mouth
    mw = r//2
    if expr in ("ok","mild"):
        dr.arc([cx-mw,cy+r//6,cx+mw,cy+r//2], 0,180, fill=outline+(255,), width=3)
    elif expr == "moderate":
        dr.line([(cx-mw,cy+r//3),(cx+mw,cy+r//3)], fill=outline+(255,), width=3)
    else:
        dr.arc([cx-mw,cy+r//4,cx+mw,cy+r//2+4], 180,0, fill=outline+(255,), width=3)

def _draw_thermometer_pil(dr, cx, cy, temp, height=60, width=16):
    """Draw thermometer with mercury level."""
    if   temp < 36.5: mc = (100,160,255)
    elif temp < 37.5: mc = (80,200,80)
    elif temp < 38.0: mc = (160,220,60)
    elif temp < 38.5: mc = (255,200,50)
    elif temp < 39.0: mc = (255,150,30)
    elif temp < 40.0: mc = (255,90,20)
    else:             mc = (220,30,30)
    bulb_r = width
    tube_top = cy - height//2
    tube_bot = cy + height//2 - bulb_r
    # tube outline
    dr.rounded_rectangle([cx-width//2, tube_top, cx+width//2, tube_bot],
                          radius=width//2,
                          fill=(220,220,220,255), outline=(160,160,160,255), width=2)
    # mercury fill
    fill_h = int((tube_bot - tube_top) * min(1, max(0,(temp-35)/7)))
    if fill_h > 2:
        dr.rounded_rectangle([cx-width//2+2, tube_bot-fill_h,
                               cx+width//2-2, tube_bot],
                              radius=width//2-2, fill=mc+(255,))
    # bulb
    dr.ellipse([cx-bulb_r, tube_bot-bulb_r//2,
                cx+bulb_r, tube_bot+bulb_r*3//2],
               fill=mc+(255,), outline=(160,160,160,255), width=2)
    # tick marks
    for i in range(4):
        ty = tube_top + int((tube_bot-tube_top)*i/4)
        dr.line([(cx+width//2, ty),(cx+width//2+6, ty)],
                fill=(160,160,160,200), width=1)

def _draw_pain_icon_pil(dr, cx, cy, pain_type, color, size=44):
    """Draw meaningful pain type icons."""
    c = color+(255,)
    lw = 3
    if pain_type == "Dull/Aching":
        # Concentric circles (dull wave)
        for r in [size//2, size//3, size//6]:
            dr.ellipse([cx-r,cy-r,cx+r,cy+r], outline=c, width=lw)
    elif pain_type == "Sharp/Stabbing":
        # Lightning bolt
        pts = [(cx-4,cy-size//2),(cx-14,cy-4),(cx+2,cy-4),
               (cx+4,cy+size//2),(cx+14,cy+4),(cx-2,cy+4)]
        dr.polygon(pts, fill=c)
    elif pain_type == "Burning":
        # Flame shape
        pts = [(cx,cy-size//2),(cx-size//4,cy),(cx-size//3,cy+size//4),
               (cx,cy+size//2),(cx+size//3,cy+size//4),(cx+size//4,cy)]
        dr.polygon(pts, fill=c)
        inner_c = (255,255,200,200)
        ipts=[(cx,cy-size//4),(cx-size//8,cy),(cx,cy+size//4),(cx+size//8,cy)]
        dr.polygon(ipts, fill=inner_c)
    elif pain_type == "Throbbing":
        # Heartbeat / pulse wave
        pts=[(cx-size//2,cy),(cx-size//3,cy),(cx-size//5,cy-size//3),
             (cx,cy+size//3),(cx+size//5,cy-size//3),(cx+size//3,cy),(cx+size//2,cy)]
        dr.line(pts, fill=c, width=lw+1)
    elif pain_type == "Pressure":
        # Downward arrows
        for ox in [-size//4, 0, size//4]:
            dr.polygon([(cx+ox,cy-size//3),(cx+ox-size//8,cy),(cx+ox+size//8,cy)], fill=c)
            dr.line([(cx+ox,cy),(cx+ox,cy+size//3)], fill=c, width=lw)
    elif pain_type == "None":
        # Checkmark in circle
        dr.ellipse([cx-size//2,cy-size//2,cx+size//2,cy+size//2],
                   outline=c, width=lw)
        dr.line([(cx-size//4,cy),(cx-size//8,cy+size//4),
                 (cx+size//3,cy-size//4)], fill=c, width=lw+1)

def _draw_yn_icon_pil(dr, cx, cy, is_yes, selected, size=54):
    """Draw YES checkmark or NO cross."""
    if is_yes:
        c = (255,255,255,255) if selected else (46,160,67,255)
        # Big checkmark
        dr.line([(cx-size//2,cy),(cx-size//6,cy+size//3),
                 (cx+size//2,cy-size//3)], fill=c, width=6)
    else:
        c = (255,255,255,255) if selected else (200,40,40,255)
        # Big X
        dr.line([(cx-size//3,cy-size//3),(cx+size//3,cy+size//3)], fill=c, width=6)
        dr.line([(cx+size//3,cy-size//3),(cx-size//3,cy+size//3)], fill=c, width=6)

def _draw_calendar_pil(dr, cx, cy, color, size=38):
    """Draw a calendar icon."""
    r,g,b = color
    hw = size//2
    # calendar body
    dr.rounded_rectangle([cx-hw,cy-hw//2,cx+hw,cy+hw],
                          radius=6, fill=(255,255,255,200),
                          outline=(r,g,b,255), width=2)
    # header bar
    dr.rounded_rectangle([cx-hw,cy-hw//2,cx+hw,cy-hw//2+12],
                          radius=6, fill=(r,g,b,255))
    # rings
    for rx in [cx-hw//2, cx+hw//2]:
        dr.rectangle([rx-2,cy-hw//2-4,rx+2,cy-hw//2+4],
                     fill=(r,g,b,255))
    # grid dots
    for dx in [-hw//3, 0, hw//3]:
        for dy_ in [4, 14]:
            dr.ellipse([cx+dx-3,cy+dy_-3,cx+dx+3,cy+dy_+3],
                       fill=(r,g,b,200))


# ── WHEN card ────────────────────────────────────────────────────
def mk_when_card(label, color_hex, selected, W=165, H=190):
    """Big, readable time-period card for Q1."""
    img, dr = _card_base(W, H,
        fill_rgba=h2r(color_hex)+(240,) if selected else (252,252,255,238),
        border_rgba=h2r(color_hex)+(255,),
        radius=24, selected=selected)
    c   = h2r(color_hex)
    fg  = (255,255,255) if selected else (30,30,50)
    ic_col = (255,255,255,55) if selected else (*c, 30)
    ic_out = (255,255,255,100) if selected else (*c, 180)

    # Time icon circle
    ic_r = 30
    dr.ellipse([W//2-ic_r, 16, W//2+ic_r, 16+ic_r*2],
               fill=ic_col, outline=ic_out, width=2)

    # Draw a clock icon for Today, calendar for others
    icon_key = "fullbody" if "Today" in label else "back"
    # Draw simple clock or calendar lines
    if "Today" in label:
        # Clock face
        dr.ellipse([W//2-ic_r+4, 20, W//2+ic_r-4, 20+ic_r*2-8],
                    outline=(*fg, 220), width=2)
        dr.line([W//2, 32, W//2, 38], fill=fg, width=2)
        dr.line([W//2, 38, W//2+10, 43], fill=fg, width=2)
        dr.ellipse([W//2-2, 36, W//2+2, 40], fill=fg)
    else:
        # Calendar icon
        cx_i, cy_i = W//2, 16+ic_r
        dr.rounded_rectangle([cx_i-ic_r+4, cy_i-ic_r+4,
                               cx_i+ic_r-4, cy_i+ic_r-4],
                              radius=4, outline=(*fg, 200), width=2)
        # Calendar header bar
        dr.rounded_rectangle([cx_i-ic_r+4, cy_i-ic_r+4,
                               cx_i+ic_r-4, cy_i-ic_r+12],
                              radius=4, fill=(*fg, 200))
        # Grid dots
        for gx in (-6, 0, 6):
            for gy in (6, 12):
                dr.ellipse([cx_i+gx-2, cy_i+gy-2, cx_i+gx+2, cy_i+gy+2], fill=fg)

    # Main label — large bold
    try:
        from PIL import ImageFont
        font_big = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 20)
        bb = dr.textbbox((0,0), label, font=font_big)
        tw = bb[2]-bb[0]
        dr.text((W//2-tw//2, 90), label, fill=fg, font=font_big)
    except Exception:
        dr.text((W//2-len(label)*5, 92), label, fill=fg)

    # Selected tick
    if selected:
        dr.ellipse([W//2-11, H-24, W//2+11, H-2],
                    fill=(*c, 220))
        try:
            from PIL import ImageFont
            ck_font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 14)
            dr.text((W//2-5, H-22), "✓", fill=(255,255,255), font=ck_font)
        except Exception:
            dr.text((W//2-5, H-20), "✓", fill=(255,255,255))
    return img

# ── SEVERITY
# ── SEVERITY card ─────────────────────────────────────────────────
def mk_sev_card(expr, label, selected, W=125, H=165):
    FILL = {
        "ok":       "#4ADE80","mild":    "#86EFAC",
        "moderate": "#FCD34D","bad":     "#FB923C",
        "severe":   "#EF4444","extreme": "#DC2626",
    }
    col = FILL.get(expr, "#888888")
    img, dr = _card_base(W, H,
        fill_rgba=h2r(col)+(230,) if selected else (248,248,252,220),
        border_rgba=h2r(col)+(255,),
        radius=18, selected=selected)

    # Face — centred in upper 60% of card
    face_size = int(W * 0.44)   # ~55px in 125w card — big and clear
    face_cy   = int(H * 0.38)   # sit in upper portion
    _draw_face_pil(dr, W//2, face_cy, expr, size=face_size)

    # Label text — number bold, description normal — in lower 40%
    fg = (255,255,255) if selected else (30,30,50)
    lines = label.split(chr(10))   # ["1", "Very Mild"]
    label_top = face_cy + face_size + 8

    try:
        from PIL import ImageFont
        font_num  = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 18)
        font_desc = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf",  13)
        fonts = [font_num, font_desc]
    except Exception:
        fonts = [None, None]

    for i, ln in enumerate(lines):
        y = label_top + i * 20
        if y > H - 8:
            break
        if fonts[min(i, 1)]:
            bb  = dr.textbbox((0,0), ln, font=fonts[min(i,1)])
            tw  = bb[2]-bb[0]
            dr.text((W//2 - tw//2, y), ln, fill=fg, font=fonts[min(i,1)])
        else:
            dr.text((W//2 - len(ln)*4, y), ln, fill=fg)

    if selected:
        dr.ellipse([W//2-6, H-14, W//2+6, H-3], fill=(255,255,255,220))
    return img

# ── TEMPERATURE card ──────────────────────────────────────────────
def mk_temp_card(temp, label, selected, W=120, H=158):
    if   temp < 36.5: col = "#64A3FF"
    elif temp < 37.5: col = "#4ADE80"
    elif temp < 38.0: col = "#A3E635"
    elif temp < 38.5: col = "#FCD34D"
    elif temp < 39.0: col = "#FB923C"
    elif temp < 40.0: col = "#F97316"
    else:             col = "#EF4444"
    img, dr = _card_base(W, H,
        fill_rgba=h2r(col)+(230,) if selected else (248,248,252,220),
        border_rgba=h2r(col)+(255,),
        radius=20, selected=selected)
    _draw_thermometer_pil(dr, W//2, 72, temp, height=80, width=14)
    fg = (255,255,255) if selected else (30,30,50)
    y = 120
    for ln in label.split(chr(10)):
        dr.text((W//2-len(ln)*4, y), ln, fill=fg)
        y += 17
    return img

# ── PAIN TYPE card ───────────────────────────────────────────────
def mk_pain_card(pain_type, selected, W=130, H=160):
    """Pain-type card with clear, meaningful icons."""
    COLS = {
        "Dull/Aching":    "#8B7355",
        "Sharp/Stabbing": "#EF4444",
        "Burning":        "#F97316",
        "Throbbing":      "#A855F7",
        "Pressure":       "#3B82F6",
        "None":           "#22C55E",
    }
    SHORT = {
        "Dull/Aching":    "Dull",
        "Sharp/Stabbing": "Sharp",
        "Burning":        "Burning",
        "Throbbing":      "Throb",
        "Pressure":       "Pressure",
        "None":           "None",
    }
    col = COLS.get(pain_type, "#888888")
    img, dr = _card_base(W, H,
        fill_rgba=h2r(col)+(235,) if selected else (250,250,255,228),
        border_rgba=h2r(col)+(255,),
        radius=22, selected=selected)
    cx, cy = W//2, 62
    IC = h2r(col) if not selected else (255,255,255)

    if pain_type == "Dull/Aching":
        # Concentric expanding circles = spreading ache
        for ri, alpha in [(28,60),(20,100),(12,160),(5,220)]:
            a = alpha if not selected else min(alpha+60, 255)
            dr.ellipse([cx-ri, cy-ri, cx+ri, cy+ri],
                        fill=(*IC, a), outline=(*IC, min(a+40,255)), width=1)

    elif pain_type == "Sharp/Stabbing":
        # Jagged spike / knife shape
        pts = [(cx, cy-28),(cx+7, cy-8),(cx+18, cy-12),
               (cx+8, cy+2),(cx+20, cy+18),(cx, cy+8),
               (cx-20, cy+18),(cx-8, cy+2),(cx-18, cy-12),
               (cx-7, cy-8)]
        dr.polygon(pts, fill=(*IC, 230), outline=(*IC, 255))

    elif pain_type == "Burning":
        # Flame shape
        pts = [(cx, cy-28),(cx+10, cy-14),(cx+14, cy),(cx+10, cy+6),
               (cx+5, cy-4),(cx+8, cy+14),(cx, cy+22),
               (cx-8, cy+14),(cx-5, cy-4),(cx-10, cy+6),
               (cx-14, cy),(cx-10, cy-14)]
        dr.polygon(pts, fill=(*IC, 230), outline=(*IC, 255))
        # Inner flame
        in_pts = [(cx, cy-12),(cx+5, cy-2),(cx+6, cy+10),
                  (cx, cy+16),(cx-6, cy+10),(cx-5, cy-2)]
        dr.polygon(in_pts, fill=(255,255,200,180 if not selected else 120))

    elif pain_type == "Throbbing":
        # ECG heartbeat pulse wave
        pts = [(cx-24, cy),(cx-16, cy),(cx-8, cy-22),
               (cx, cy+22),(cx+8, cy-12),(cx+16, cy),(cx+24, cy)]
        dr.line(pts, fill=(*IC, 230), width=4, joint="curve")
        # Heart shape above wave
        for hx in (cx-7, cx+7):
            dr.arc([hx-11, cy-40, hx+5, cy-26],
                    start=0, end=180, fill=(*IC, 200), width=3)
        dr.polygon([(cx-10, cy-30),(cx+10, cy-30),(cx, cy-16)],
                    fill=(*IC, 180))

    elif pain_type == "Pressure":
        # Weight/compression — arrows pressing down
        for ay in (-10, 0, 10):
            dr.polygon([(cx, cy+ay+10),(cx-10, cy+ay-4),(cx+10, cy+ay-4)],
                        fill=(*IC, 200), outline=(*IC, 255))
        # Flat surface below
        dr.rounded_rectangle([cx-22, cy+18, cx+22, cy+24],
                               radius=3, fill=(*IC, 200))

    elif pain_type == "None":
        # Clean circle with large tick
        dr.ellipse([cx-24, cy-24, cx+24, cy+24],
                    fill=(*IC, 40), outline=(*IC, 220), width=3)
        dr.line([cx-12, cy, cx-2, cy+12, cx+14, cy-14],
                fill=(*IC, 255), width=4, joint="curve")

    # Label
    lbl = SHORT.get(pain_type, pain_type)
    fg  = (255,255,255) if selected else (30,30,50)
    try:
        from PIL import ImageFont
        font = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 14)
        bbox = dr.textbbox((0,0), lbl, font=font)
        tw = bbox[2]-bbox[0]
        dr.text((W//2-tw//2, 110), lbl, fill=fg, font=font)
    except Exception:
        dr.text((W//2-len(lbl)*4, 112), lbl, fill=fg)

    if selected:
        dr.ellipse([W//2-7, H-18, W//2+7, H-4], fill=(255,255,255,220))
    return img

# ── YES / NO card ─────────────────────────────────────────────────
def mk_yn_card(is_yes, selected=False, W=270, H=250,
               sub_yes="Yes", sub_no="No"):
    """Large, accessible Yes/No card with dynamic sub-labels."""
    col     = "#22C55E" if is_yes else "#EF4444"
    txt     = "YES"     if is_yes else "NO"
    sub_txt = sub_yes   if is_yes else sub_no

    img, dr = _card_base(W, H,
        fill_rgba=h2r(col)+(238,) if selected else (250,250,255,228),
        border_rgba=h2r(col)+(255,),
        radius=32, selected=selected)

    # Icon circle (large)
    ic_r = 52
    ic_cx, ic_cy = W//2, 28+ic_r
    ic_fill = (255,255,255,55) if selected else (*h2r(col), 28)
    dr.ellipse([ic_cx-ic_r, ic_cy-ic_r, ic_cx+ic_r, ic_cy+ic_r],
               fill=ic_fill,
               outline=(255,255,255,90) if selected else (*h2r(col), 110),
               width=3)
    _draw_yn_icon_pil(dr, ic_cx, ic_cy, is_yes, selected, size=58)

    fg = (255,255,255) if selected else h2r(col)

    # YES / NO — big text
    try:
        from PIL import ImageFont
        font_big = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 28)
        font_sub = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 14)
        bbox = dr.textbbox((0,0), txt, font=font_big)
        tw = bbox[2]-bbox[0]
        dr.text((W//2-tw//2, 142), txt, fill=fg, font=font_big)
        # Sub label
        sub_fg = (255,255,255,210) if selected else (70,70,80)
        for i, ln in enumerate(sub_txt.split("|")):
            b2 = dr.textbbox((0,0), ln, font=font_sub)
            tw2 = b2[2]-b2[0]
            dr.text((W//2-tw2//2, 182+i*20), ln, fill=sub_fg, font=font_sub)
    except Exception:
        dr.text((W//2-20, 148), txt, fill=fg)
        sub_fg = (255,255,255,200) if selected else (80,80,80)
        for i,ln in enumerate(sub_txt.split("|")):
            dr.text((W//2-len(ln)*4, 184+i*18), ln, fill=sub_fg)

    if selected:
        dr.rounded_rectangle([4,4,W-5,H-5], radius=32,
                              outline=(255,255,255,80), width=3)
    return img

# alias used by S4
_make_yn_card = mk_yn_card


