"""
SACA — Reusable widgets: SF (smooth-scroll frame), NavBar,
       voice_bar, progress_timeline, triage engine, temp_band.
"""
import tkinter as tk
from tkinter import Canvas, Frame, Label
from PIL import Image, ImageDraw, ImageTk
from constants import *
from helpers  import mkcard, pill, h2r, r2h, lerp
from tts      import speak

class SF(Frame):
    """Smooth-scroll frame with inertia. Works on Windows/Mac/Linux."""
    FRICTION = 0.86      # deceleration (0=instant stop, 1=never stops)
    SENSITIVITY = 0.35   # wheel sensitivity
    FPS_MS = 14          # ~71fps animation interval

    def __init__(self,parent,**kw):
        super().__init__(parent,bg=BG,**kw)
        self._cv  = Canvas(self,bg=BG,highlightthickness=0,bd=0)
        self._cv.pack(fill="both",expand=1)
        self.inner   = Frame(self._cv,bg=BG)
        self._win_id = None
        self._vel    = 0.0
        self._job    = None
        self._active = False
        self.after(10, self._init)

    def _init(self):
        self._win_id = self._cv.create_window(0, 0, window=self.inner, anchor="nw")
        self.inner.bind("<Configure>", self._on_content)
        self._cv.bind("<Configure>",   self._on_canvas)
        # Bind wheel on canvas
        self._cv.bind("<MouseWheel>",  self._wheel)
        self._cv.bind("<Enter>",       self._attach)
        self._cv.bind("<Leave>",       self._detach)
        self.inner.bind("<Enter>",     self._attach)

    def _on_content(self, e=None):
        self._cv.configure(scrollregion=self._cv.bbox("all"))

    def _on_canvas(self, e=None):
        if self._win_id:
            self._cv.itemconfig(self._win_id, width=self._cv.winfo_width())

    # Windows uses <MouseWheel> with delta in multiples of 120
    def _wheel(self, e):
        self._vel += -e.delta * self.SENSITIVITY
        self._vel  = max(-60, min(60, self._vel))
        if self._job is None:
            self._tick()

    def _attach(self, e=None):
        """Grab global mousewheel when mouse enters this scroll area."""
        self._active = True
        self._cv.bind_all("<MouseWheel>", self._wheel_global)

    def _detach(self, e=None):
        self._active = False
        self._cv.unbind_all("<MouseWheel>")

    def _wheel_global(self, e):
        """Only scroll if cursor is actually inside this canvas."""
        wx = self._cv.winfo_rootx(); wy = self._cv.winfo_rooty()
        ww = self._cv.winfo_width(); wh = self._cv.winfo_height()
        if wx <= e.x_root <= wx+ww and wy <= e.y_root <= wy+wh:
            self._wheel(e)

    def _tick(self):
        if abs(self._vel) < 0.4:
            self._vel = 0.0
            self._job = None
            return
        # Compute scrollregion and view height
        bbox = self._cv.bbox("all")
        if bbox:
            content_h = bbox[3] - bbox[1]
            view_h    = self._cv.winfo_height()
            if content_h > view_h:
                top   = self._cv.yview()[0]
                cur   = top * content_h
                new   = max(0, min(content_h - view_h, cur + self._vel))
                self._cv.yview_moveto(new / content_h)
        self._vel *= self.FRICTION
        self._job  = self.after(self.FPS_MS, self._tick)

# ══════════════════════════════════════════════════════════════════
# NAV BAR
# ══════════════════════════════════════════════════════════════════
class NavBar(Canvas):
    def __init__(self,parent,title,sub=None,back=None,accent=OCHRE):
        super().__init__(parent,height=76,bg=BG_ALT,highlightthickness=0,bd=0)
        self.pack(fill="x")
        self._t=title; self._s=sub; self._b=back; self._a=accent
        self.bind("<Configure>",self._draw)

    def _draw(self,e=None):
        self.delete("all"); w=self.winfo_width()
        if w<2: return
        nb=Image.new("RGB",(w,76),(int(h2r(BG_ALT)[0]),int(h2r(BG_ALT)[1]),int(h2r(BG_ALT)[2])))
        dr=ImageDraw.Draw(nb)
        r,g,b=h2r(self._a)
        dr.line([(0,74),(w,74)],fill=(r,g,b,255),width=3)
        dr.line([(0,72),(w,72)],fill=(r,g,b,80),width=1)
        self._bg=ImageTk.PhotoImage(nb)
        self.create_image(0,0,anchor="nw",image=self._bg)
        if self._b:
            self.create_text(36,38,text="← Back",font=("Segoe UI",11,"bold"),
                             fill=TXT3,anchor="center",tags="bk")
            self.tag_bind("bk","<Button-1>",lambda e:self._b())
            self.tag_bind("bk","<Enter>",lambda e:(self.configure(cursor="hand2"),self.itemconfig("bk",fill=self._a)))
            self.tag_bind("bk","<Leave>",lambda e:(self.configure(cursor=""),self.itemconfig("bk",fill=TXT3)))
        ty=28 if self._s else 38
        self.create_text(w//2,ty,text=self._t,font=("Segoe UI",15,"bold"),fill=TXT1,anchor="center")
        if self._s:
            self.create_text(w//2,54,text=self._s,font=("Segoe UI",9),fill=TXT3,anchor="center")

# ══════════════════════════════════════════════════════════════════
# TRIAGE
# ══════════════════════════════════════════════════════════════════
RISK={"Chest Pain":5,"Breathless":5,"Dizziness":3,"Fever":3,"Vomiting":3,
      "Stomach Pain":2,"Headache":2,"Cough":1,"Fatigue":1,
      "Skin Rash":1,"Back Pain":1,"Sore Throat":1}

def temp_band(t):
    """Classify temperature into clinical bands."""
    if t<=0: return "not recorded", 0
    if t<36.0: return "hypothermia (dangerously low)", 3
    if t<36.5: return "below normal (mild hypothermia)", 1
    if t<37.5: return "normal", 0
    if t<38.0: return "low-grade fever", 1
    if t<38.5: return "mild fever", 1
    if t<39.0: return "moderate fever", 2
    if t<39.5: return "high fever", 3
    if t<40.0: return "very high fever", 4
    return "dangerously high fever", 5

def triage(sym,days,sev,med,other,fever_temp,pain_type,breathe_scale,chills):
    s=RISK.get(sym,1)
    # Severity slider
    s+=int(sev*1.8)
    # Duration (days computed from date vs today)
    if days>14: s+=5
    elif days>10: s+=4
    elif days>5:  s+=2
    elif days>2:  s+=1
    # Medication not taken
    if not med: s+=1
    # Other areas affected
    if other: s+=2
    # Temperature band scoring
    _,temp_pts=temp_band(fever_temp)
    s+=temp_pts
    # Pain type
    if pain_type=="Sharp/Stabbing": s+=2
    elif pain_type=="Burning": s+=1
    # Breathing difficulty (weighted heavily)
    if breathe_scale>=8: s+=4
    elif breathe_scale>=6: s+=3
    elif breathe_scale>=4: s+=2
    elif breathe_scale>=2: s+=1
    # Chills = systemic infection signal
    if chills: s+=2
    return "severe" if s>=20 else "moderate" if s>=11 else "mild"

# ══════════════════════════════════════════════════════════════════
# APP
# ══════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════
# NLP BRIDGE — load Sai's module gracefully

# ══════════════════════════════════════════════════════════════════
# ACCESSIBLE UI HELPERS
# ══════════════════════════════════════════════════════════════════

def voice_bar(parent, text, bg=None, accent=SKY):
    """🔊 Tap to Hear strip — add to any screen for low-literacy users."""
    bg_ = bg or BG_ALT
    vf  = Frame(parent, bg=bg_, cursor="hand2")
    vf.pack(fill="x", pady=(0, 2))
    lbl = Label(vf, text="🔊   Tap to Hear  /  Dhukarr ga wäŋa",
                font=("Segoe UI", 12, "bold"), fg=accent, bg=bg_,
                pady=9, padx=18, cursor="hand2")
    lbl.pack(side="left")
    do = lambda e=None: speak(text)
    vf.bind("<Button-1>", do)
    lbl.bind("<Button-1>", do)
    return vf


def progress_timeline(parent, current_step, bg=BG_CARD):
    """4-step visual timeline: Body Part → Symptoms → How Bad → Advice."""
    steps = [("1", "Body Part"), ("2", "Symptoms"),
             ("3", "How Bad"),   ("4", "Advice")]
    tl    = Frame(parent, bg=bg)
    tl.pack(fill="x")
    inner = Frame(tl, bg=bg)
    inner.pack(pady=8)

    for i, (num, label) in enumerate(steps):
        is_done    = i < current_step
        is_current = i == current_step

        sz = 34
        cv = Canvas(inner, width=sz, height=sz, bg=bg,
                    highlightthickness=0, bd=0)
        cv.pack(side="left")

        if is_done:
            fill_col = GREEN;  txt = "✓"
        elif is_current:
            fill_col = SKY;    txt = num
        else:
            fill_col = BORDER2; txt = num

        rr, gg, bb = h2r(fill_col)
        cv.create_oval(2, 2, sz-2, sz-2,
                       fill=r2h(rr, gg, bb), outline="")
        cv.create_text(sz//2, sz//2, text=txt,
                       font=("Segoe UI", 11, "bold"),
                       fill="#FFFFFF", anchor="center")

        fc = TXT1 if is_current else (GREEN if is_done else TXT4)
        fw = "bold" if is_current else "normal"
        Label(inner, text=label,
              font=("Segoe UI", 10, fw),
              fg=fc, bg=bg, padx=3).pack(side="left")

        if i < len(steps) - 1:
            bc = GREEN if i < current_step else BORDER
            Frame(inner, width=28, height=3, bg=bc).pack(side="left", padx=4)

    return tl
