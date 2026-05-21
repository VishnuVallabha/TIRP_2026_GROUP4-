"""
SACA — PIL drawing helpers and colour utilities.
Photo download/loading code removed — app uses HD vector icons instead.
"""
import os, sys, math, random
from PIL import Image, ImageDraw, ImageFont, ImageTk
from constants import *


def _dir():
    try: return os.path.dirname(os.path.abspath(sys.argv[0])) or os.getcwd()
    except: return os.getcwd()


def h2r(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def r2h(r, g, b):
    return "#{:02x}{:02x}{:02x}".format(int(r), int(g), int(b))


def lerp(c1, c2, t):
    r1,g1,b1 = h2r(c1) if isinstance(c1, str) else c1
    r2,g2,b2 = h2r(c2) if isinstance(c2, str) else c2
    return (int(r1+(r2-r1)*t), int(g1+(g2-g1)*t), int(b1+(b2-b1)*t))


def mkcard(w, h, bc=BORDER, fc=BG_CARD, bw=1, radius=12):
    img = Image.new("RGBA", (w, h), (0,0,0,0))
    dr  = ImageDraw.Draw(img)
    r,g,b = h2r(fc) if isinstance(fc, str) else fc
    dr.rounded_rectangle([0,0,w-1,h-1], radius=radius, fill=(r,g,b,255))
    rr,gg,bb = h2r(bc) if isinstance(bc, str) else bc
    dr.rounded_rectangle([0,0,w-1,h-1], radius=radius, outline=(rr,gg,bb,220), width=bw)
    return img


def pill(w, h, col, radius=None):
    radius = radius or h//2
    img = Image.new("RGBA", (w, h), (0,0,0,0))
    dr  = ImageDraw.Draw(img)
    r,g,b = h2r(col) if isinstance(col, str) else col
    dr.rounded_rectangle([0,0,w-1,h-1], radius=radius, fill=(r,g,b,255))
    return img


def load_cover(w, h):
    """Load aboriginal_cover.jpg for the splash screen; procedural fallback."""
    paths = [
        os.path.join(_dir(), "aboriginal_cover.jpg"),
        os.path.join(os.getcwd(), "aboriginal_cover.jpg"),
        "aboriginal_cover.jpg",
    ]
    for p in paths:
        if os.path.exists(p):
            try:
                img = Image.open(p).convert("RGB")
                return img.resize((w, h), Image.LANCZOS)
            except Exception:
                pass
    # Warm procedural gradient fallback
    img = Image.new("RGB", (w, h), (205, 127, 50))
    dr  = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        r = int(205-60*t); g = int(127-50*t); b = int(50-20*t)
        dr.line([(0,y),(w,y)], fill=(max(0,r), max(0,g), max(0,b)))
    return img


# ── Stubs kept so existing import lines don't break ──────────────
def download_photos():
    pass   # removed — no longer needed

def get_photo(key, size=170):
    return Image.new("RGB", (size, size), (240, 235, 225))

def _load_photo_from_disk(key, size=190):
    """Returns a blank placeholder — real photos no longer used."""
    return Image.new("RGB", (size, size), (240, 235, 225))


# ══════════════════════════════════════════════════════════════════
# HD ICON RENDERER — crisp PIL vector icons (no external files)
# ══════════════════════════════════════════════════════════════════
def draw_hd_icon(key, size=54, bg_col=None, fg_col="#FFFFFF"):
    """
    Crisp vector icon for a body region or symptom key.
    All drawn with PIL — no image files required.
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    dr  = ImageDraw.Draw(img)
    cx = cy = size // 2
    s  = size
    lw = max(2, s // 14)

    if bg_col:
        rr, gg, bb = h2r(bg_col)
        dr.rounded_rectangle([0, 0, s-1, s-1], radius=s//5,
                              fill=(rr, gg, bb, 230))

    fg = h2r(fg_col) if isinstance(fg_col, str) else fg_col

    if key in ("head", "headache"):
        dr.ellipse([cx-s//3, cy-s//3, cx+s//3, cy+s//6], outline=fg, width=lw)
        dr.arc([cx-s//4, cy, cx+s//4, cy+s//4], start=20, end=160, fill=fg, width=lw)
        for ex in (cx-s//9, cx+s//9):
            dr.ellipse([ex-s//16, cy-s//6, ex+s//16, cy-s//12], fill=fg)
        dr.line([cx, cy-s//3+lw, cx, cy-s//12], fill=fg, width=max(1,lw-1))

    elif key == "throat":
        dr.rounded_rectangle([cx-s//8, cy-s//3, cx+s//8, cy+s//3],
                               radius=s//8, outline=fg, width=lw)
        for tx in (cx-s//14, cx+s//14):
            dr.ellipse([tx-s//18, cy-s//10, tx+s//18, cy+s//10], fill=fg)

    elif key in ("chest",):
        ox, oy = cx, cy+s//16
        dr.polygon([(ox, oy+s//4),(ox-s//3, oy-s//8),(ox-s//3, oy-s//4),
                    (ox-s//6, oy-s//3),(ox, oy-s//8),(ox+s//6, oy-s//3),
                    (ox+s//3, oy-s//4),(ox+s//3, oy-s//8)], fill=fg)

    elif key == "stomach":
        dr.arc([cx-s//3, cy-s//4, cx+s//4, cy+s//3], start=230, end=90, fill=fg, width=lw)
        dr.arc([cx-s//8, cy-s//3, cx+s//3, cy+s//4], start=270, end=130, fill=fg, width=lw)

    elif key == "arms":
        dr.line([cx-s//4, cy-s//3, cx, cy], fill=fg, width=lw)
        dr.ellipse([cx-lw, cy-lw, cx+lw, cy+lw], fill=fg)
        dr.line([cx, cy, cx+s//4, cy+s//3], fill=fg, width=lw)
        dr.ellipse([cx+s//4-s//10, cy+s//3-s//10, cx+s//4+s//10, cy+s//3+s//10],
                    outline=fg, width=lw)
        dr.ellipse([cx-s//4-s//10, cy-s//3-s//10, cx-s//4+s//10, cy-s//3+s//10],
                    fill=fg)

    elif key == "legs":
        for dx in (-s//6, s//6):
            dr.line([cx+dx, cy-s//3, cx+dx*2//3, cy+s//3], fill=fg, width=lw)
            dr.ellipse([cx+dx-lw, cy-s//16, cx+dx+lw, cy+s//16], fill=fg)

    elif key == "back":
        for vy in range(cy-s//3, cy+s//3, s//7):
            dr.rounded_rectangle([cx-s//8, vy, cx+s//8, vy+s//9], radius=2, fill=fg)
        for ry, side in [(cy-s//8,-1),(cy-s//8,1),(cy+s//16,-1),(cy+s//16,1)]:
            x0=cx+side*s//8; x1=cx+side*s//3
            dr.arc([min(x0,x1), ry, max(x0,x1), ry+s//7],
                   start=200 if side==-1 else 340,
                   end=340 if side==-1 else 200,
                   fill=fg, width=max(1,lw-1))

    elif key in ("fullbody", "fever"):
        tx1,tx2 = cx-s//10, cx+s//10; ty1,ty2 = cy-s//3, cy+s//8
        dr.rounded_rectangle([tx1,ty1,tx2,ty2], radius=s//10, outline=fg, width=lw)
        dr.ellipse([cx-s//6,cy+s//8,cx+s//6,cy+s//3], outline=fg, width=lw)
        dr.ellipse([cx-s//8,cy+s//9,cx+s//8,cy+s//3-lw], fill=fg)
        dr.rounded_rectangle([tx1+lw,ty2-s//5,tx2-lw,ty2], radius=2, fill=fg)
        for tm in range(3):
            ty=ty1+s//10+tm*s//10; dr.line([tx2,ty,tx2+s//10,ty],fill=fg,width=max(1,lw-1))

    elif key == "breathless":
        for side in (-1, 1):
            dr.arc([cx+side*s//4-s//5, cy-s//4, cx+side*s//4+s//5, cy+s//3],
                   start=180, end=360, outline=fg, width=lw)
            dr.line([cx+side*s//4, cy-s//4, cx+side*s//4, cy+s//3], fill=fg, width=lw)
        dr.line([cx, cy-s//3, cx, cy-s//5], fill=fg, width=lw)
        dr.polygon([(cx,cy-s//3),(cx-s//10,cy-s//5+2),(cx+s//10,cy-s//5+2)], fill=fg)

    elif key == "dizziness":
        dr.ellipse([cx-s//5,cy-s//5,cx+s//5,cy+s//5], outline=fg, width=lw)
        for ang in (0,90,180,270):
            rad=math.radians(ang); sr=s//3; er=s//3+s//8
            ex=cx+int(sr*math.cos(rad)); ey=cy+int(sr*math.sin(rad))
            ex2=cx+int(er*math.cos(math.radians(ang+30)))
            ey2=cy+int(er*math.sin(math.radians(ang+30)))
            dr.line([ex,ey,ex2,ey2], fill=fg, width=lw)

    elif key == "fatigue":
        for fx,fy,fsz in [(cx-s//6,cy+s//4,s//4),(cx,cy+s//12,s//6),(cx+s//8,cy-s//8,s//8)]:
            fsz=max(4,fsz)
            dr.line([fx,fy,fx+fsz,fy],       fill=fg, width=max(1,lw-1))
            dr.line([fx+fsz,fy,fx,fy+fsz],   fill=fg, width=max(1,lw-1))
            dr.line([fx,fy+fsz,fx+fsz,fy+fsz],fill=fg,width=max(1,lw-1))
        dr.arc([cx-s//4,cy-s//4,cx+s//4,cy], start=0, end=180, outline=fg, width=lw)

    elif key == "rash":
        random.seed(42)
        for _ in range(12):
            rx=cx+random.randint(-s//3,s//3); ry=cy+random.randint(-s//3,s//3)
            rr2=random.randint(2,max(3,s//12))
            dr.ellipse([rx-rr2,ry-rr2,rx+rr2,ry+rr2], fill=fg)

    elif key == "vomiting":
        for wy in range(cy,cy+s//3,s//8):
            pts=[(wx, wy+(s//16 if (wx//(s//16))%2==0 else -s//16))
                 for wx in range(cx-s//3,cx+s//3,s//16)]
            if len(pts)>=2: dr.line(pts, fill=fg, width=max(1,lw-1))
        dr.polygon([(cx,cy-s//3),(cx-s//8,cy-s//6),(cx+s//8,cy-s//6)], fill=fg)
        dr.line([cx,cy-s//6,cx,cy], fill=fg, width=lw)

    else:  # generic plus
        dr.line([cx-s//3,cy,cx+s//3,cy], fill=fg, width=lw*2)
        dr.line([cx,cy-s//3,cx,cy+s//3], fill=fg, width=lw*2)

    return img
