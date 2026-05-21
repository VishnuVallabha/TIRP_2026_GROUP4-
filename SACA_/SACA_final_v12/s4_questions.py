"""SACA — S4_Questions: One-question-per-screen photo triage flow."""
import os
import tkinter as tk
from tkinter import Canvas, Frame, Label, Entry, StringVar, BooleanVar, IntVar
from PIL import Image, ImageDraw, ImageTk, ImageFilter
from constants import *
from helpers  import mkcard, pill, h2r, r2h, lerp, _dir
from widgets  import SF, NavBar, voice_bar, progress_timeline
from tts      import speak
from card_drawers import (_draw_card, _card_base, _draw_face_pil,
    _draw_thermometer_pil, _draw_pain_icon_pil, _draw_yn_icon_pil,
    _draw_calendar_pil, mk_when_card, mk_sev_card, mk_temp_card,
    mk_pain_card, mk_yn_card)
from triage import triage

class S4_Questions(Frame):
    """
    Clean question flow on a light/white background.
    Each question is shown as tappable image cards.
    One question at a time, navigate with NEXT button.
    """

    # Base questions — overridden per body part in on_show()
    # ── Exactly 6 questions — same for every body part ─────────────
    # Q1: When did it start?        → onset/duration
    # Q2: How bad is the pain?      → severity 1-10
    # Q3: Do you have a fever?      → temperature / infection
    # Q4: Can you breathe normally? → breathing / emergency
    # Q5: Feeling sick or dizzy?    → nausea + dizziness flag
    # Q6: Can you do your daily activities?  → functional impact
    QUESTIONS = [
        "when",
        "severity",
        "fever_yn",
        "breathing",
        "sick_dizzy",
        "medication",
    ]

    # Same 6 for every region — consistent, predictable, clinically complete
    REGION_QUESTIONS = {
        "head":     ["when", "severity", "fever_yn", "breathing", "sick_dizzy", "daily_activity"],
        "throat":   ["when", "severity", "fever_yn", "breathing", "sick_dizzy", "daily_activity"],
        "chest":    ["when", "severity", "fever_yn", "breathing", "sick_dizzy", "daily_activity"],
        "stomach":  ["when", "severity", "fever_yn", "breathing", "sick_dizzy", "daily_activity"],
        "arms":     ["when", "severity", "fever_yn", "breathing", "sick_dizzy", "daily_activity"],
        "legs":     ["when", "severity", "fever_yn", "breathing", "sick_dizzy", "daily_activity"],
        "back":     ["when", "severity", "fever_yn", "breathing", "sick_dizzy", "daily_activity"],
        "fullbody": ["when", "severity", "fever_yn", "breathing", "sick_dizzy", "daily_activity"],
    }

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app   = app
        self._step = 0
        self._refs = {}      # PhotoImage references — must stay alive
        self._last = None    # (lang, symptom) that was built

    def on_show(self, from_results=False):
        """
        from_results=True  → user pressed Back on results page, keep answers, show last Q
        from_results=False → fresh entry, reset everything
        """
        new_key = (self.app.lang.get(), self.app.symptom)

        if from_results and self._last == new_key:
            # Coming back from results — just redisplay, no reset
            for w in self.winfo_children():
                w.destroy()
            self._refs = {}
            self._build_bg()
            self._show_q()
            return

        # Fresh entry — reset all state
        self._last = new_key
        self._step = 0
        self.app.days_computed = 1
        self.app.fever_temp_v.set("37.0")
        self.app.breathe_v.set(1)
        self.app.chills_v.set(False)
        self.app.nausea_v.set(False)
        self.app.other_v.set(False)
        self.app.med_v.set(False)
        self.app.pain_type_v.set("None")
        if hasattr(self.app, "activity_v"):
            self.app.activity_v.set(3)
        region = getattr(self.app, "selected_body_part", None) or "fullbody"
        self.QUESTIONS = self.REGION_QUESTIONS.get(region, self.REGION_QUESTIONS["fullbody"])
        for w in self.winfo_children():
            w.destroy()
        self._refs = {}
        self._build_bg()
        self._show_q()

    # ── Clean gradient background ───────────────────────────────
    def _build_bg(self):
        # No blurred photo — clean light background for readability
        self._bg_cv = None   # unused, kept for compatibility

    def _redraw_bg(self, e=None):
        pass  # No blurred background

    # ── Show one question ────────────────────────────────────────
    def _show_q(self):
        # Destroy all widgets and rebuild
        for w in self.winfo_children():
            w.destroy()
        self._refs = {}

        q = self.QUESTIONS[self._step]
        W_SCREEN = self.winfo_width() or 980
        card_w   = min(860, W_SCREEN - 40)

        # ── Row 1: Timeline ──────────────────────────────────────
        tl_frame = Frame(self, bg=BG, height=56)
        tl_frame.pack(fill="x")
        tl_frame.pack_propagate(False)
        progress_timeline(tl_frame, current_step=2, bg=BG)

        # ── Row 2: Accent bar ────────────────────────────────────
        Frame(self, height=3, bg=OCHRE).pack(fill="x")

        # ── Row 3: Back | Step counter | Symptom name ────────────
        nav_row = Frame(self, bg=BG_ALT, height=36)
        nav_row.pack(fill="x")
        nav_row.pack_propagate(False)

        back_lbl = Label(nav_row, text="← Back",
                         font=("Segoe UI", 11, "bold"),
                         fg=SKY, bg=BG_ALT, cursor="hand2", padx=14)
        back_lbl.pack(side="left", pady=4)

        sym_lbl = Label(nav_row,
                        text=(self.app.symptom or "").upper(),
                        font=("Segoe UI", 10, "bold"),
                        fg=OCHRE, bg=BG_ALT, padx=14)
        sym_lbl.pack(side="right", pady=4)

        Label(nav_row,
              text=f"Question {self._step+1} of {len(self.QUESTIONS)}",
              font=("Segoe UI", 10, "bold"), fg=TXT3, bg=BG_ALT).pack(
              side="left", expand=1)

        def go_back():
            if self._step > 0:
                self._step -= 1
                self._show_q()
            else:
                method = self.app.input_method.get()
                if method == "photo":   self.app.go("S3_BodyPart")
                elif method == "speak": self.app.go("nlp_speak")
                elif method == "type":  self.app.go("nlp_type")
                else:                   self.app.go("S2_Method")
        back_lbl.bind("<Button-1>", lambda e: go_back())

        # ── Question card — centred, fills remaining space ────────
        outer = Frame(self, bg=BG)
        outer.pack(fill="both", expand=1, pady=6)

        pad_w = max(0, (W_SCREEN - card_w) // 2)
        if pad_w > 0:
            Frame(outer, bg=BG, width=pad_w).pack(side="left", fill="y")
            Frame(outer, bg=BG, width=pad_w).pack(side="right", fill="y")

        container = Frame(outer, bg=BG_CARD,
                          highlightthickness=1, highlightbackground=BORDER)
        container.pack(side="left", fill="both", expand=1)

        # Dispatch
        if   q == "when":           self._render_when(container, card_w)
        elif q == "severity":       self._render_severity(container, card_w)
        elif q == "fever_yn":       self._render_fever_yn(container, card_w)
        elif q == "breathing":      self._render_breath(container, card_w)
        elif q == "sick_dizzy":     self._render_sick_dizzy(container, card_w)
        elif q == "daily_activity": self._render_daily_activity(container, card_w)

        # NEXT/ANALYSE button at bottom of card — always visible
        self._draw_next_btn(container)

    # ── Helpers ──────────────────────────────────────────────────
    def _q_title(self, parent, text, sub):
        Label(parent, text=text,
              font=("Segoe UI",28,"bold"),
              fg=TXT1, bg=BG_CARD).pack(pady=(14,4))
        Label(parent, text=sub,
              font=("Segoe UI",15),
              fg=TXT3, bg=BG_CARD).pack(pady=(0,16))

    def _next_btn(self, parent):
        """Kept for compatibility — delegates to _draw_next_btn."""
        self._draw_next_btn(parent)

    def _draw_next_btn(self, parent):
        """Render NEXT/ANALYSE pill button at the bottom of parent."""
        is_last = (self._step == len(self.QUESTIONS)-1)
        lbl = "ANALYSE  →" if is_last else "NEXT  →"
        col = OCHRE if is_last else "#4ADE80"
        BW, BH = 320, 58
        # Separator line
        Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=24, pady=(8,0))
        # Button row
        btn_row = Frame(parent, bg=BG_CARD, height=80)
        btn_row.pack(fill="x")
        btn_row.pack_propagate(False)
        cv = Canvas(btn_row, width=BW, height=BH,
                    bg=BG_CARD, highlightthickness=0, bd=0, cursor="hand2")
        cv.pack(expand=1, anchor="center", pady=11)
        pil = pill(BW, BH, col, BH//2)
        self._refs[f"nb{self._step}"] = ImageTk.PhotoImage(pil)
        cv.create_image(0, 0, anchor="nw", image=self._refs[f"nb{self._step}"])
        cv.create_text(BW//2, BH//2, text=lbl,
                       font=("Segoe UI", 15, "bold"),
                       fill="#000000" if col==OCHRE else "#FFFFFF",
                       anchor="center")
        def click():
            if is_last:
                self.app.analyse()
            else:
                self._step += 1
                self._show_q()
        cv.bind("<Button-1>", lambda e: click())

    def _option_cv(self, parent, pil, key, cmd):
        """Create a clickable canvas option."""
        cv = Canvas(parent, width=pil.width, height=pil.height,
                    bg=BG_CARD, highlightthickness=0, bd=0,
                         cursor="hand2")
        cv.pack(side="left", padx=5, pady=4)
        self._refs[key] = ImageTk.PhotoImage(pil)
        cv.create_image(0,0,anchor="nw",image=self._refs[key])
        cv.bind("<Button-1>", lambda e: cmd(cv))
        return cv

    # ── Q0: WHEN ─────────────────────────────────────────────────
    def _render_when(self, parent, card_w):
        self._q_title(parent,
                      "When did it start?",
                      "Tap the best answer  ·  Nhaltjan warray ga djäma?")
        row = Frame(parent, bg=BG_CARD)
        row.pack(pady=12)
        OPTIONS = [
            ("Today",       0,  "#4ADE80"),
            ("Yesterday",   1,  "#60A5FA"),
            ("2–7 days",    4,  "#FB923C"),
            ("Over a week", 10, "#EF4444"),
        ]
        sel_idx = [0]
        self.app.days_computed = 0
        cvs = {}

        def pick(idx, val):
            sel_idx[0] = idx
            self.app.days_computed = max(1, val)
            for i2, cv2 in cvs.items():
                cv2.delete("all")
                lbl2, v2, bc2 = OPTIONS[i2]
                sel  = (i2 == idx)
                pil2 = mk_when_card(lbl2, bc2, sel)
                k2   = f"when_{i2}"
                self._refs[k2] = ImageTk.PhotoImage(pil2)
                cv2.create_image(0,0,anchor="nw",image=self._refs[k2])

        for i,(lbl,val,bc) in enumerate(OPTIONS):
            pil = mk_when_card(lbl, bc, i==0)
            k   = f"when_{i}"
            self._refs[k] = ImageTk.PhotoImage(pil)
            cv2 = Canvas(row, width=pil.width, height=pil.height,
                         bg=BG_CARD, highlightthickness=0, bd=0,
                         cursor="hand2")
            cv2.pack(side="left", padx=8, pady=4)
            cv2.create_image(0,0,anchor="nw",image=self._refs[k])
            cvs[i] = cv2
            cv2.bind("<Button-1>", lambda e,i_=i,v_=val: pick(i_,v_))


    def _render_severity(self, parent, card_w):
        self._q_title(parent,
                      "How bad does it feel? 😣",
                      "Tap the face that matches  ·  1 = Very mild   10 = Very bad")
        row = Frame(parent, bg=BG_CARD)
        row.pack(pady=12)
        LEVELS = [
            (1,  "ok",       "1\nVery Mild"),
            (3,  "mild",     "3\nMild"),
            (5,  "moderate", "5\nModerate"),
            (7,  "bad",      "7\nSevere"),
            (9,  "severe",   "9\nV.Severe"),
            (10, "extreme",  "10\nExtreme"),
        ]
        sel_idx = [2]  # default 5
        self.app.sev_v.set(5)
        cvs = {}

        def pick(idx, val):
            sel_idx[0] = idx
            self.app.sev_v.set(val)
            for i2,cv2 in cvs.items():
                cv2.delete("all")
                v2,e2,l2 = LEVELS[i2]
                pil2 = self._sev_card(e2, l2, i2==idx, W=125, H=165)
                k2   = f"sev_{i2}"
                self._refs[k2] = ImageTk.PhotoImage(pil2)
                cv2.create_image(0,0,anchor="nw",image=self._refs[k2])

        for i,(val,expr,lbl) in enumerate(LEVELS):
            pil = self._sev_card(expr, lbl, i==2, W=125, H=165)
            k   = f"sev_{i}"
            self._refs[k] = ImageTk.PhotoImage(pil)
            cv2 = Canvas(row, width=pil.width, height=pil.height,
                         bg=BG_CARD, highlightthickness=0, bd=0,
                         cursor="hand2")
            cv2.pack(side="left", padx=5)
            cv2.create_image(0,0,anchor="nw",image=self._refs[k])
            cvs[i] = cv2
            cv2.bind("<Button-1>", lambda e,i_=i,v_=val: pick(i_,v_))


    def _sev_card(self, expr, label, selected, W=120, H=158):
        return mk_sev_card(expr, label, selected, W, H)

    def _render_daily_activity(self, parent, card_w):
        """Q6 — Can you do your daily activities? 4 picture cards."""
        self._q_title(parent,
                      "Can you do your daily activities?",
                      "Eating  ·  Walking  ·  Looking after yourself  ·  Normal life")

        self.app.activity_v.set(3)   # default = yes, mostly normal
        row = Frame(parent, bg=BG_CARD)
        row.pack(pady=12)
        cvs = {}

        # (emoji, title, description, colour, activity_score)
        OPTIONS = [
            ("✓",  "Yes, fully",  "Doing everything\nnormally",    "#4ADE80", 4),
            ("~",  "Mostly yes",  "Slowing down\na little",        "#FCD34D", 3),
            ("!",  "Struggling",  "Hard to eat,\nwalk or move",    "#FB923C", 2),
            ("✗",  "No, cannot",  "Lying down,\nneed help",        "#EF4444", 1),
        ]
        sel_idx = [1]   # default = "Mostly yes"
        CW, CH = 185, 210

        def pick(idx):
            sel_idx[0] = idx
            self.app.activity_v.set(OPTIONS[idx][4])
            # Low activity score bumps triage severity
            self.app.other_v.set(OPTIONS[idx][4] <= 2)
            for i2, cv2 in cvs.items():
                for child in cv2.winfo_children(): child.destroy()
                cv2.delete("all")
                opt2 = OPTIONS[i2]
                sel2 = (i2 == idx)
                pil2 = self._activity_card(*opt2, sel2, CW, CH)
                k2 = f"act_{i2}"
                self._refs[k2] = ImageTk.PhotoImage(pil2)
                cv2.create_image(0, 0, anchor="nw", image=self._refs[k2])

        for i, opt in enumerate(OPTIONS):
            sel = (i == 1)
            pil = self._activity_card(*opt, sel, CW, CH)
            k = f"act_{i}"
            self._refs[k] = ImageTk.PhotoImage(pil)
            cv2 = Canvas(row, width=CW, height=CH, bg=BG_CARD,
                         highlightthickness=0, bd=0, cursor="hand2")
            cv2.pack(side="left", padx=10)
            cv2.create_image(0, 0, anchor="nw", image=self._refs[k])
            cvs[i] = cv2
            cv2.bind("<Button-1>", lambda e, i_=i: pick(i_))
            # Tkinter emoji label — reliable cross-platform


    def _activity_card(self, emoji, title, desc, col, score,
                       selected=False, W=185, H=210):
        """Activity card — uses PIL for background/border, tkinter for emoji."""
        from card_drawers import _card_base
        rr, gg, bb = h2r(col)
        img, dr = _card_base(W, H,
            fill_rgba=(rr, gg, bb, 230) if selected else (252, 252, 255, 238),
            border_rgba=(rr, gg, bb, 255),
            radius=22, selected=selected)
        fg = (255, 255, 255) if selected else (30, 30, 50)
        # Title
        try:
            from PIL import ImageFont
            fb = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 22)
            fs = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 14)
            bb3 = dr.textbbox((0, 0), title, font=fb)
            dr.text((W//2-(bb3[2]-bb3[0])//2, 60), title, fill=fg, font=fb)
            for ln_i, ln in enumerate(desc.split("\n")):
                bb4 = dr.textbbox((0, 0), ln, font=fs)
                dr.text((W//2-(bb4[2]-bb4[0])//2, 92+ln_i*18), ln, fill=fg, font=fs)
        except Exception:
            dr.text((W//2-len(title)*5, 62), title, fill=fg)
            for ln_i, ln in enumerate(desc.split("\n")):
                dr.text((W//2-len(ln)*4, 94+ln_i*16), ln, fill=fg)
        if selected:
            dr.ellipse([W//2-8, H-16, W//2+8, H-3], fill=(255, 255, 255, 220))
        # Store emoji for tkinter overlay (drawn in _render_daily_activity)
        img._emoji = emoji
        img._selected = selected
        img._col = col
        return img

    def _render_fever_yn(self, parent, card_w):
        """Q3 — Do you have a fever? Simple Yes/No with temperature context."""
        self._q_title(parent,
                      "Do you have a fever?  🌡",
                      "Is your body hot?  ·  Do you feel hotter than normal?")
        self.app.chills_v.set(False)   # reset; YES here sets fever flag
        self.app.fever_temp_v.set("37.0")
        row = Frame(parent, bg=BG_CARD)
        row.pack(pady=12)
        cvs = {}

        OPTIONS = [
            # (label_top, label_bot, colour, fever_temp, is_yes)
            ("No fever",   "I feel normal",        "#4ADE80", 37.0, False),
            ("Warm",       "Body feels a bit hot",  "#FCD34D", 37.6, True),
            ("Fever",      "Clearly feverish",      "#FB923C", 38.5, True),
            ("High fever", "Very hot / burning",    "#EF4444", 39.5, True),
        ]
        sel_idx = [0]

        CW, CH = 185, 220

        def pick(idx):
            sel_idx[0] = idx
            _, _, _, ft, is_fever = OPTIONS[idx]
            self.app.fever_temp_v.set(str(ft))
            self.app.chills_v.set(is_fever)
            for i2, cv2 in cvs.items():
                cv2.delete("all")
                pil2 = self._fever_card(*OPTIONS[i2][:4], i2 == idx, CW, CH)
                k2 = f"fv_{i2}"
                self._refs[k2] = ImageTk.PhotoImage(pil2)
                cv2.create_image(0, 0, anchor="nw", image=self._refs[k2])

        for i, (lbl_t, lbl_b, col, ft, _) in enumerate(OPTIONS):
            pil = self._fever_card(lbl_t, lbl_b, col, ft, i == 0, CW, CH)
            k = f"fv_{i}"
            self._refs[k] = ImageTk.PhotoImage(pil)
            cv2 = Canvas(row, width=CW, height=CH, bg=BG_CARD,
                         highlightthickness=0, bd=0, cursor="hand2")
            cv2.pack(side="left", padx=10)
            cv2.create_image(0, 0, anchor="nw", image=self._refs[k])
            cvs[i] = cv2
            cv2.bind("<Button-1>", lambda e, i_=i: pick(i_))


    def _fever_card(self, lbl_top, lbl_bot, col, temp, selected, W=185, H=220):
        """Visual card for fever question — thermometer + label."""
        from card_drawers import _card_base, _draw_thermometer_pil
        rr, gg, bb = h2r(col)
        img, dr = _card_base(W, H,
            fill_rgba=(rr, gg, bb, 230) if selected else (252, 252, 255, 238),
            border_rgba=(rr, gg, bb, 255),
            radius=22, selected=selected)
        fg = (255, 255, 255) if selected else (30, 30, 50)
        # Thermometer
        _draw_thermometer_pil(dr, W//2, 90, temp, height=90, width=16)
        # Labels
        try:
            from PIL import ImageFont
            fb = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 17)
            fs = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 12)
            bb2 = dr.textbbox((0,0), lbl_top, font=fb)
            dr.text((W//2-(bb2[2]-bb2[0])//2, 148), lbl_top, fill=fg, font=fb)
            bb3 = dr.textbbox((0,0), lbl_bot, font=fs)
            dr.text((W//2-(bb3[2]-bb3[0])//2, 172), lbl_bot, fill=fg, font=fs)
        except Exception:
            dr.text((W//2-len(lbl_top)*5, 148), lbl_top, fill=fg)
            dr.text((W//2-len(lbl_bot)*4,  172), lbl_bot, fill=fg)
        if selected:
            dr.ellipse([W//2-8, H-16, W//2+8, H-3], fill=(255, 255, 255, 220))
        return img

    def _render_sick_dizzy(self, parent, card_w):
        """Q5 — Feeling sick or dizzy? Two Yes/No cards side by side."""
        self._q_title(parent,
                      "Feeling sick or dizzy?  🤢",
                      "Nausea · Vomiting · Spinning · Light-headed")
        # Use nausea_v to store: No/Nausea/Dizzy/Both
        self.app.nausea_v.set(False)
        row = Frame(parent, bg=BG_CARD)
        row.pack(pady=12)
        cvs = {}

        OPTIONS = [
            # (emoji, label, sublabel, colour, nausea, dizzy)
            ("✓",  "No",           "Feeling OK",          "#4ADE80", False, False),
            ("~",  "Sick stomach", "Nausea or vomiting",  "#FCD34D", True,  False),
            ("!",  "Dizzy",        "Spinning or faint",   "#FB923C", False, True),
            ("✗",  "Both",         "Sick AND dizzy",      "#EF4444", True,  True),
        ]
        sel_idx = [0]
        CW, CH = 185, 200

        def pick(idx):
            sel_idx[0] = idx
            _, _, _, _, nausea, dizzy = OPTIONS[idx]
            self.app.nausea_v.set(nausea or dizzy)
            self.app.other_v.set(nausea or dizzy)
            for i2, cv2 in cvs.items():
                for child in cv2.winfo_children(): child.destroy()
                cv2.delete("all")
                opt2 = OPTIONS[i2]; sel2 = (i2 == idx)
                pil2 = self._sick_card(*opt2, sel2, CW, CH)
                k2 = f"sd_{i2}"
                self._refs[k2] = ImageTk.PhotoImage(pil2)
                cv2.create_image(0, 0, anchor="nw", image=self._refs[k2])

        for i, opt in enumerate(OPTIONS):
            pil = self._sick_card(*opt, i == 0, CW, CH)
            k = f"sd_{i}"
            self._refs[k] = ImageTk.PhotoImage(pil)
            cv2 = Canvas(row, width=CW, height=CH, bg=BG_CARD,
                         highlightthickness=0, bd=0, cursor="hand2")
            cv2.pack(side="left", padx=10)
            cv2.create_image(0, 0, anchor="nw", image=self._refs[k])
            cvs[i] = cv2
            cv2.bind("<Button-1>", lambda e, i_=i: pick(i_))


    def _sick_card(self, emoji, label, sublabel, col, nausea, dizzy,
                   selected=False, W=185, H=200):
        from card_drawers import _card_base
        rr, gg, bb = h2r(col)
        img, dr = _card_base(W, H,
            fill_rgba=(rr, gg, bb, 230) if selected else (252, 252, 255, 238),
            border_rgba=(rr, gg, bb, 255),
            radius=22, selected=selected)
        fg = (255, 255, 255) if selected else (30, 30, 50)
        # Labels only in PIL (emoji via tkinter overlay)
        try:
            from PIL import ImageFont
            fb = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 22)
            fs = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 14)
            bb3 = dr.textbbox((0,0), label, font=fb)
            dr.text((W//2-(bb3[2]-bb3[0])//2, 60), label,    fill=fg, font=fb)
            bb4 = dr.textbbox((0,0), sublabel, font=fs)
            dr.text((W//2-(bb4[2]-bb4[0])//2, 90), sublabel, fill=fg, font=fs)
        except Exception:
            dr.text((W//2-len(label)*5,    62), label,    fill=fg)
            dr.text((W//2-len(sublabel)*4, 90), sublabel, fill=fg)
        if selected:
            dr.ellipse([W//2-8, H-16, W//2+8, H-3], fill=(255, 255, 255, 220))
        img._emoji = emoji
        return img

    def _render_breath(self, parent, card_w):
        self._q_title(parent,
                      "Can you breathe OK? 💨",
                      "1 = Breathing fine  ·  10 = Cannot breathe")
        row = Frame(parent, bg=BG_CARD)
        row.pack(pady=12)
        OPTIONS = [
            (1,  "ok",       "1\nFine"),
            (3,  "mild",     "3\nSlight"),
            (5,  "moderate", "5\nModerate"),
            (7,  "bad",      "7\nDifficult"),
            (9,  "severe",   "9\nV. Hard"),
            (10, "extreme",  "10\nCannot"),
        ]
        sel_idx = [0]
        self.app.breathe_v.set(1)
        cvs = {}

        def pick(idx, val):
            sel_idx[0] = idx
            self.app.breathe_v.set(val)
            for i2,cv2 in cvs.items():
                cv2.delete("all")
                v2,e2,l2 = OPTIONS[i2]
                pil2 = self._sev_card(e2, l2, i2==idx, W=125, H=165)
                k2   = f"br_{i2}"
                self._refs[k2] = ImageTk.PhotoImage(pil2)
                cv2.create_image(0,0,anchor="nw",image=self._refs[k2])

        for i,(val,expr,lbl) in enumerate(OPTIONS):
            pil = self._sev_card(expr, lbl, i==0, W=125, H=165)
            k   = f"br_{i}"
            self._refs[k] = ImageTk.PhotoImage(pil)
            cv2 = Canvas(row, width=pil.width, height=pil.height,
                         bg=BG_CARD, highlightthickness=0, bd=0,
                         cursor="hand2")
            cv2.pack(side="left", padx=5)
            cv2.create_image(0,0,anchor="nw",image=self._refs[k])
            cvs[i] = cv2
            cv2.bind("<Button-1>", lambda e,i_=i,v_=val: pick(i_,v_))




# ══════════════════════════════════════════════════════════════════
