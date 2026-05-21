"""SACA — S4_Questions_Text: Scrollable all-questions-in-one-page flow
   (used by TYPE and SPEAK input methods).
"""
import tkinter as tk
from tkinter import Canvas, Frame, Label, Entry, StringVar, BooleanVar, IntVar
from PIL import Image, ImageDraw, ImageTk, ImageFilter
from constants import *
from helpers  import mkcard, pill, h2r, r2h, lerp
from widgets  import SF, NavBar, voice_bar, progress_timeline
from tts      import speak

class S4_Questions_Text(Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app = app
        self._built_lang = None

    def on_show(self):
        lang = self.app.lang.get()
        sym  = self.app.symptom
        key  = (lang, sym)
        if self._built_lang == key: return
        self._built_lang = key
        for w in self.winfo_children(): w.destroy()
        self._build()

    def _build(self):
        col  = self.app.sym_c or OCHRE
        sym  = self.app.symptom or "Symptom"
        lang = self.app.lang.get()
        yo   = lang == "Yolngu Matha"

        NavBar(self,
               f"Questions — {sym}" if not yo else f"Märr Dhäruk — {sym}",
               "Answer each question below  ·  Step 3 of 4",
               back=lambda: (self.app.go("S3_BodyPart") if self.app.input_method.get()=="photo" else self.app.go("nlp_speak") if self.app.input_method.get()=="speak" else self.app.go("nlp_type")), accent=col)

        progress_timeline(self, current_step=2, bg=BG_CARD)
        voice_bar(self,
                  f"You selected {sym}. Please answer the questions below to help us assess your condition.",
                  accent=col)

        # Symptom banner
        banner = Frame(self, bg=col, height=58)
        banner.pack(fill="x")
        banner.pack_propagate(False)
        Label(banner, text=sym.upper(),
              font=("Segoe UI", 20, "bold"),
              fg="#FFFFFF", bg=col).place(relx=0.5, rely=0.5, anchor="center")

        outer = Frame(self, bg=BG)
        outer.pack(fill="both", expand=1)
        sf = SF(outer)
        sf.pack(fill="both", expand=1)
        pad = Frame(sf.inner, bg=BG)
        pad.pack(fill="x", padx=60, pady=20)

        # Bilingual question text
        T = {
          "q1":    "When did the symptom start?" if not yo else "Nhaltjan warray ga djäma?",
          "q2":    "How severe does it feel?  (1=Low → 10=High)" if not yo else "Nhä märr djuy'yun?  (1=Mäkitj → 10=Djorra')",
          "q3":    "What is your body temperature?" if not yo else "Märr yukurra (°C)?",
          "q4":    "What type of pain or discomfort?" if not yo else "Nhä yolŋu märr?",
          "q5":    "Any difficulty breathing?" if not yo else "Ŋunha djuy'yun?",
          "q6":    "Have you taken any medication?" if not yo else "Manapan dhäruk?",
          "q7":    "Do you have chills or shivering?" if not yo else "Nhuma ga märr-djarrka?",
          "q8":    "Is any other body part affected?" if not yo else "Mala gäna bäy dhäwu?",
          "yes6":  "Yes — I have taken medication" if not yo else "Ŋa — manapan djäma",
          "no6":   "No — I have not taken medication" if not yo else "Gakal — manapan djäma",
          "yes7":  "Yes — I have chills or shivering" if not yo else "Ŋa — märr djarrka",
          "no7":   "No — no chills" if not yo else "Gakal — märr djarrka",
          "yes8":  "Yes — another body part is also affected" if not yo else "Ŋa — mala gäna bäy",
          "no8":   "No — only this symptom" if not yo else "Gakal — mala djäka",
        }

        # Q1: WHEN
        self._section(pad, "1", T["q1"], col)
        self._option_group(pad, [
            ("Today"       if not yo else "Warray",          lambda: setattr(self.app,'days_computed',0)),
            ("Yesterday"   if not yo else "Ŋunha warray",   lambda: setattr(self.app,'days_computed',1)),
            ("2–3 days"    if not yo else "2–3 dhärran",    lambda: setattr(self.app,'days_computed',2)),
            ("4–7 days"    if not yo else "4–7 dhärran",    lambda: setattr(self.app,'days_computed',5)),
            ("1–2 weeks"   if not yo else "1–2 Ŋarrak",     lambda: setattr(self.app,'days_computed',10)),
            ("Longer"      if not yo else "Dhuwanydja",     lambda: setattr(self.app,'days_computed',21)),
        ], col, default=0)
        self._div(pad)

        # Q2: SEVERITY
        self._section(pad, "2", T["q2"], col)
        self._option_group(pad, [
            ("1–2  Very mild"   if not yo else "1–2  Mäkitj",    lambda: self.app.sev_v.set(2)),
            ("3–4  Mild"        if not yo else "3–4  Djuy'yun",  lambda: self.app.sev_v.set(4)),
            ("5–6  Moderate"    if not yo else "5–6  Yukurra",   lambda: self.app.sev_v.set(6)),
            ("7–8  Severe"      if not yo else "7–8  Djorra'",   lambda: self.app.sev_v.set(8)),
            ("9–10 Very severe" if not yo else "9–10 Gakal",     lambda: self.app.sev_v.set(10)),
        ], col, default=2,
           sev_colors=["#4ADE80","#86EFAC","#FCD34D","#FB923C","#EF4444"])
        self._div(pad)

        # Q3: TEMPERATURE
        self._section(pad, "3", T["q3"], col)
        self._option_group(pad, [
            ("Below 36°C  — Low / hypothermia"    if not yo else "36°C bäl — Mäkitj",         lambda: self.app.fever_temp_v.set("35.5")),
            ("36–37.4°C   — Normal"               if not yo else "36–37.4°C — Gakal",          lambda: self.app.fever_temp_v.set("37.0")),
            ("37.5–38°C   — Low-grade fever"      if not yo else "37.5–38°C — Mäkitj märr",   lambda: self.app.fever_temp_v.set("37.7")),
            ("38–39°C     — Fever"                if not yo else "38–39°C — Märr",             lambda: self.app.fever_temp_v.set("38.5")),
            ("39–40°C     — High fever"           if not yo else "39–40°C — Märr djorra'",    lambda: self.app.fever_temp_v.set("39.5")),
            ("Above 40°C  — Very high / emergency" if not yo else "40°C yaka — Bäyŋu märr",   lambda: self.app.fever_temp_v.set("40.5")),
        ], col, default=1)
        self._div(pad)

        # Q4: PAIN TYPE
        self._section(pad, "4", T["q4"], col)
        self._option_group(pad, [
            ("Dull / Aching   — constant, heavy"  if not yo else "Dull   — galkun djuy'yun",   lambda: self.app.pain_type_v.set("Dull/Aching")),
            ("Sharp / Stabbing — sudden, knife"   if not yo else "Sharp  — djarra märr",        lambda: self.app.pain_type_v.set("Sharp/Stabbing")),
            ("Burning — hot or stinging"          if not yo else "Dhäkay — märr waŋa",          lambda: self.app.pain_type_v.set("Burning")),
            ("Throbbing — pulsing pain"           if not yo else "Throb  — märr buku-lili",     lambda: self.app.pain_type_v.set("Throbbing")),
            ("Pressure — squeezing or tight"      if not yo else "Yukurra — märr dhukarr",      lambda: self.app.pain_type_v.set("Pressure")),
            ("None — no pain"                     if not yo else "Gakal  — märr djäka",         lambda: self.app.pain_type_v.set("None")),
        ], col, default=5)
        self._div(pad)

        # Q5: BREATHING
        self._section(pad, "5", T["q5"], col)
        self._option_group(pad, [
            ("1–2  Fine — breathing normally"    if not yo else "1–2  Gakal ŋunha",         lambda: self.app.breathe_v.set(1)),
            ("3–4  Slight shortness of breath"   if not yo else "3–4  Mäkitj ŋunha",        lambda: self.app.breathe_v.set(3)),
            ("5–6  Moderate difficulty"          if not yo else "5–6  Yukurra ŋunha",        lambda: self.app.breathe_v.set(5)),
            ("7–8  Significant difficulty"       if not yo else "7–8  Djorra' ŋunha",        lambda: self.app.breathe_v.set(7)),
            ("9–10 Cannot breathe properly"      if not yo else "9–10 Gakal ŋunha",          lambda: self.app.breathe_v.set(9)),
        ], col, default=0,
           sev_colors=["#4ADE80","#86EFAC","#FCD34D","#FB923C","#EF4444"])
        self._div(pad)

        # Q6–Q8: YES/NO
        for qnum, title, var, yes_txt, no_txt in [
            ("6", T["q6"], self.app.med_v,    T["yes6"], T["no6"]),
            ("7", T["q7"], self.app.chills_v, T["yes7"], T["no7"]),
            ("8", T["q8"], self.app.other_v,  T["yes8"], T["no8"]),
        ]:
            self._section(pad, qnum, title, col)
            self._yn_toggle(pad, var, yes_txt, no_txt, col)
            self._div(pad)

        # ANALYSE button
        self._analyse_btn(pad, col, yo)

    # ── Helpers ──────────────────────────────────────────────────

    def _section(self, p, num, title, col):
        Label(p, bg=BG).pack(pady=5)
        f = Frame(p, bg=BG); f.pack(anchor="w", fill="x")
        # Number badge
        nc = Canvas(f, width=36, height=36, bg=BG,
                    highlightthickness=0, bd=0)
        nc.pack(side="left", padx=(0,12))
        nc.create_oval(2,2,34,34, fill=col, outline="")
        nc.create_text(18,18, text=num,
                       font=("Segoe UI",13,"bold"),
                       fill="#FFFFFF", anchor="center")
        Label(f, text=title, font=("Segoe UI",14,"bold"),
              fg=TXT1, bg=BG).pack(side="left")

    def _option_group(self, parent, options, col, default=0,
                      sev_colors=None):
        """Render a list of selectable option cards."""
        holder  = Frame(parent, bg=BG)
        holder.pack(anchor="w", fill="x", pady=(8,4))
        sel     = [default]
        frames  = {}

        def pick(idx, cmd):
            sel[0] = idx
            cmd()
            for i2, f2 in frames.items():
                self._style_option(f2, i2==idx, col,
                                   sev_colors[i2] if sev_colors else col)

        for i, (label, cmd) in enumerate(options):
            row = Frame(holder, bg=BG_ALT if i==default else BG_CARD,
                        highlightthickness=2,
                        highlightbackground=col if i==default else BORDER,
                        cursor="hand2")
            row.pack(fill="x", pady=4)
            frames[i] = row

            # Left accent dot
            accent_col = sev_colors[i] if sev_colors else col
            dot = Canvas(row, width=20, height=20,
                         bg=BG_ALT if i==default else BG_CARD,
                         highlightthickness=0, bd=0)
            dot.pack(side="left", padx=(16,10), pady=18)
            if i == default:
                dot.create_oval(2,2,18,18, fill=col, outline="")
                dot.create_text(10,10,text="✓",
                                font=("Segoe UI",9,"bold"),
                                fill="#FFFFFF")
            else:
                dot.create_oval(2,2,18,18, fill=BG_CARD,
                                outline=BORDER2, width=2)
            row._dot = dot

            Label(row, text=label, font=("Segoe UI",13),
                  fg=TXT1 if i==default else TXT2,
                  bg=BG_ALT if i==default else BG_CARD,
                  anchor="w").pack(side="left", padx=(0,12), pady=18)

            # Colour bar right edge
            if sev_colors:
                bar = Frame(row, width=6, bg=accent_col)
                bar.pack(side="right", fill="y")

            def on_click(e, i_=i, c_=cmd):
                pick(i_, c_)

            for widget in row.winfo_children():
                widget.bind("<Button-1>", on_click)
            row.bind("<Button-1>", on_click)

        # Run default action
        try:
            options[default][1]()
        except: pass

    def _style_option(self, frame, selected, col, acc_col):
        """Restyle an option card."""
        bg = BG_ALT if selected else BG_CARD
        bc = col  if selected else BORDER
        frame.configure(bg=bg, highlightbackground=bc)
        for child in frame.winfo_children():
            try:
                if isinstance(child, Canvas):
                    child.configure(bg=bg)
                    child.delete("all")
                    if selected:
                        child.create_oval(2,2,14,14,fill=col,outline="")
                        child.create_text(8,8,text="✓",
                                          font=("Segoe UI",8,"bold"),
                                          fill="#FFFFFF")
                    else:
                        child.create_oval(2,2,14,14,fill=BG_CARD,
                                          outline=BORDER2,width=2)
                elif isinstance(child, Label):
                    child.configure(bg=bg,
                                    fg=TXT1 if selected else TXT2,
                                    font=("Segoe UI",12,"bold" if selected else "normal"))
                elif isinstance(child, Frame):
                    pass  # colour bar
            except: pass

    def _yn_toggle(self, parent, var, yes_txt, no_txt, col):
        """Large YES/NO toggle cards."""
        holder = Frame(parent, bg=BG); holder.pack(fill="x", pady=(8,4))
        var.set(False)
        cards  = {}

        def pick(val):
            var.set(val)
            for is_yes_, card_ in cards.items():
                sel_ = (is_yes_ == val)
                bc_  = GREEN if is_yes_ else TERRA
                card_.configure(
                    bg=r2h(*lerp(BG_CARD, bc_, 0.10)) if sel_ else BG_CARD,
                    highlightbackground=bc_ if sel_ else BORDER)
                for child in card_.winfo_children():
                    try:
                        card_bg = r2h(*lerp(BG_CARD, bc_, 0.10)) if sel_ else BG_CARD
                        child.configure(bg=card_bg,
                            fg="#FFFFFF" if sel_ else TXT2,
                            font=("Segoe UI",12,"bold" if sel_ else "normal"))
                    except: pass

        for is_yes, txt, bc in [(True, yes_txt, GREEN), (False, no_txt, TERRA)]:
            card = Frame(holder, bg=BG_CARD,
                         highlightthickness=2,
                         highlightbackground=BORDER,
                         cursor="hand2")
            card.pack(fill="x", pady=3)
            cards[is_yes] = card

            icon_c = Canvas(card, width=28, height=28, bg=BG_CARD,
                            highlightthickness=0, bd=0)
            icon_c.pack(side="left", padx=(12,10), pady=14)
            icon_c.create_oval(2,2,26,26, fill=bc, outline="")
            icon_c.create_text(14,14,
                               text="✓" if is_yes else "✗",
                               font=("Segoe UI",13,"bold"),
                               fill="#FFFFFF")

            Label(card, text=txt, font=("Segoe UI",12),
                  fg=TXT2, bg=BG_CARD, anchor="w").pack(
                  side="left", padx=(0,16), pady=14)

            def on_click(e, v=is_yes): pick(v)
            for w_ in card.winfo_children():
                w_.bind("<Button-1>", on_click)
            card.bind("<Button-1>", on_click)

    def _div(self, p):
        Frame(p, height=1, bg=BORDER).pack(fill="x", pady=8)

    def _analyse_btn(self, parent, col, yo):
        BW, BH = 640, 70
        cv = Canvas(parent, width=BW, height=BH, bg=BG,
                    highlightthickness=0, bd=0, cursor="hand2")
        cv.pack(pady=(12,24))
        pn = pill(BW, BH, col, BH//2)
        ph = pill(BW, BH, r2h(*lerp(col,"#000000",0.2)), BH//2)
        self._an = ImageTk.PhotoImage(pn)
        self._ah = ImageTk.PhotoImage(ph)
        bid = cv.create_image(0,0,anchor="nw",image=self._an)
        cv.create_text(BW//2, BH//2-9,
                       text="ANALYSE" if not yo else "YUKURRA",
                       font=("Segoe UI",17,"bold"),
                       fill="#FFFFFF", anchor="center")
        cv.create_text(BW//2, BH//2+12,
                       text="Tap to get your triage result",
                       font=("Segoe UI",10),
                       fill="#FFFFFF", anchor="center")

        def _confirm():
            if tk.messagebox.askyesno("Confirm",
                f"Ready to analyse your {self.app.symptom or 'symptom'}?",
                icon="question"):
                self.app.analyse()
        cv.bind("<Button-1>", lambda e: _confirm())
        cv.bind("<Enter>", lambda e: cv.itemconfig(bid, image=self._ah))
        cv.bind("<Leave>", lambda e: cv.itemconfig(bid, image=self._an))


# ══════════════════════════════════════════════════════════════════
# S4_Questions_Voice — Fully voice-driven Q&A
