"""SACA — S5_Result  v6  — Matches the HTML mockup exactly.

Layout mirrors the mockup:
  ┌─────────────────────────────────────────────────────┐
  │  COLOURED HEADER  (outcome colour, pill badge, voice)│
  │  PROGRESS BAR     (outcome colour dots + lines)      │
  ├──────────────┬──────────────────────────────────────┤
  │  LEFT 280px  │  RIGHT (fills)                       │
  │  · Gauge     │  · Badge strip                       │
  │  · SEVERITY  │  · Message card (left accent strip)  │
  │    hero box  │  · WHAT TO DO NOW label              │
  │  · Yolŋu     │  · 4 action cards (coloured top bar) │
  │              │  · Contact strip                     │
  ├──────────────┴──────────────────────────────────────┤
  │  Save Report              Start Over                │
  │  ML badge                                           │
  └─────────────────────────────────────────────────────┘
"""
import math
from tkinter import Canvas, Frame, Label
from PIL import Image, ImageDraw, ImageTk
from constants import *
from helpers   import pill, h2r, r2h
from tts       import speak
from triage    import temp_band


class S5_Result(Frame):

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app   = app
        self._body = None
        self._refs = {}   # keeps all PhotoImage references alive

    # ── Per-outcome config ────────────────────────────────────────
    CFG = {
        "mild": {
            "label":       "MILD",
            "yo_label":    "MÄRR MÄKITJ",
            "outcome":     "MILD",
            "yo_outcome":  "MÄKITJ",
            "yo":          "Märr Mäkitj",
            "tag":         "LOW RISK",
            "yo_tag":      "YAKA DJORRA",
            "col":         "#00875A",
            "col_dark":    "#005C3D",
            "col_light":   "#E8F8F2",
            "gauge_bg":    "#E8F8F2",
            "emoji":       "😊",
            "msg":         "Rest at home. Monitor your symptoms.",
            "yo_msg":      "Nhuma yolŋu dhuwali. Ŋuli djäma ga buŋgawa.",
            "voice":       "Your result is mild. Rest at home and drink plenty of water.",
        },
        "moderate": {
            "label":       "MODERATE",
            "yo_label":    "MÄRR DJUY'YUN",
            "outcome":     "MODERATE",
            "yo_outcome":  "DJUY'YUN",
            "yo":          "Märr Djuy'yun",
            "tag":         "SEE A DOCTOR",
            "yo_tag":      "NHUMA CLINIC",
            "col":         "#C96A00",
            "col_dark":    "#8A4800",
            "col_light":   "#FFF3E0",
            "gauge_bg":    "#FFF3E0",
            "emoji":       "😟",
            "msg":         "Visit the Yirrkala clinic within 24 hours.",
            "yo_msg":      "Nhuma Yirrkala clinic dhuwali ga warray.",
            "voice":       "Your result is moderate. Please visit the clinic today.",
        },
        "severe": {
            "label":       "EMERGENCY",
            "yo_label":    "MÄRR DJORRA'",
            "outcome":     "CRITICAL",
            "yo_outcome":  "DJORRA'",
            "yo":          "Märr Djorra'",
            "tag":         "CALL 000 NOW",
            "yo_tag":      "000 DJÄMA ŊAYI",
            "col":         "#C0392B",
            "col_dark":    "#7B241C",
            "col_light":   "#FDEDEC",
            "gauge_bg":    "#FDEDEC",
            "emoji":       "🚨",
            "msg":         "Call 000 immediately. Do not wait.",
            "yo_msg":      "Nhuma 000 djäma ŋayi. Yaka warray.",
            "voice":       "EMERGENCY. Call triple zero right now. Do not wait.",
        },
    }

    STEPS = {
        "mild": [
            ("🛏", "Rest",        "Sleep · avoid heavy activity",  "Ŋunhi",       "Yolŋu ga ŋunhi"),
            ("💧", "Drink water", "Stay hydrated all day",          "Gäna",        "Gäna djäma dhuwali"),
            ("💊", "Panadol",     "Take for pain or fever",         "Märr-djorra", "Märr-djorra ga ŋunhi"),
            ("👁",  "Monitor",    "Return if symptoms worsen",      "Buŋgawa",     "Djäma ga nhuma"),
        ],
        "moderate": [
            ("🏥", "Go to clinic","Yirrkala clinic · 24 hrs",       "Clinic",      "Yirrkala clinic dhuwali"),
            ("👫", "Bring help",  "Take family with you",           "Yolŋu",       "Nhuma yolŋu djäma"),
            ("📋", "Tell all",    "How long and how bad",           "Dhäruk",      "Dhäruk ga nhaltjan"),
            ("💊", "Take meds",   "Follow all advice",              "Märr-djorra", "Märr-djorra nhuma"),
        ],
        "severe": [
            ("📞", "Call 000",   "Free · tell where you are",      "000 Djäma",   "000 djäma ŋayi"),
            ("🏥", "Go NOW",     "Hospital · don't wait",          "Hospital",    "Hospital ŋayi"),
            ("🧍", "Stay still", "Sit · breathe slowly",           "Ŋunhi",       "Ŋunhi ga dhu djäma"),
            ("👫", "Get help",   "Someone stay with you",          "Yolŋu",       "Yolŋu nhuma bäpa"),
        ],
    }

    # ─────────────────────────────────────────────────────────────
    def set_result(self, key):
        if self._body:
            self._body.destroy()
        self._refs = {}

        d   = self.CFG[key]
        col = d["col"]
        sym = self.app.symptom or "Symptom"
        ts  = getattr(self.app, "triage_ts", "") or ""
        sev = self.app.sev_v.get()

        # ML prediction — use pre-computed result from background thread
        # (avoids running ml_predict again on the main thread which causes freeze)
        _ml_label, _bname = None, None
        try:
            ml_res = getattr(self.app, "_ml_result", None)
            if ml_res:
                _ml_label, _, _, _bname = ml_res
        except Exception:
            pass

        # ── Root body ────────────────────────────────────────────
        self._body = Frame(self, bg=BG)
        self._body.place(relx=0, rely=0, relwidth=1, relheight=1)

        # ML strip — absolute bottom
        if _ml_label and _bname:
            Label(self._body,
                  text=f"🤖  {_bname}  ·  Prediction: {_ml_label.upper()}",
                  font=("Segoe UI", 8, "bold"),
                  bg="#1B2A3B", fg="#7EC8E3",
                  anchor="center").pack(fill="x", side="bottom")

        # Save / Start Over — above ML strip
        bot = Frame(self._body, bg=BG)
        bot.pack(side="bottom", fill="x", padx=16, pady=(4, 6))
        is_yo_btn = self.app.lang.get() == "Yolngu Matha"
        save_lbl  = "💾  Djäl Dhäruk" if is_yo_btn else "💾  Save Report"
        over_lbl  = "↩  Mala Djäma"  if is_yo_btn else "↩  Start Over"
        self._btn(bot, save_lbl, col,      self.app.save_report, "left")
        self._btn(bot, over_lbl, "#8899AA", self.app.reset,      "right")

        # ── HEADER ───────────────────────────────────────────────
        self._header(key, d, col, sym, ts)

        # ── PROGRESS BAR ─────────────────────────────────────────
        self._progress(col)

        # ── MAIN grid ────────────────────────────────────────────
        main = Frame(self._body, bg=BG)
        main.pack(fill="both", expand=True, padx=10, pady=(6, 2))
        main.columnconfigure(0, minsize=280, weight=0)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        # LEFT
        left = Frame(main, bg=BG)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self._left_column(left, key, d, col, sev)

        # RIGHT
        right = Frame(main, bg=BG)
        right.grid(row=0, column=1, sticky="nsew")
        self._right_column(right, key, d, col)

    # ─────────────────────────────────────────────────────────────
    # HEADER  — full-bleed coloured, pill badge, voice button
    # ─────────────────────────────────────────────────────────────
    def _header(self, key, d, col, sym, ts):
        hdr = Frame(self._body, bg=col)
        hdr.pack(fill="x")

        row = Frame(hdr, bg=col)
        row.pack(fill="x", padx=12, pady=(8, 4))

        # ← Back
        back = Label(row, text="← Back",
                     font=("Segoe UI", 11, "bold"),
                     fg="#FFFFFF", bg=col, cursor="hand2")
        back.pack(side="left")
        def _go_back():
            method = self.app.input_method.get()
            if method == "type":
                self.app.go("nlp_type")
            elif method == "speak":
                self.app.go("nlp_speak")
            else:
                # photo flow — back to visual question cards
                self.app._sc["S4_Questions"].on_show(from_results=True)
                self.app._sc["S4_Questions"].lift()
        back.bind("<Button-1>", lambda e: _go_back())

        # White pill badge — centre
        pill_f = Frame(row, bg="#FFFFFF", padx=12, pady=5)
        pill_f.pack(side="left", expand=True)
        is_yo_h = self.app.lang.get() == "Yolngu Matha"
        h_label = d.get("yo_label", d["label"]) if is_yo_h else d["label"]
        h_tag   = d.get("yo_tag",   d["tag"])   if is_yo_h else d["tag"]
        Label(pill_f,
              text=f"{d['emoji']}  {h_label}  —  {h_tag}",
              font=("Segoe UI", 13, "bold"),
              fg=col, bg="#FFFFFF").pack()

        # 🔊 Hear — right
        hear = Label(row, text="🔊 Hear",
                     font=("Segoe UI", 10, "bold"),
                     fg="#FFFFFF", bg=col, cursor="hand2")
        hear.pack(side="right")
        hear.bind("<Button-1>", lambda e: speak_lang(d["voice"]))

        # Subtitle
        Label(hdr,
              text=f"{sym}   ·   {ts}",
              font=("Segoe UI", 9),
              fg="#FFFFFF", bg=col).pack(pady=(0, 7))

        # Dark separator line
        Frame(hdr, height=2, bg=d["col_dark"]).pack(fill="x")

    # ─────────────────────────────────────────────────────────────
    # PROGRESS BAR — outcome-coloured
    # ─────────────────────────────────────────────────────────────
    def _progress(self, col):
        pb    = Frame(self._body, bg=BG_CARD)
        pb.pack(fill="x")
        inner = Frame(pb, bg=BG_CARD)
        inner.pack(pady=7)

        steps = ["Body Part", "Symptoms", "How Bad", "Advice"]
        for i, label in enumerate(steps):
            done    = i < 3
            current = i == 3

            sz = 26
            cv = Canvas(inner, width=sz, height=sz,
                        bg=BG_CARD, highlightthickness=0, bd=0)
            cv.pack(side="left")
            fill_c = col if (done or current) else BORDER2
            txt    = "✓" if done else str(i + 1)
            rr, gg, bb = h2r(fill_c)
            cv.create_oval(1, 1, sz-1, sz-1, fill=r2h(rr,gg,bb), outline="")
            cv.create_text(sz//2, sz//2, text=txt,
                           font=("Segoe UI", 9, "bold"),
                           fill="#FFFFFF", anchor="center")

            fw = "bold" if current or done else "normal"
            fc = col if (done or current) else TXT4
            Label(inner, text=label,
                  font=("Segoe UI", 9, fw),
                  fg=fc, bg=BG_CARD, padx=2).pack(side="left")

            if i < 3:
                bc = col if done else BORDER
                Frame(inner, width=20, height=2, bg=bc).pack(side="left", padx=3)

    # ─────────────────────────────────────────────────────────────
    # LEFT COLUMN — gauge + severity hero + yolŋu
    # ─────────────────────────────────────────────────────────────
    def _left_column(self, parent, key, d, col, sev):
        # Gauge
        G = 262
        cv = Canvas(parent, width=G, height=G,
                    bg=BG, highlightthickness=0, bd=0)
        cv.pack()
        self._gauge(cv, key, d, col, sev, G)

        # Severity hero box — solid colour fill, white text
        hero = Frame(parent, bg=col, pady=10)
        hero.pack(fill="x", padx=4, pady=(6, 0))
        Label(hero,
              text=f"SEVERITY  {sev} / 10",
              font=("Segoe UI", 22, "bold"),
              fg="#FFFFFF", bg=col).pack()
        dots = "●" * sev + "○" * (10 - sev)
        Label(hero, text=dots,
              font=("Segoe UI", 14),
              fg="#FFFFFF", bg=col).pack(pady=(3, 0))
        Label(hero, text=d["outcome"],
              font=("Segoe UI", 17, "bold"),
              fg="#FFFFFF", bg=col).pack(pady=(3, 0))

        # Yolŋu italic line
        yo = {"mild":     "Märr Mäkitj  —  dhäwu dhäruk",
              "moderate": "Märr Djuy'yun  —  nhä ga nhuma?",
              "severe":   "Märr Djorra'  —  000 ga wäŋa!"}[key]
        Label(parent, text=yo,
              font=("Segoe UI", 10, "italic"),
              fg=TXT3, bg=BG).pack(pady=(7, 0))

    # ─────────────────────────────────────────────────────────────
    # RIGHT COLUMN
    # ─────────────────────────────────────────────────────────────
    def _right_column(self, parent, key, d, col):
        # ── Badge strip ───────────────────────────────────────────
        is_yo_b  = self.app.lang.get() == "Yolngu Matha"
        b_label  = d.get("yo_label", d["label"]) if is_yo_b else d["label"]
        b_tag    = d.get("yo_tag",   d["tag"])   if is_yo_b else d["tag"]
        badge = Frame(parent, bg=col)
        badge.pack(fill="x", pady=(0, 7))
        Label(badge,
              text=f"  {d['emoji']}   {b_label}  —  {b_tag}",
              font=("Segoe UI", 18, "bold"),
              fg="#FFFFFF", bg=col, pady=9).pack(side="left")
        Label(badge,
              text=f"  {d['yo']}",
              font=("Segoe UI", 11, "italic"),
              fg="#FFFFFF", bg=col, pady=9).pack(side="left")

        # ── Message card — left accent strip ─────────────────────
        card = Frame(parent, bg=d["col_light"],
                     highlightthickness=2, highlightbackground=col)
        card.pack(fill="x", pady=(0, 7))
        Frame(card, bg=col, width=6).pack(side="left", fill="y")
        body = Frame(card, bg=d["col_light"])
        body.pack(side="left", fill="both", expand=True, padx=12, pady=10)
        is_yo_m  = self.app.lang.get() == "Yolngu Matha"
        msg_text = d.get("yo_msg", d["msg"]) if is_yo_m else d["msg"]
        Label(body,
              text=msg_text,
              font=("Segoe UI", 13, "bold"),
              fg=d["col_dark"], bg=d["col_light"],
              justify="left", wraplength=600, anchor="w").pack(anchor="w")
        if is_yo_m:
            Label(body,
                  text=d["msg"],
                  font=("Segoe UI", 11), fg=d["col_dark"], bg=d["col_light"],
                  justify="left", wraplength=600, anchor="w").pack(anchor="w", pady=(2,0))
        facts = self._facts(key)
        if facts:
            Label(body, text=facts,
                  font=("Segoe UI", 10),
                  fg=TXT2, bg=d["col_light"],
                  justify="left", wraplength=600, anchor="w").pack(anchor="w", pady=(4, 0))

        # ── WHAT TO DO NOW ────────────────────────────────────────
        is_yo_w  = self.app.lang.get() == "Yolngu Matha"
        what_lbl = "NHUMA DJÄMA ŊAYI?" if is_yo_w else "WHAT TO DO NOW"
        Label(parent,
              text=what_lbl,
              font=("Segoe UI", 10, "bold"),
              fg=d["col_dark"], bg=BG,
              pady=0).pack(anchor="w", pady=(0, 4))

        cards = Frame(parent, bg=BG)
        cards.pack(fill="x")
        is_yo_c = self.app.lang.get() == "Yolngu Matha"
        for step_data in self.STEPS[key]:
            emoji = step_data[0]
            title = step_data[3] if is_yo_c and len(step_data) > 3 else step_data[1]
            desc  = step_data[4] if is_yo_c and len(step_data) > 4 else step_data[2]
            self._card(cards, emoji, title, desc, col)

        # ── Contact strip ─────────────────────────────────────────
        is_yo_ct = self.app.lang.get() == "Yolngu Matha"
        ct_text = {
            "mild": (
                "📞  Yirrkala Clinic: (08) 8987 1000  ·  Djäma ga nhuma"
                if is_yo_ct else
                "📞  Yirrkala Clinic: (08) 8987 1000  ·  Mon–Fri 8am–5pm"
            ),
            "moderate": (
                "📞  Yirrkala Clinic: (08) 8987 1000  ·  Gove Hospital (08) 8987 0211"
                if is_yo_ct else
                "📞  Yirrkala Clinic: (08) 8987 1000  ·  After hours: Gove Hospital (08) 8987 0211"
            ),
            "severe": (
                "📞  000  (Märr Djorra)   ·   Flying Doctor: 1800 625 800  (Yaka märr-djorra)"
                if is_yo_ct else
                "📞  000  (Emergency)   ·   Flying Doctor: 1800 625 800  (Free · 24 hrs)"
            ),
        }[key]
        ct = Frame(parent, bg=col)
        ct.pack(fill="x", pady=(7, 0))
        Label(ct, text=ct_text,
              font=("Segoe UI", 11, "bold"),
              fg="#FFFFFF", bg=col,
              padx=12, pady=9).pack(anchor="w")

    # ─────────────────────────────────────────────────────────────
    # ACTION CARD — coloured top bar + emoji + title + desc
    # ─────────────────────────────────────────────────────────────
    def _card(self, parent, emoji, title, desc, col):
        f = Frame(parent, bg="#FFFFFF",
                  highlightthickness=1, highlightbackground=BORDER)
        f.pack(side="left", fill="x", expand=True, padx=2)
        Frame(f, bg=col, height=4).pack(fill="x")        # coloured top stripe
        Label(f, text=emoji,
              font=("Segoe UI Emoji", 24), bg="#FFFFFF").pack(pady=(8, 0))
        Label(f, text=title,
              font=("Segoe UI", 10, "bold"),
              fg=col, bg="#FFFFFF").pack(pady=(2, 0))
        Label(f, text=desc,
              font=("Segoe UI", 8),
              fg=TXT3, bg="#FFFFFF",
              wraplength=135, justify="center").pack(pady=(2, 9))

    # ─────────────────────────────────────────────────────────────
    # Called from background thread — pure PIL, no Tkinter
    # ─────────────────────────────────────────────────────────────
    def build_gauge_image(self, key, sev, size=262):
        """Pre-render gauge as PIL Image in background thread (thread-safe)."""
        d = self.CFG[key]

        def rgb(h):
            h = h.lstrip("#")
            return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

        cx = cy  = size // 2
        R_outer  = int(size * 0.46)
        R_inner  = int(size * 0.30)
        band     = R_outer - R_inner
        R_mid    = (R_outer + R_inner) // 2
        cap_r    = band // 2
        N        = 10
        SEG_STEP = 27.0
        SEG_ARC  = SEG_STEP * 0.88

        img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        draw.ellipse([cx-R_outer-8, cy-R_outer-8,
                      cx+R_outer+8, cy+R_outer+8],
                     fill=(200, 205, 215, 120))
        draw.ellipse([cx-R_outer-3, cy-R_outer-3,
                      cx+R_outer+3, cy+R_outer+3],
                     fill=(*rgb(d["gauge_bg"]), 255),
                     outline=(*rgb(BORDER), 150), width=1)

        for i in range(N):
            start_deg = 225.0 - i * SEG_STEP
            end_deg   = start_deg - SEG_ARC
            filled    = sev >= (i + 1)
            seg_col   = rgb(SEV_COLS[i]) if filled else rgb(BORDER)
            rgba      = (*seg_col, 255)
            draw.arc([cx-R_mid, cy-R_mid, cx+R_mid, cy+R_mid],
                     -start_deg, -end_deg, fill=rgba, width=band)
            for deg in [start_deg, end_deg]:
                rad = math.radians(deg)
                ex  = cx + R_mid * math.cos(rad)
                ey  = cy - R_mid * math.sin(rad)
                draw.ellipse([ex-cap_r, ey-cap_r,
                              ex+cap_r, ey+cap_r], fill=rgba)

        disc_r = R_inner - 2
        draw.ellipse([cx-disc_r-4, cy-disc_r-4,
                      cx+disc_r+4, cy+disc_r+4],
                     fill=(200, 208, 220, 160))
        draw.ellipse([cx-disc_r, cy-disc_r,
                      cx+disc_r, cy+disc_r],
                     fill=(255, 255, 255, 255))
        return img   # PIL Image — safe to build in any thread

    # ─────────────────────────────────────────────────────────────
    # GAUGE — thick rainbow segments matching the reference image
    # Wide band (R_outer-R_inner ~= 30% of size), fully rounded caps,
    # 270° sweep with clear white gaps between segments.
    # ─────────────────────────────────────────────────────────────
    def _gauge(self, cv, key, d, col, sev, size=262):
        """Draw gauge — uses pre-rendered PIL image if available, else builds it."""
        cx = cy  = size // 2
        R_inner  = int(size * 0.30)
        disc_r   = R_inner - 2

        # Use image pre-rendered in background thread (fastest path)
        pre = getattr(self.app, "_gauge_img", None)
        if pre is not None:
            self.app._gauge_img = None          # consume it
            cv.delete("all")
            self._refs["gauge"] = ImageTk.PhotoImage(pre)  # only PhotoImage on main thread
            cv.create_image(0, 0, anchor="nw", image=self._refs["gauge"])
            self._draw_gauge_text(cv, cx, cy, disc_r, d, col, sev)
            return

        # Fallback: build synchronously (only happens if thread didn't finish in time)
        img = self.build_gauge_image(key, sev, size)
        cv.delete("all")
        self._refs["gauge"] = ImageTk.PhotoImage(img)
        cv.create_image(0, 0, anchor="nw", image=self._refs["gauge"])
        self._draw_gauge_text(cv, cx, cy, disc_r, d, col, sev)

    def _draw_gauge_text(self, cv, cx, cy, disc_r, d, col, sev):
        """Draw text labels inside gauge disc — Tkinter only, very fast."""
        cv.create_text(cx, cy - int(disc_r*0.50), text=d["emoji"],
                       font=("Segoe UI Emoji", int(disc_r*0.30)), anchor="center")
        cv.create_text(cx, cy - int(disc_r*0.03), text=str(sev),
                       font=("Segoe UI", int(disc_r*0.44), "bold"),
                       fill=col, anchor="center")
        is_yo_g  = self.app.lang.get() == "Yolngu Matha"
        g_outcome = d.get("yo_outcome", d["outcome"]) if is_yo_g else d["outcome"]
        cv.create_text(cx, cy + int(disc_r*0.37), text=g_outcome,
                       font=("Segoe UI", int(disc_r*0.17), "bold"),
                       fill=col, anchor="center")
        g_tag = d.get("yo_tag", d["tag"]) if is_yo_g else d["tag"]
        cv.create_text(cx, cy + int(disc_r*0.58), text=f"[ {g_tag} ]",
                       font=("Segoe UI", int(disc_r*0.11), "bold"),
                       fill=col, anchor="center")

    # ─────────────────────────────────────────────────────────────
    # HELPERS
    # ─────────────────────────────────────────────────────────────
    def _facts(self, key):
        facts = []
        try:    ft = float(self.app.fever_temp_v.get() or 37.0)
        except: ft = 37.0
        tb, _ = temp_band(ft)
        if ft >= 37.5:
            facts.append(f"Temp {ft}°C  ({tb})")
        if self.app.chills_v.get():
            facts.append("Chills and shivering")
        if self.app.nausea_v.get():
            facts.append("Nausea / vomiting")
        if self.app.other_v.get():
            facts.append("Other body areas affected")
        return "   ·   ".join(facts)

    def _summary_rows(self):
        sym  = self.app.symptom or "—"
        days = getattr(self.app, "days_computed", 1)
        sev  = self.app.sev_v.get()
        try:    ft = float(self.app.fever_temp_v.get() or 37.0)
        except: ft = 37.0
        tb, _ = temp_band(ft)
        br     = self.app.breathe_v.get()
        chills = self.app.chills_v.get()
        nausea = getattr(self.app, "nausea_v", None)
        nausea = nausea.get() if nausea else False
        dur    = "Today" if days <= 1 else f"{days} days"
        filled = "●" * round(sev/2) + "○" * (5 - round(sev/2))
        rows   = [("Symptom", sym, False),
                  ("When", dur, False),
                  ("Severity", f"{sev}/10 {filled}", sev >= 7)]
        if ft >= 37.5:
            rows.append(("Temp", f"{ft}°C ({tb})", ft >= 38.5))
        if br >= 4:
            rows.append(("Breathing", f"{br}/10", br >= 7))
        if chills:
            rows.append(("Chills", "Yes ⚠", True))
        if nausea:
            rows.append(("Nausea", "Yes", False))
        act = getattr(self.app, "activity_v", None)
        sc  = act.get() if act else 3
        rows.append(("Daily life",
                      {4:"Fully normal",3:"Mostly OK",2:"Struggling",1:"Cannot"}.get(sc,"—"),
                      sc <= 2))
        return rows

    def _summary(self):
        return [f"{r[0]:<13}: {r[1]}" for r in self._summary_rows()]

    def _btn(self, parent, text, col, cmd, side):
        W, H = 220, 44
        cv = Canvas(parent, width=W, height=H, bg=BG,
                    highlightthickness=0, bd=0, cursor="hand2")
        cv.pack(side=side, padx=(0 if side == "left" else 6, 0))
        p = pill(W, H, col, H // 2)
        k = "b_" + text[:3]
        self._refs[k] = ImageTk.PhotoImage(p)
        cv.create_image(0, 0, anchor="nw", image=self._refs[k])
        cv.create_text(W//2, H//2, text=text,
                       font=("Segoe UI", 11, "bold"),
                       fill="#FFFFFF", anchor="center")
        cv.bind("<Button-1>", lambda e: cmd())