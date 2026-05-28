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
def _draw_sun_icon(dr, cx, cy, r, col, selected):
    """HD sun icon — 8 pointed rays + glowing disc + highlight."""
    fg = (255,255,255) if selected else col
    # Soft glow halo
    dr.ellipse([cx-r-10,cy-r-10,cx+r+10,cy+r+10], fill=(*col,18))
    # 8 tapered rays
    for i in range(8):
        a  = math.radians(i*45)
        r1 = r + 7
        r2 = r + 20
        w  = 0.17
        x1=cx+r1*math.cos(a-w); y1=cy+r1*math.sin(a-w)
        x2=cx+r1*math.cos(a+w); y2=cy+r1*math.sin(a+w)
        x3=cx+r2*math.cos(a);   y3=cy+r2*math.sin(a)
        dr.polygon([(x1,y1),(x2,y2),(x3,y3)], fill=(*fg,210))
    # Sun disc
    dr.ellipse([cx-r,cy-r,cx+r,cy+r], fill=(*col,255), outline=(*col,255), width=2)
    # Shine highlight top-left
    hr = r//3
    dr.ellipse([cx-hr-3,cy-hr-3,cx-hr//2,cy-hr//2], fill=(255,255,255,130))


def _draw_moon_icon(dr, cx, cy, r, col, selected):
    """HD crescent moon + 2 small stars."""
    fg = (255,255,255) if selected else col
    bg = (255,255,255) if selected else (252,253,255)
    # Glow
    dr.ellipse([cx-r-8,cy-r-8,cx+r+8,cy+r+8], fill=(*col,20))
    # Full moon disc
    dr.ellipse([cx-r,cy-r,cx+r,cy+r], fill=(*col,255))
    # Crescent cut-out
    offset = int(r*0.42)
    cr     = int(r*0.86)
    dr.ellipse([cx-r+offset,cy-cr,cx+r+offset,cy+cr], fill=(*bg,255))
    # Stars
    for sx,sy,ss in [(cx+r-5,cy-r+6,5),(cx+r+5,cy+4,3)]:
        for a in range(4):
            ang = math.radians(a*90)
            x1=sx+(ss)*math.cos(ang); y1=sy+(ss)*math.sin(ang)
            x2=sx+(ss//2)*math.cos(ang+math.pi/4); y2=sy+(ss//2)*math.sin(ang+math.pi/4)
            dr.polygon([(sx,sy),(x1,y1),(x2,y2)], fill=(*fg,190))


def _draw_calendar_icon(dr, cx, cy, r, col, selected, filled_dots=2):
    """HD calendar with coloured header, binding rings, and dot grid."""
    fg  = (255,255,255) if selected else col
    body_bg = (255,255,255,210) if selected else (*col,18)
    L,T,R2,B = cx-r, cy-r+4, cx+r, cy+r
    # Body
    dr.rounded_rectangle([L,T,R2,B], radius=10, fill=body_bg,
                          outline=(*col,255), width=3)
    # Header band
    hdr_b = T + int((B-T)*0.33)
    dr.rounded_rectangle([L,T,R2,hdr_b], radius=10, fill=(*col,255))
    dr.rectangle([L,hdr_b-10,R2,hdr_b], fill=(*col,255))
    # Binding rings at top
    for rx in [cx - r//3, cx + r//3]:
        dr.ellipse([rx-4,T-7,rx+4,T+5],
                   fill=(*fg,255), outline=(*col,255), width=2)
    # Small date number circle in header
    dr.ellipse([cx-5,T+6,cx+5,T+16], fill=(255,255,255,180))
    # Dot grid
    dot_r  = max(3, r//8)
    xs     = [L+14, cx, R2-14]
    for row in range(3):
        filled = (row < filled_dots)
        for x in xs:
            y = hdr_b + 14 + row*int((B-hdr_b-10)/3)
            if y < B-5:
                dc = (*col,230) if filled else (*col,80)
                dr.ellipse([x-dot_r,y-dot_r,x+dot_r,y+dot_r], fill=dc)


def _draw_hourglass_icon(dr, cx, cy, r, col, selected):
    """HD hourglass — framed triangles + sand particles."""
    fg  = (255,255,255) if selected else col
    sand = (255,255,255,200) if selected else (*col,210)
    # Background glow
    dr.ellipse([cx-r-8,cy-r-8,cx+r+8,cy+r+8], fill=(*col,15))
    # Top filled triangle (full sand)
    tw = r-3; th = r-4
    dr.polygon([(cx-tw,cy-th),(cx+tw,cy-th),(cx,cy-2)], fill=(*col,240))
    # Bottom empty triangle (less sand)
    dr.polygon([(cx-tw//2,cy+th),(cx+tw//2,cy+th),(cx,cy+2)], fill=(*col,150))
    # Frame bars
    for y in [cy-th-4, cy+th+4]:
        dr.rounded_rectangle([cx-tw-3,y-3,cx+tw+3,y+3], radius=3, fill=(*fg,240))
    # Frame side lines
    dr.line([(cx-tw,cy-th),(cx,cy-2)], fill=(*fg,120), width=2)
    dr.line([(cx+tw,cy-th),(cx,cy-2)], fill=(*fg,120), width=2)
    # Falling sand particles
    for i,offset in enumerate([0,6,11]):
        r2 = max(2, 4-i)
        dr.ellipse([cx-r2,cy+offset-r2,cx+r2,cy+offset+r2], fill=sand)


def mk_when_card(label, color_hex, selected, W=190, H=230):
    """
    Redesigned HD time-period selection card.
    Icons: Sun (Today) | Moon (Yesterday) | Calendar (2-7 days) | Hourglass (Over a week)
    """
    def rgb(h):
        h = h.lstrip("#")
        return tuple(int(h[i:i+2],16) for i in (0,2,4))

    col = rgb(color_hex)

    if selected:
        fill_rgba   = (*col, 235)
        border_rgba = (*col, 255)
    else:
        fill_rgba   = (252, 253, 255, 250)
        border_rgba = (*col, 255)

    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    dr  = ImageDraw.Draw(img)

    # Drop shadow
    for i in range(6):
        a = int(28*(1-i/6))
        dr.rounded_rectangle([i+2,i+3,W-1-i,H-1-i], radius=26,
                              outline=(0,0,0,a), width=1)

    # Card base
    dr.rounded_rectangle([2,2,W-3,H-3], radius=26,
                          fill=fill_rgba,
                          outline=border_rgba,
                          width=3 if selected else 2)

    # Inner subtle highlight ring (top edge shimmer)
    if not selected:
        dr.rounded_rectangle([4,4,W-5,H-5], radius=25,
                              outline=(255,255,255,120), width=1)

    # Icon area — centred in upper 55% of card
    icx, icy = W//2, int(H*0.37)
    icon_r   = int(W * 0.22)

    if "Today" in label:
        _draw_sun_icon(dr, icx, icy, icon_r, col, selected)
    elif "Yesterday" in label:
        _draw_moon_icon(dr, icx, icy, icon_r, col, selected)
    elif "2" in label:
        _draw_calendar_icon(dr, icx, icy, icon_r, col, selected, filled_dots=2)
    else:
        _draw_hourglass_icon(dr, icx, icy, icon_r, col, selected)

    # Main label — bold, large
    try:
        from PIL import ImageFont
        try:
            font_big = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 22)
        except Exception:
            try:
                font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 22)
            except Exception:
                font_big = ImageFont.load_default()
        bb  = dr.textbbox((0,0), label, font=font_big)
        tw  = bb[2] - bb[0]
        lbl_col = (255,255,255,255) if selected else (*col,255)
        lbl_y   = int(H * 0.65)
        dr.text(((W-tw)//2, lbl_y), label, fill=lbl_col, font=font_big)
    except Exception:
        lbl_col = (255,255,255,255) if selected else (*col,255)
        dr.text((W//2-len(label)*6, int(H*0.65)), label, fill=lbl_col)

    # Yolŋu sub-label — italic smaller
    yo_map = {
        "Today":       "Dhuwali",
        "Yesterday":   "Warray",
        "2–7 days":    "Rua–lurrkun",
        "Over a week": "Week yan",
    }
    yo = yo_map.get(label, "")
    if yo:
        try:
            from PIL import ImageFont
            try:
                font_yo = ImageFont.truetype("C:/Windows/Fonts/segoeuii.ttf", 13)
            except Exception:
                try:
                    font_yo = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 13)
                except Exception:
                    font_yo = None
            yo_col = (255,255,255,170) if selected else (*col,160)
            yo_y   = int(H * 0.65) + 30
            if font_yo:
                bb2 = dr.textbbox((0,0), yo, font=font_yo)
                tw2 = bb2[2]-bb2[0]
                dr.text(((W-tw2)//2, yo_y), yo, fill=yo_col, font=font_yo)
            else:
                dr.text((W//2-len(yo)*4, yo_y), yo, fill=yo_col)
        except Exception:
            pass

    # Selected indicator — white pill at bottom
    if selected:
        pw, ph = 48, 12
        dr.rounded_rectangle([W//2-pw//2, H-20, W//2+pw//2, H-8],
                              radius=6, fill=(255,255,255,210))

    return img


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