"""
SACA — S4_Questions_Voice: Voice-driven question flow.
Same 6 questions as s4_questions.py, same light UI style.
"""
import os
import threading
import tkinter as tk
from tkinter import Canvas, Frame, Label
from PIL import Image, ImageDraw, ImageTk, ImageFilter
from constants import *
from helpers  import mkcard, pill, h2r, r2h, lerp, _dir
from widgets  import SF, NavBar, voice_bar, progress_timeline
from tts      import speak

class S4_Questions_Voice(Frame):

    # ── Exactly 6 questions — same as s4_questions.py ─────────────
    QUESTIONS = [
        {
            "key":      "when",
            "label":    "When did it start?",
            "prompt":   "When did your symptom start?  Say:  today,  yesterday,  a few days,  or  over a week.",
            "example":  "e.g.  today  /  yesterday  /  two days  /  one week",
        },
        {
            "key":      "severity",
            "label":    "How bad is the pain?",
            "prompt":   "How bad is the pain or discomfort?  Say a number from one to ten.  One is very mild.  Ten is the worst.",
            "example":  "e.g.  three  /  five  /  eight  /  ten",
        },
        {
            "key":      "fever_yn",
            "label":    "Do you have a fever?",
            "prompt":   "Do you have a fever?  Is your body hot or warm?  Say:  no fever,  warm,  fever,  or  high fever.",
            "example":  "e.g.  no fever  /  a bit warm  /  fever  /  very hot",
        },
        {
            "key":      "breathing",
            "label":    "Can you breathe normally?",
            "prompt":   "Can you breathe normally?  Say a number from one to ten.  One means breathing fine.  Ten means you cannot breathe.",
            "example":  "e.g.  one  /  fine  /  five  /  very hard",
        },
        {
            "key":      "sick_dizzy",
            "label":    "Feeling sick or dizzy?",
            "prompt":   "Are you feeling sick in the stomach or dizzy?  Say:  no,  sick stomach,  dizzy,  or  both.",
            "example":  "e.g.  no  /  nausea  /  dizzy  /  both",
        },
        {
            "key":      "daily_activity",
            "label":    "Can you do daily activities?",
            "prompt":   "Can you do your normal daily activities?  Say:  yes fully,  mostly,  struggling,  or  cannot.",
            "example":  "e.g.  yes  /  mostly  /  struggling  /  cannot move",
        },
    ]

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app   = app
        self._step = 0
        self._last = None
        self._job  = None
        self._refs = {}

    def on_show(self):
        # Always rebuild fresh
        self._last = (self.app.lang.get(), self.app.symptom)
        self._step = 0
        self._job  = None
        # Reset state
        self.app.days_computed = 1
        self.app.sev_v.set(5)
        self.app.fever_temp_v.set("37.0")
        self.app.breathe_v.set(False)
        self.app.breathe_v.set(1)
        self.app.chills_v.set(False)
        self.app.nausea_v.set(False)
        self.app.other_v.set(False)
        self.app.med_v.set(False)
        self.app.pain_type_v.set("None")
        if hasattr(self.app, "activity_v"):
            self.app.activity_v.set(3)
        for w in self.winfo_children():
            w.destroy()
        self._refs = {}
        self._show_question()

    # ── Show one question ─────────────────────────────────────────
    def _show_question(self):
        if self._job:
            try: self.after_cancel(self._job)
            except: pass
            self._job = None

        for w in self.winfo_children():
            w.destroy()
        self._refs = {}

        q   = self.QUESTIONS[self._step]
        col = self.app.sym_c or OCHRE
        sym = self.app.symptom or "Symptom"
        W   = self.winfo_width() or 980

        # ── NavBar — same as s4_questions ─────────────────────────
        progress_timeline(self, current_step=2, bg=BG_CARD)

        acc = Frame(self, height=4, bg=col)
        acc.pack(fill="x")

        # Voice bar
        vb = Frame(self, bg=BG_ALT, cursor="hand2")
        vb.pack(fill="x")
        vb_lbl = Label(vb, text="🔊  Tap to Hear  /  Dhukarr ga wäŋa",
                       font=("Segoe UI", 11, "bold"), fg=SKY, bg=BG_ALT,
                       pady=4, padx=18, cursor="hand2")
        vb_lbl.pack(side="left")
        vb.bind("<Button-1>",     lambda e: speak(q["prompt"]))
        vb_lbl.bind("<Button-1>", lambda e: speak(q["prompt"]))

        # Back + step counter bar
        top = Frame(self, bg=BG)
        top.pack(fill="x", padx=16, pady=6)
        back_lbl = Label(top, text="← Back",
                         font=("Segoe UI", 11, "bold"),
                         fg=SKY, bg=BG, cursor="hand2", padx=4)
        back_lbl.pack(side="left")
        back_lbl.bind("<Button-1>", lambda e: self._go_back())
        Label(top,
              text=f"Question  {self._step+1}  of  {len(self.QUESTIONS)}",
              font=("Segoe UI", 10, "bold"),
              fg=TXT3, bg=BG).pack(side="left", padx=16)
        Label(top,
              text=(sym or "").upper(),
              font=("Segoe UI", 11, "bold"),
              fg=col, bg=BG).pack(side="right")

        # ── Main card — white, same style as body map ─────────────
        card_w = min(820, W - 40)
        card = Frame(self, bg=BG_CARD,
                     highlightthickness=1, highlightbackground=BORDER)
        card.place(relx=0.5, y=150, anchor="n", width=card_w)

        # Question label
        Label(card, text=q["label"].upper(),
              font=("Segoe UI", 12, "bold"),
              fg=col, bg=BG_CARD).pack(pady=(20, 4))

        Frame(card, height=1, bg=BORDER).pack(fill="x", padx=24)

        # Question text
        Label(card, text=q["prompt"],
              font=("Segoe UI", 15, "bold"),
              fg=TXT1, bg=BG_CARD,
              wraplength=card_w - 80,
              justify="center").pack(pady=(16, 4), padx=40)

        Label(card, text=q["example"],
              font=("Segoe UI", 11, "italic"),
              fg=TXT3, bg=BG_CARD).pack(pady=(0, 12))

        Frame(card, height=1, bg=BORDER).pack(fill="x", padx=24)

        # ── Mic visualiser ─────────────────────────────────────────
        mic_frame = Frame(card, bg=BG_CARD)
        mic_frame.pack(pady=16)

        self._mic_cv = Canvas(mic_frame, width=160, height=160,
                              bg=BG_CARD, highlightthickness=0, bd=0,
                              cursor="hand2")
        self._mic_cv.pack()
        self._draw_mic("idle", col)
        self._mic_cv.bind("<Button-1>", lambda e: self._on_mic_click(q))

        # Status
        self._status_lbl = Label(card, text="Tap the microphone to speak",
                                 font=("Segoe UI", 12), fg=TXT3, bg=BG_CARD)
        self._status_lbl.pack(pady=(4, 8))

        # Heard / answer labels
        self._heard_lbl = Label(card, text="",
                                font=("Segoe UI", 11, "italic"),
                                fg=TXT3, bg=BG_CARD)
        self._heard_lbl.pack()

        self._answer_lbl = Label(card, text="",
                                 font=("Segoe UI", 14, "bold"),
                                 fg=GREEN, bg=BG_CARD)
        self._answer_lbl.pack(pady=(2, 8))

        Frame(card, height=1, bg=BORDER).pack(fill="x", padx=24)

        # ── Bottom row: Skip + Next buttons ───────────────────────
        btn_row = Frame(card, bg=BG_CARD)
        btn_row.pack(pady=14)

        # Skip button
        skip_cv = Canvas(btn_row, width=130, height=46,
                         bg=BG_CARD, highlightthickness=0, bd=0, cursor="hand2")
        skip_cv.pack(side="left", padx=8)
        pn_skip = pill(130, 46, BORDER2, 23)
        self._refs["skip"] = ImageTk.PhotoImage(pn_skip)
        skip_cv.create_image(0, 0, anchor="nw", image=self._refs["skip"])
        skip_cv.create_text(65, 23, text="Skip  →",
                            font=("Segoe UI", 12), fill=TXT1, anchor="center")
        skip_cv.bind("<Button-1>", lambda e: self._next_question())

        # Next/Analyse button
        is_last = (self._step == len(self.QUESTIONS) - 1)
        btn_txt = "ANALYSE  →" if is_last else "NEXT  →"
        btn_col = OCHRE if is_last else SKY
        next_cv = Canvas(btn_row, width=180, height=46,
                         bg=BG_CARD, highlightthickness=0, bd=0, cursor="hand2")
        next_cv.pack(side="left", padx=8)
        pn_next = pill(180, 46, btn_col, 23)
        self._refs["next"] = ImageTk.PhotoImage(pn_next)
        next_cv.create_image(0, 0, anchor="nw", image=self._refs["next"])
        next_cv.create_text(90, 23, text=btn_txt,
                            font=("Segoe UI", 13, "bold"),
                            fill="#000000" if btn_col == OCHRE else "#FFFFFF",
                            anchor="center")
        next_cv.bind("<Button-1>", lambda e: self._next_question())

        # Auto-speak the question after 0.8s (allows TTS engine to be ready)
        self.after(800, lambda: speak(q["prompt"]))

    # ── Mic drawing ───────────────────────────────────────────────
    def _draw_mic(self, state, col=None):
        col = col or SKY
        cv  = self._mic_cv
        cv.delete("all")
        cx, cy = 80, 80

        state_cfg = {
            "idle":       (BG_CARD, col,    col),
            "listening":  (TERRA,  "#FF6B6B", TERRA),
            "processing": (OCHRE,  "#FFD700", OCHRE),
            "done":       (GREEN,  GREEN,   GREEN),
        }
        bg_c, ring_c, icon_c = state_cfg.get(state, state_cfg["idle"])

        # Outer rings (pulse effect)
        for r, alpha in [(72, 30), (60, 60), (50, 120)]:
            rr, gg, bb = h2r(ring_c)
            cv.create_oval(cx-r, cy-r, cx+r, cy+r,
                           fill="", outline=ring_c, width=2)

        # Main circle
        r_main = 44
        cv.create_oval(cx-r_main, cy-r_main, cx+r_main, cy+r_main,
                       fill=ring_c, outline="")

        # Mic icon
        icon = "🎙" if state in ("idle", "listening") else ("⏳" if state == "processing" else "✓")
        cv.create_text(cx, cy, text=icon,
                       font=("Segoe UI Emoji", 26), fill="#FFFFFF", anchor="center")

    # ── Mic click ─────────────────────────────────────────────────
    def _on_mic_click(self, q):
        self._draw_mic("listening", self.app.sym_c or OCHRE)
        self._set_status("🔴  Listening — speak now", TERRA)
        self._heard_lbl.configure(text="")
        self._answer_lbl.configure(text="")
        threading.Thread(target=self._listen, args=(q,), daemon=True).start()

    def _set_status(self, text, color=TXT3):
        self.after(0, lambda: self._status_lbl.configure(text=text, fg=color))

    # ── Voice capture ─────────────────────────────────────────────
    def _listen(self, q):
        try:
            import speech_recognition as sr
        except ImportError:
            import subprocess, sys
            subprocess.run([sys.executable,"-m","pip","install","SpeechRecognition","-q"])
            import speech_recognition as sr
        try:
            rec = sr.Recognizer()
            rec.dynamic_energy_threshold = False
            rec.energy_threshold         = 50
            rec.pause_threshold          = 1.0
            rec.phrase_threshold         = 0.1
            rec.non_speaking_duration    = 0.5

            try:
                mic = sr.Microphone()
            except Exception:
                self.after(0, lambda: self._set_status("No mic found — check connection", TERRA))
                self.after(0, lambda: self._draw_mic("idle", self.app.sym_c or OCHRE))
                return

            with mic as source:
                self.after(0, lambda: self._set_status("🔴  Speak now!", TERRA))
                try:
                    audio = rec.listen(source, timeout=8, phrase_time_limit=6)
                except sr.WaitTimeoutError:
                    self.after(0, lambda: self._set_status("No speech heard — try again", TERRA))
                    self.after(0, lambda: self._draw_mic("idle", self.app.sym_c or OCHRE))
                    return

            self.after(0, lambda: self._draw_mic("processing", self.app.sym_c or OCHRE))
            self.after(0, lambda: self._set_status("Processing...", TXT3))

            text = None
            for lang in ("en-AU", "en-US"):
                try:
                    text = rec.recognize_google(audio, language=lang)
                    if text: break
                except sr.UnknownValueError: pass
                except sr.RequestError: break
            if not text:
                try: text = rec.recognize_sphinx(audio)
                except Exception: pass
            if not text:
                self.after(0, lambda: self._set_status(
                    "Could not understand — speak clearly", TERRA))
                self.after(0, lambda: self._draw_mic("idle", self.app.sym_c or OCHRE))
                return
            self.after(0, lambda t=text: self._process_answer(t, q))
        except Exception as e:
            col = self.app.sym_c or OCHRE
            self.after(0, lambda: self._draw_mic("idle", col))
            self.after(0, lambda m=str(e)[:80]: self._set_status(m, TERRA))

    # ── Answer interpretation ─────────────────────────────────────
    def _process_answer(self, spoken, q):
        col = self.app.sym_c or OCHRE
        self._draw_mic("done", col)
        self._heard_lbl.configure(text=f'You said:  "{spoken}"')

        key    = q["key"]
        result = self._interpret(spoken, key)

        if result is None:
            self._set_status("Could not understand — tap mic to try again", TERRA)
            self._draw_mic("idle", col)
            return

        self._apply(key, result)
        display = self._friendly(key, result)
        self._answer_lbl.configure(text=f"✓  {display}", fg=GREEN)
        self._set_status("Got it!", GREEN)
        self._job = self.after(1600, self._next_question)

    def _interpret(self, spoken, key):
        import re
        t = spoken.lower().strip()

        if key == "when":
            if any(w in t for w in ["today","just","now","this morning","tonight"]):
                return 0
            if any(w in t for w in ["yesterday","one day","1 day"]):
                return 1
            if any(w in t for w in ["two","2 day","three","3 day","couple","few"]):
                return 3
            if any(w in t for w in ["week","seven","8","9","10","eight","nine","ten"]):
                return 7
            if any(w in t for w in ["longer","month","more than","weeks"]):
                return 14
            return None

        elif key == "severity":
            nums = re.findall(r"\d+", t)
            words = {"one":1,"two":2,"three":3,"four":4,"five":5,
                     "six":6,"seven":7,"eight":8,"nine":9,"ten":10}
            if nums: return min(10, max(1, int(nums[0])))
            for w, n in words.items():
                if w in t: return n
            if any(w in t for w in ["mild","light","little","low"]): return 2
            if any(w in t for w in ["moderate","medium","okay","ok"]): return 5
            if any(w in t for w in ["severe","bad","very bad","high"]): return 8
            if any(w in t for w in ["extreme","worst","terrible"]): return 10
            return None

        elif key == "fever_yn":
            if any(w in t for w in ["very hot","very high","high fever","burning up","40","41"]): return "high"
            if any(w in t for w in ["fever","feverish","hot","38","39"]):                         return "fever"
            if any(w in t for w in ["warm","little warm","bit warm","bit hot","37.5","37.6"]):    return "warm"
            if any(w in t for w in ["no fever","no","normal","fine","not hot","ok"]):             return "none"
            return None

        elif key == "breathing":
            nums = re.findall(r"\d+", t)
            words = {"one":1,"two":2,"three":3,"four":4,"five":5,
                     "six":6,"seven":7,"eight":8,"nine":9,"ten":10}
            if nums: return min(10, max(1, int(nums[0])))
            for w, n in words.items():
                if w in t: return n
            if any(w in t for w in ["fine","normal","okay","no problem","breathing well"]): return 1
            if any(w in t for w in ["little","slight","mild"]): return 3
            if any(w in t for w in ["moderate","some","bit hard","difficult"]): return 5
            if any(w in t for w in ["very hard","really hard","struggling"]): return 7
            if any(w in t for w in ["cannot","can't","no breath","extreme","worst"]): return 10
            return None

        elif key == "sick_dizzy":
            if any(w in t for w in ["both","sick and dizzy","nausea and dizzy","vomit and dizzy"]):
                return "both"
            if any(w in t for w in ["dizzy","dizziness","spinning","light head","faint","vertigo"]):
                return "dizzy"
            if any(w in t for w in ["sick","nausea","nauseous","vomit","throw up","queasy"]):
                return "nausea"
            if any(w in t for w in ["no","not","fine","neither","okay","nothing"]):
                return "none"
            return None

        elif key == "daily_activity":
            if any(w in t for w in ["cannot","can't","no","not able","bed","lying down","help"]):
                return 1
            if any(w in t for w in ["struggling","hard","difficult","not easy","barely"]):
                return 2
            if any(w in t for w in ["mostly","kind of","sort of","some","little bit","ok"]):
                return 3
            if any(w in t for w in ["yes","fully","normal","fine","everything","all"]):
                return 4
            return None

        return None

    def _apply(self, key, value):
        if key == "when":
            self.app.days_computed = max(1, value)
        elif key == "severity":
            self.app.sev_v.set(value)
        elif key == "fever_yn":
            temp_map = {"none": 37.0, "warm": 37.6, "fever": 38.5, "high": 39.5}
            self.app.fever_temp_v.set(str(temp_map.get(value, 37.0)))
            self.app.chills_v.set(value in ("fever", "high"))
        elif key == "breathing":
            self.app.breathe_v.set(value)
        elif key == "sick_dizzy":
            has = value in ("nausea", "dizzy", "both")
            self.app.nausea_v.set(has)
            self.app.other_v.set(has)
        elif key == "daily_activity":
            if hasattr(self.app, "activity_v"):
                self.app.activity_v.set(value)
            self.app.other_v.set(value <= 2)

    def _friendly(self, key, value):
        if key == "when":
            if value == 0:  return "Today"
            if value <= 1:  return "Yesterday"
            if value <= 5:  return f"{value} days ago"
            return "Over a week"
        elif key == "severity":     return f"{value} / 10"
        elif key == "fever_yn":
            return {"none":"No fever","warm":"Warm","fever":"Fever","high":"High fever"}.get(value, value)
        elif key == "breathing":    return f"{value} / 10"
        elif key == "sick_dizzy":
            return {"none":"No","nausea":"Sick stomach","dizzy":"Dizzy","both":"Both"}.get(value, value)
        elif key == "daily_activity":
            return {4:"Fully normal",3:"Mostly OK",2:"Struggling",1:"Cannot function"}.get(value, str(value))
        return str(value)

    def _next_question(self):
        if self._step < len(self.QUESTIONS) - 1:
            self._step += 1
            self._show_question()
        else:
            self.app.analyse()

    def _go_back(self):
        if self._step > 0:
            self._step -= 1
            self._show_question()
        else:
            # Route back to whichever NLP screen launched this
            method = self.app.input_method.get()
            if method == "speak":
                self.app.go("nlp_speak")
            else:
                self.app.go("nlp_type")
