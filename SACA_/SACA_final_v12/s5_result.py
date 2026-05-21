"""SACA — S5_Result: Single-screen triage result. Minimal text, maximum visuals."""
import os
import tkinter as tk
from tkinter import Canvas, Frame, Label
from PIL import Image, ImageDraw, ImageTk
from constants import *
from helpers  import mkcard, pill, h2r, r2h, lerp, _dir
from widgets  import NavBar, voice_bar, progress_timeline
from tts      import speak
from triage   import triage, temp_band

class S5_Result(Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app   = app
        self._body = None

    CFG = {
        "mild": {
            "label": "MILD",         "yo": "Märr Mäkitj",
            "tag":   "LOW RISK",     "color": GREEN,
            "bg":    GRN_BG,         "icon": "✓",
            "emoji": "😊",
            "msg":   "Rest at home. Monitor your symptoms.",
        },
        "moderate": {
            "label": "MODERATE",     "yo": "Märr Djuy'yun",
            "tag":   "SEE A DOCTOR", "color": OCHRE,
            "bg":    YEL_BG,         "icon": "⚠",
            "emoji": "😟",
            "msg":   "Visit the Yirrkala clinic within 24 hours.",
        },
        "severe": {
            "label": "EMERGENCY",    "yo": "Märr Djorra'",
            "tag":   "CALL 000 NOW", "color": RED_EM,
            "bg":    RED_BG,         "icon": "🚨",
            "emoji": "😱",
            "msg":   "Call 000 immediately. Do not wait.",
        },
    }

    # ── Steps per outcome ──────────────────────────────────────────
    STEPS = {
        "mild": [
            ("🛏", "Rest",       "Sleep and avoid heavy activity"),
            ("💧", "Drink water","Stay hydrated all day"),
            ("💊", "Panadol",    "Take if needed for pain/fever"),
            ("👁", "Watch",      "Return if it gets worse"),
        ],
        "moderate": [
            ("🏥", "Go to clinic","Yirrkala clinic within 24 hrs"),
            ("👫", "Bring help",  "Take a family member with you"),
            ("📋", "Tell all",    "Share how long and how bad"),
            ("💊", "Follow advice","Take all medicine as told"),
        ],
        "severe": [
            ("📞", "Call 000",   "Free · Tell them where you are"),
            ("🏥", "Go NOW",     "Hospital immediately · Don't wait"),
            ("🧍", "Stay still", "Sit or lie down · Breathe slowly"),
            ("👫", "Get help",   "Have someone stay with you"),
        ],
    }

    def set_result(self, key):
        if self._body:
            self._body.destroy()
        d   = self.CFG[key]
        col = d["color"]
        sym = self.app.symptom or "Symptom"
        ts  = getattr(self.app, "triage_ts", "") or ""
        sev = self.app.sev_v.get()

        self._body = Frame(self, bg=BG)
        self._body.place(relx=0, rely=0, relwidth=1, relheight=1)

        # ── Header bar ────────────────────────────────────────────
        NavBar(self._body,
               "Your Result" if key != "severe" else "🚨  URGENT — Act Now",
               f"{sym}  ·  {ts}",
               back=lambda: self.app._sc["S4_Questions"].on_show(from_results=True) or self.app._sc["S4_Questions"].lift(), accent=col)

        progress_timeline(self._body, current_step=3, bg=BG_CARD)
        voice_bar(self._body, {
            "mild":     "Your result is mild. Rest at home.",
            "moderate": "Your result is moderate. Visit the clinic today.",
            "severe":   "EMERGENCY. Call 000 right now.",
        }.get(key, ""), accent=col)

        # ── TOP BANNER — big colour strip ─────────────────────────
        # Pack bottom buttons FIRST so they aren't pushed off screen
        bot = Frame(self._body, bg=BG)
        bot.pack(side="bottom", fill="x", padx=16, pady=(4, 8))
        self._rbtn(bot, "💾  Save Report", col,   self.app.save_report, "left")
        self._rbtn(bot, "↩  Start Over",   BORDER2, self.app.reset,     "right")

        # ── MAIN single-screen body ───────────────────────────────
        main = Frame(self._body, bg=BG)
        main.pack(fill="both", expand=1, padx=14, pady=(6, 4))

        # ── LEFT COLUMN — gauge + answers ────────────────────────
        left = Frame(main, bg=BG, width=268)
        left.pack(side="left", fill="y", padx=(0, 12))
        left.pack_propagate(False)

        # Compact gauge
        gauge_cv = Canvas(left, width=240, height=240,
                          bg=BG, highlightthickness=0, bd=0)
        gauge_cv.pack(pady=(2, 0), anchor="center")
        self._draw_gauge(gauge_cv, key, d, col, size=240)

        # Severity label
        Label(left, text=f"Severity  {sev}/10",
              font=("Segoe UI", 13, "bold"), fg=col, bg=BG).pack()

        # Your Answers — compact
        sm = Frame(left, bg=BG_CARD,
                   highlightthickness=1, highlightbackground=BORDER)
        sm.pack(fill="x", padx=4, pady=(6, 0))
        Label(sm, text="Your Answers",
              font=("Segoe UI", 11, "bold"), fg=col, bg=BG_CARD,
              pady=5, padx=12).pack(anchor="w")
        Frame(sm, height=1, bg=BORDER).pack(fill="x")
        for lbl, val, hi in self._summary_rows():
            r = Frame(sm, bg=BG_CARD)
            r.pack(fill="x", padx=12, pady=2)
            Label(r, text=lbl, font=("Segoe UI", 9), fg=TXT3,
                  bg=BG_CARD, width=11, anchor="w").pack(side="left")
            Label(r, text=val,
                  font=("Segoe UI", 10, "bold" if hi else "normal"),
                  fg=col if hi else TXT1, bg=BG_CARD,
                  anchor="w").pack(side="left")

        # ── RIGHT COLUMN ──────────────────────────────────────────
        right = Frame(main, bg=BG)
        right.pack(side="left", fill="both", expand=1)

        # Status badge
        badge = Frame(right, bg=col)
        badge.pack(fill="x", pady=(0, 8))
        Label(badge,
              text=f"  {d['emoji']}   {d['label']}  —  {d['tag']}  ",
              font=("Segoe UI", 20, "bold"), fg="#FFFFFF", bg=col,
              pady=10).pack(side="left")

        # ── Key message — ONE sentence, large, clear ──────────────
        msg_f = Frame(right, bg=d["bg"],
                      highlightthickness=2, highlightbackground=col)
        msg_f.pack(fill="x", pady=(0, 8))
        Label(msg_f, text=d["msg"],
              font=("Segoe UI", 15, "bold"),
              fg=col if key != "severe" else "#C0392B",
              bg=d["bg"], padx=16, pady=10,
              justify="left", wraplength=680,
              anchor="w").pack(anchor="w")

        # Extra info only if actually relevant
        extra = self._key_facts(key)
        if extra:
            Label(msg_f, text=extra,
                  font=("Segoe UI", 12),
                  fg=TXT2, bg=d["bg"],
                  padx=16, pady=4,
                  justify="left", wraplength=680,
                  anchor="w").pack(anchor="w", pady=(0, 8))

        # ── 4 action cards in a row ───────────────────────────────
        Label(right, text="What To Do Now",
              font=("Segoe UI", 13, "bold"), fg=TXT1, bg=BG).pack(anchor="w", pady=(2, 4))

        cards_row = Frame(right, bg=BG)
        cards_row.pack(fill="x")

        for emoji, title, desc in self.STEPS[key]:
            self._action_card(cards_row, emoji, title, desc, col)

        # ── Contact strip ─────────────────────────────────────────
        contact_text = {
            "mild":     "📞  Yirrkala Clinic: (08) 8987 1000  ·  Mon–Fri 8am–5pm",
            "moderate": "📞  Yirrkala Clinic: (08) 8987 1000  ·  After hours: Gove Hospital (08) 8987 0211",
            "severe":   "📞  000  (Emergency)   ·   Flying Doctor: 1800 625 800  (Free · 24 hrs)",
        }[key]

        ct = Frame(right, bg=col)
        ct.pack(fill="x", pady=(8, 0))
        Label(ct, text=contact_text,
              font=("Segoe UI", 12, "bold"), fg="#FFFFFF", bg=col,
              padx=14, pady=8).pack(anchor="w")

    # ── Action card — visual square with big emoji ─────────────────
    def _action_card(self, parent, emoji, title, desc, col):
        W, H = 175, 130
        f = Frame(parent, bg=BG_CARD,
                  highlightthickness=2, highlightbackground=col)
        f.pack(side="left", fill="x", expand=1, padx=3)
        # Emoji large
        Label(f, text=emoji,
              font=("Segoe UI Emoji", 28), bg=BG_CARD).pack(pady=(8, 0))
        # Title bold
        Label(f, text=title,
              font=("Segoe UI", 11, "bold"), fg=col, bg=BG_CARD).pack()
        # Description small
        Label(f, text=desc,
              font=("Segoe UI", 9), fg=TXT3, bg=BG_CARD,
              wraplength=155, justify="center").pack(pady=(0, 8))

    # ── Key facts — only non-obvious info ─────────────────────────
    def _key_facts(self, key):
        facts = []
        try:   ft = float(self.app.fever_temp_v.get() or 37.0)
        except: ft = 37.0
        tb_label, _ = temp_band(ft)
        if ft >= 37.5:
            facts.append(f"Temperature {ft}°C  ({tb_label})")
        if self.app.chills_v.get():
            facts.append("Chills and shivering reported")
        if self.app.nausea_v.get():
            facts.append("Nausea / vomiting reported")
        if self.app.other_v.get():
            facts.append("Other body areas also affected")
        return "  ·  ".join(facts) if facts else ""

    # ── Summary rows — only relevant info ─────────────────────────
    def _summary_rows(self):
        sym  = self.app.symptom or "—"
        days = getattr(self.app, "days_computed", 1)
        sev  = self.app.sev_v.get()
        try:   ft = float(self.app.fever_temp_v.get() or 37.0)
        except: ft = 37.0
        tb_label, _ = temp_band(ft)
        br     = self.app.breathe_v.get()
        chills = self.app.chills_v.get()
        med    = self.app.med_v.get()
        other  = self.app.other_v.get()
        nausea = getattr(self.app, "nausea_v", None)
        nausea = nausea.get() if nausea else False

        dur = "Today" if days <= 1 else (f"{days} days ago" if days <= 7 else f"{days} days")
        filled  = round(sev / 2)
        sev_bar = "●" * filled + "○" * (5 - filled)

        rows = [
            ("Symptom", sym,                     False),
            ("When",    dur,                      False),
            ("Severity", f"{sev}/10  {sev_bar}", sev >= 7),
        ]
        if ft >= 37.5:
            rows.append(("Temp", f"{ft}°C  ({tb_label})", ft >= 38.5))
        if br >= 4:
            rows.append(("Breathing", f"{br}/10", br >= 7))
        if chills:
            rows.append(("Chills", "Yes ⚠", True))
        if nausea:
            rows.append(("Nausea", "Yes", False))
        activity = getattr(self.app, "activity_v", None)
        act_score = activity.get() if activity else 3
        act_labels = {4: "Fully normal", 3: "Mostly OK", 2: "Struggling", 1: "Cannot function"}
        act_label  = act_labels.get(act_score, "—")
        rows.append(("Daily life", act_label, act_score <= 2))
        if other:
            rows.append(("Other areas", "Yes ⚠", True))
        return rows

    def _summary(self):
        """Legacy for save_report."""
        return [f"{r[0]:<13}: {r[1]}" for r in self._summary_rows()]

    # ── Compact gauge (size param) ─────────────────────────────────
    def _draw_gauge(self, cv, key, d, col, size=240):
        cx = cy = size // 2
        R  = int(size * 0.47)
        cv.delete("all")
        cv.create_oval(cx-R, cy-R, cx+R, cy+R,
                       fill=d["bg"], outline=BORDER, width=2)
        sev = self.app.sev_v.get()
        for i in range(10):
            start_ang = 225 - i * 27
            c_ = SEV_COLS[i]
            filled = sev >= (i + 1)
            ring_col = c_ if filled else BORDER
            thick = max(14, int(size * 0.056))
            for t in range(thick):
                r2 = R - t
                cv.create_arc(cx-r2, cy-r2, cx+r2, cy+r2,
                              start=start_ang-26, extent=25,
                              fill="", outline=ring_col, width=1)
        inner = int(R * 0.72)
        cv.create_oval(cx-inner, cy-inner, cx+inner, cy+inner,
                       fill=BG_CARD, outline=d["bg"], width=3)
        icon_size = max(24, int(size * 0.13))
        cv.create_text(cx, cy - int(size * 0.10),
                       text=d["emoji"],
                       font=("Segoe UI Emoji", icon_size), anchor="center")
        cv.create_text(cx, cy + int(size * 0.08),
                       text=d["label"],
                       font=("Segoe UI", int(size * 0.085), "bold"),
                       fill=col, anchor="center")
        cv.create_text(cx, cy + int(size * 0.22),
                       text=f"[ {d['tag']} ]",
                       font=("Segoe UI", int(size * 0.048), "bold"),
                       fill=col, anchor="center")

    # ── Button ─────────────────────────────────────────────────────
    def _rbtn(self, parent, text, col, cmd, side):
        W_, H_ = 220, 46
        cv = Canvas(parent, width=W_, height=H_, bg=BG,
                    highlightthickness=0, bd=0, cursor="hand2")
        cv.pack(side=side, padx=(0 if side == "left" else 8, 0))
        pil = pill(W_, H_, col, H_ // 2)
        k = "btn_" + text[:4]
        setattr(self, k, ImageTk.PhotoImage(pil))
        cv.create_image(0, 0, anchor="nw", image=getattr(self, k))
        cv.create_text(W_//2, H_//2, text=text,
                       font=("Segoe UI", 11, "bold"),
                       fill="#FFFFFF", anchor="center")
        cv.bind("<Button-1>", lambda e: cmd())
