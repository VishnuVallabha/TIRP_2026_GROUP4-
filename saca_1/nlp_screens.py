"""SACA — NLP Speak and NLP Type screens."""
import tkinter as tk
import threading
from tkinter import Canvas, Frame, Label, Entry, StringVar, BooleanVar, IntVar
from PIL import Image, ImageDraw, ImageTk, ImageFilter
from constants import *
from helpers  import mkcard, pill, h2r, r2h, lerp, load_cover, download_photos, get_photo, _load_photo_from_disk, _dir, draw_hd_icon
from widgets  import SF, NavBar, voice_bar, progress_timeline
from tts      import speak, speak_lang

def _load_nlp_bridge():
    try:
        import importlib.util, os, sys
        bridge_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                   "saca_nlp_bridge.py")
        spec = importlib.util.spec_from_file_location("saca_nlp_bridge", bridge_path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        print("[NLP] Bridge loaded OK")
        return mod
    except Exception as e:
        print(f"[NLP] Bridge not loaded: {e}")
        return None

_NLP = _load_nlp_bridge()

def _basic_match(text):
    """Keyword-based symptom matcher used when NLP bridge is unavailable."""
    t = text.lower().strip()
    KEYWORDS = {
        "headache":   ["headache","head","migraine","head pain","head ache","aching head"],
        "fever":      ["fever","temperature","hot","feverish","high temp","burning up","pyrexia"],
        "chest":      ["chest","chest pain","heart","cardiac","chest tight","palpitation"],
        "cough":      ["cough","coughing","cough up","dry cough","wet cough"],
        "stomach":    ["stomach","stomach pain","belly","abdomen","abdominal","nausea",
                       "vomit","vomiting","tummy","gut","gastro","bowel"],
        "breathless": ["breath","breathless","breathing","short of breath","can't breathe",
                       "hard to breathe","wheeze","asthma","suffocate"],
        "dizziness":  ["dizzy","dizziness","dizzy spell","light headed","vertigo","spinning"],
        "fatigue":    ["tired","fatigue","exhausted","weak","no energy","lethargic","weary"],
        "rash":       ["rash","skin","itch","itchy","hives","redness","spots","breakout"],
        "back":       ["back","back pain","spine","lower back","upper back","backache"],
        "throat":     ["throat","sore throat","throat pain","swallowing","tonsil","strep"],
        "vomiting":   ["vomit","vomiting","throwing up","throw up","sick stomach","nausea"],
    }
    NAME_MAP = {
        "headache":   "Headache",
        "fever":      "Fever",
        "chest":      "Chest Pain",
        "cough":      "Cough",
        "stomach":    "Stomach Pain",
        "breathless": "Hard to Breathe",
        "dizziness":  "Feeling Dizzy",
        "fatigue":    "Very Tired",
        "rash":       "Skin Rash",
        "back":       "Back Pain",
        "throat":     "Sore Throat",
        "vomiting":   "Vomiting",
    }
    for key, words in KEYWORDS.items():
        if any(w in t for w in words):
            return {"symptom": NAME_MAP[key], "key": key, "days": None, "error": None}
    return {"symptom": None, "key": None, "days": None,
            "error": "Could not identify symptom from text"}



class S_NLP_Speak(Frame):
    """
    Voice input screen — styled exactly like s3_bodypart (pic selection).
    Left/right columns: clickable symptom buttons.
    Centre: mic visualiser + speak button.
    After recognition: highlights the matched button and enables START QUESTIONS.
    """

    # Same regions as s3_bodypart
    ALL_SYMPTOMS = [
        ("headache",  "Head / Headache",  "Nuthu",        "🧠", SKY),
        ("throat",    "Throat / Cough",   "Dhawu",        "🗣", OCHRE),
        ("chest",     "Chest Pain",       "Buku-djarrka", "❤",  TERRA),
        ("stomach",   "Stomach Pain",     "Wana",         "🤢", GOLD),
        ("back",      "Back Pain",        "Galk",         "🦴", "#795548"),
        ("fever",     "Fever",            "Marr",         "🌡", "#E53935"),
        ("breathless","Hard to Breathe",  "Gurrku",       "💨", "#5B8DB8"),
        ("fatigue",   "Very Tired",       "Djaka",        "😴", "#5B7A6B"),
    ]

    SYMPTOM_NAMES = {
        "headache":   "Headache",
        "throat":     "Sore Throat",
        "chest":      "Chest Pain",
        "stomach":    "Stomach Pain",
        "back":       "Back Pain",
        "fever":      "Fever",
        "breathless": "Hard to Breathe",
        "fatigue":    "Very Tired",
    }

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app      = app
        self._refs    = {}
        self._sel_key = None
        self._busy    = False

    def on_show(self):
        # Clear any global button binds leaked from S0_Cover
        try: self.unbind_all("<Button-1>")
        except: pass
        # Stamp input_method immediately — must happen before S4_Questions.on_show()
        self.app.input_method.set("speak")
        for w in self.winfo_children(): w.destroy()
        self._refs    = {}
        self._sel_key = None
        self._busy    = False
        self._build()

    def _build(self):
        is_yo_nb = self.app.lang.get() == "Yolngu Matha"
        NavBar(self,
               "ŊUNHI DJÄMA DHÄRUK" if is_yo_nb else "SPEAK YOUR SYMPTOM",
               "Nhuma djäma ga buku-dhukarr nhä" if is_yo_nb else "Press Speak Now and say your symptom clearly",
               back=lambda: self.app.go("S2_Method"), accent=SKY)

        progress_timeline(self, current_step=0)

        hdr = Frame(self, bg=BG)
        hdr.pack(pady=(6, 2))
        Label(hdr, text="Nhaltjan nhe wayin?" if self.app.lang.get()=="Yolngu Matha" else "What is your symptom?",
              font=("Segoe UI", 22, "bold"), fg=TXT1, bg=BG).pack()
        is_yo_sub = self.app.lang.get() == "Yolngu Matha"
        Label(hdr, text="Nhuma djäma bäpa tap" if is_yo_sub else "Speak or tap a button to select",
              font=("Segoe UI", 11, "italic"), fg=TXT3, bg=BG).pack(pady=(2, 0))

        # ── Continue button packed FIRST (bottom) ─────────────────
        BW, BH = 380, 54
        bot = Frame(self, bg=BG)
        bot.pack(side="bottom", fill="x", pady=(6, 10))
        btn_frame = Frame(bot, bg=BG)
        btn_frame.pack(anchor="center")
        self._cont_cv = Canvas(btn_frame, width=BW, height=BH, bg=BG,
                               highlightthickness=0, bd=0)
        self._cont_cv.pack()
        self._refresh_continue(enabled=False)

        # ── 3-column layout ───────────────────────────────────────
        outer = Frame(self, bg=BG)
        outer.pack(fill="both", expand=1, padx=10, pady=(4, 0))

        left_col = Frame(outer, bg=BG, width=185)
        left_col.pack(side="left", fill="y", anchor="n", pady=4)
        left_col.pack_propagate(False)

        centre = Frame(outer, bg=BG)
        centre.pack(side="left", fill="both", expand=1, padx=8)

        right_col = Frame(outer, bg=BG, width=185)
        right_col.pack(side="left", fill="y", anchor="n", pady=4)
        right_col.pack_propagate(False)

        # Left: first 4 symptoms
        for sym in self.ALL_SYMPTOMS[:4]:
            self._sym_btn(left_col, sym)

        # Right: next 4 symptoms
        for sym in self.ALL_SYMPTOMS[4:]:
            self._sym_btn(right_col, sym)

        # ── Centre: mic panel ─────────────────────────────────────
        mic_wrap = Frame(centre, bg=BG)
        mic_wrap.pack(expand=1, anchor="center")

        # Status label
        self._status = Label(mic_wrap,
                             text=("Nhuma ŊUNHI DJÄMA ga dhäruk" if self.app.lang.get()=="Yolngu Matha" else "Press Speak Now and say your symptom"),
                             font=("Segoe UI", 12), fg=TXT3, bg=BG,
                             wraplength=280, justify="center")
        self._status.pack(pady=(0, 8))

        # Mic canvas — pulsing circle
        self._mic_cv = Canvas(mic_wrap, width=200, height=200,
                              bg=BG, highlightthickness=0, bd=0)
        self._mic_cv.pack()
        self._draw_mic("idle")

        # SPEAK NOW button — same pill style as s3_bodypart continue button
        BW2, BH2 = 260, 56
        self._speak_cv = Canvas(mic_wrap, width=BW2, height=BH2,
                                bg=BG, highlightthickness=0, bd=0,
                                cursor="hand2")
        self._speak_cv.pack(pady=10)
        self._draw_speak_btn("ready")
        self._speak_cv.bind("<Button-1>", lambda e: self._on_speak_click())

        # Result label (hidden until recognised)
        self._result_lbl = Label(mic_wrap, text="",
                                 font=("Segoe UI", 12, "bold"),
                                 fg=GREEN, bg=BG, wraplength=260,
                                 justify="center")
        self._result_lbl.pack(pady=4)

    # ── Symptom side button — exact same style as s3_bodypart ──────
    def _sym_btn(self, parent, sym_data):
        key, en, yo, icon, color = sym_data
        BW_, BH_ = 178, 72

        cv = Canvas(parent, width=BW_, height=BH_, bg=BG,
                    highlightthickness=0, bd=0, cursor="hand2")
        cv.pack(pady=3, padx=3)

        def _render(selected=False):
            img = Image.new("RGBA", (BW_, BH_), (0, 0, 0, 0))
            dr  = ImageDraw.Draw(img)
            rr, gg, bb = h2r(color)
            if selected:
                dr.rounded_rectangle([0, 0, BW_-1, BH_-1], radius=14,
                                      fill=(rr, gg, bb, 25),
                                      outline=(rr, gg, bb, 255), width=3)
            else:
                dr.rounded_rectangle([0, 0, BW_-1, BH_-1], radius=14,
                                      fill=(255, 255, 255, 255),
                                      outline=(185, 195, 215, 255), width=2)
            ic = 34
            ix_, iy_ = 10, (BH_ - ic) // 2
            dr.rounded_rectangle([ix_, iy_, ix_+ic, iy_+ic], radius=9,
                                   fill=(rr, gg, bb, 230 if selected else 195))
            base = Image.new("RGBA", (BW_, BH_), (247, 248, 252, 0))
            return Image.alpha_composite(base, img)

        k = "sb_" + key
        self._refs[k+"_n"] = ImageTk.PhotoImage(_render(False))
        self._refs[k+"_s"] = ImageTk.PhotoImage(_render(True))

        bid = cv.create_image(0, 0, anchor="nw", image=self._refs[k+"_n"])
        try:
            ic_pil2 = draw_hd_icon(key, size=ic, bg_col=color, fg_col="#FFFFFF")
            ic_ref2 = ImageTk.PhotoImage(ic_pil2)
            self._refs[k+"_sicon"] = ic_ref2
            cv.create_image(10, (BH_-ic)//2, anchor="nw", image=ic_ref2)
        except Exception:
            cv.create_text(10+17, BH_//2, text=icon,
                           font=("Segoe UI Emoji", 14), fill="#FFFFFF", anchor="center")
        cv.create_text(10+34+10, BH_//2-9, text=en,
                       font=("Segoe UI", 11, "bold"), fill=TXT1, anchor="w")
        cv.create_text(10+34+10, BH_//2+8, text=yo,
                       font=("Segoe UI", 9, "italic"), fill=TXT3, anchor="w")

        self._refs[k+"_cv"]  = cv
        self._refs[k+"_bid"] = bid
        cv.bind("<Button-1>",
                lambda e, k_=key, c_=color, n_=en: self._select(k_, c_, n_))

    # ── Mic visualiser ─────────────────────────────────────────────
    def _draw_mic(self, state):
        cv = self._mic_cv
        cv.delete("all")
        cx, cy, r = 100, 100, 70

        colors = {
            "idle":       ("#E8EDF5", SKY,   "#FFFFFF"),
            "listening":  (TERRA,    "#FF6B6B", "#FFFFFF"),
            "processing": (OCHRE,    "#FFD700", "#FFFFFF"),
        }
        ring_col, fill_col, icon_col = colors.get(state, colors["idle"])

        # Outer pulse ring
        cv.create_oval(cx-r-12, cy-r-12, cx+r+12, cy+r+12,
                       fill="", outline=ring_col, width=3)
        # Main circle
        cv.create_oval(cx-r, cy-r, cx+r, cy+r,
                       fill=fill_col, outline="", width=0)
        # Mic emoji
        cv.create_text(cx, cy, text="🎙",
                       font=("Segoe UI Emoji", 38), fill=icon_col, anchor="center")

        if state == "listening":
            # Animated rings
            for i, alpha_r in enumerate([r+20, r+32, r+44]):
                cv.create_oval(cx-alpha_r, cy-alpha_r, cx+alpha_r, cy+alpha_r,
                               fill="", outline=TERRA,
                               width=max(1, 3-i))

    def _draw_speak_btn(self, state):
        BW2, BH2 = 260, 56
        self._speak_cv.delete("all")
        cfg = {
            "ready":      (SKY,    "🎤  ŊUNHI DJÄMA" if self.app.lang.get()=="Yolngu Matha" else "🎤  SPEAK NOW"),
            "listening":  (TERRA,  "🔴  Listening..."),
            "processing": (OCHRE,  "⏳  Processing..."),
        }
        col, txt = cfg.get(state, cfg["ready"])
        pil = pill(BW2, BH2, col, BH2//2)
        self._refs["speak_btn"] = ImageTk.PhotoImage(pil)
        self._speak_cv.create_image(0, 0, anchor="nw",
                                    image=self._refs["speak_btn"])
        self._speak_cv.create_text(BW2//2, BH2//2, text=txt,
                                   font=("Segoe UI", 14, "bold"),
                                   fill="#FFFFFF", anchor="center")

    # ── Button / side button selection ─────────────────────────────
    def _select(self, key, color, en):
        self._sel_key = key
        sym_name = self.SYMPTOM_NAMES.get(key, en)
        # Update all button visuals
        for sym in self.ALL_SYMPTOMS:
            k = "sb_" + sym[0]
            rcv  = self._refs.get(k+"_cv")
            rbid = self._refs.get(k+"_bid")
            if rcv and rbid:
                rcv.itemconfig(rbid,
                    image=self._refs[k+("_s" if sym[0]==key else "_n")])
        self._result_lbl.configure(
            text=f"✓  {sym_name}  selected", fg=color)
        self._status.configure(
            text="Tap START QUESTIONS to continue", fg=TXT3)
        self._draw_mic("idle")

        # Set app state
        self.app.symptom = sym_name
        self.app.sym_c   = color
        self.app.sym_key = key
        self.app.selected_body_part = "fullbody"
        self.app.input_method.set("speak")
        self._refresh_continue(enabled=True, color=color)

    # ── Speak button click ─────────────────────────────────────────
    def _on_speak_click(self):
        if self._busy:
            return
        self._busy = True
        self._result_lbl.configure(text="")
        self._draw_speak_btn("listening")
        self._draw_mic("listening")
        self._status.configure(text="Adjusting for noise...", fg=SKY)
        threading.Thread(target=self._listen_thread, daemon=True).start()

    def _set_status(self, text, color=None):
        self.after(0, lambda: self._status.configure(
            text=text, fg=color or TXT3))

    def _listen_thread(self):
        import subprocess, sys
        try:
            import speech_recognition as sr
        except ImportError:
            self._set_status("Installing speech_recognition...", SKY)
            subprocess.run([sys.executable,"-m","pip","install","SpeechRecognition","-q"])
            import speech_recognition as sr

        is_yolngu = self.app.lang.get() == "Yolngu Matha"

        try:
            rec = sr.Recognizer()
            rec.dynamic_energy_threshold = False
            rec.energy_threshold         = 300   # fixed: was 50
            rec.pause_threshold          = 1.8   # longer for Yolnu speakers
            rec.phrase_threshold         = 0.1
            rec.non_speaking_duration    = 0.8

            try:
                mic = sr.Microphone()
            except Exception:
                self._set_status("No microphone found — check connection", TERRA)
                self.after(0, lambda: self._draw_speak_btn("ready"))
                self.after(0, lambda: self._draw_mic("idle"))
                self._busy = False
                return

            with mic as source:
                # Calibrate for room noise
                self._set_status("⏸  Hold still — calibrating mic...", TXT3)
                rec.adjust_for_ambient_noise(source, duration=1.0)
                self._set_status("🔴  Speak your symptom clearly!", TERRA)
                self.after(0, lambda: self._draw_speak_btn("listening"))
                self.after(0, lambda: self._draw_mic("listening"))
                try:
                    audio = rec.listen(source, timeout=12, phrase_time_limit=8)
                except sr.WaitTimeoutError:
                    self._set_status("No speech heard — tap mic and try again", TERRA)
                    self.after(0, lambda: self._draw_speak_btn("ready"))
                    self.after(0, lambda: self._draw_mic("idle"))
                    self._busy = False
                    return

            self._set_status("Processing...", TXT3)
            self.after(0, lambda: self._draw_speak_btn("processing"))
            self.after(0, lambda: self._draw_mic("processing"))

            text = None

            # Try Groq Whisper first (handles Yolnu phonetics best)
            try:
                import tempfile, os, requests
                from saca_nlp_bridge import _get_groq_key
                groq_key = _get_groq_key()
                if groq_key:
                    wav_bytes = audio.get_wav_data()
                    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
                        tmp.write(wav_bytes)
                        tmp_path = tmp.name
                    try:
                        with open(tmp_path, "rb") as f:
                            resp = requests.post(
                                "https://api.groq.com/openai/v1/audio/transcriptions",
                                headers={"Authorization": f"Bearer {groq_key}"},
                                files={"file": ("audio.wav", f, "audio/wav")},
                                data={"model": "whisper-large-v3",
                                      "language": "en",
                                      "temperature": "0",
                                      "response_format": "json"},
                                timeout=8)
                        if resp.status_code == 200:
                            text = resp.json().get("text", "").strip()
                            print(f"[Mic] Whisper heard: '{text}'")
                    finally:
                        try: os.unlink(tmp_path)
                        except: pass
            except Exception as we:
                print(f"[Mic] Whisper unavailable: {we}")

            # Fallback: Google Speech — force en-AU only
            # Do NOT try multiple languages: Google auto-detects and may
            # pick Hindi/other languages for Yolnu sounds (Devanagari output)
            if not text:
                try:
                    text = rec.recognize_google(audio, language="en-AU")
                    if text:
                        print(f"[Mic] Google SR heard: '{text}'")
                except sr.UnknownValueError:
                    pass
                except sr.RequestError:
                    pass

            if not text:
                try: text = rec.recognize_sphinx(audio)
                except Exception: pass

            # For Yolnu: translate phonetic output → English before NLP
            if is_yolngu and text:
                try:
                    from saca_nlp_bridge import _translate_yolngu
                    translated = _translate_yolngu(text)
                    print(f"[Mic] Yolnu: '{text}' → '{translated}'")
                    # Run NLP on translated text
                    try: age = self.app.age_v.get()
                    except Exception: age = 30
                    result = (_NLP.extract_symptom_from_text(
                                  translated, language="yolngu", age=age)
                              if _NLP else _basic_match(translated))
                    self.after(0, lambda t=text, r=result: self._show_result(t, r))
                    return
                except Exception as te:
                    print(f"[Mic] Yolnu translate error: {te}")

            # English path
            try: age = self.app.age_v.get()
            except Exception: age = 30
            result = (_NLP.extract_symptom_from_text(text, language="english", age=age)
                      if (_NLP and text) else _basic_match(text or ""))
            self.after(0, lambda t=text, r=result: self._show_result(t, r))

        except Exception as e:
            self._set_status(f"Error: {str(e)[:60]}", TERRA)
            self.after(0, lambda: self._draw_speak_btn("ready"))
            self.after(0, lambda: self._draw_mic("idle"))
            self._busy = False

    def _show_result(self, spoken, r):
        self._draw_speak_btn("ready")
        self._draw_mic("idle")
        self._busy = False

        if r.get("symptom"):
            key = r.get("key", "fever")
            sym = r["symptom"]
            col = next((s[4] for s in self.ALL_SYMPTOMS if s[0]==key), SKY)
            self._select(key, col, sym)
            self._set_status(f'Heard: "{spoken}"', GREEN)
        else:
            err = r.get("error", "No symptom matched")
            self._set_status(f'Heard: "{spoken}"  —  {err}', TERRA)
            self._result_lbl.configure(
                text="Try: headache / fever / chest pain / stomach pain",
                fg=TERRA)

    # ── Continue button ────────────────────────────────────────────
    def _refresh_continue(self, enabled=False, color=SKY):
        cv = self._cont_cv
        BW, BH = int(cv["width"]), int(cv["height"])
        cv.delete("all")
        if enabled:
            pil = pill(BW, BH, color, BH//2)
            self._refs["cont"] = ImageTk.PhotoImage(pil)
            cv.create_image(0, 0, anchor="nw", image=self._refs["cont"])
            cv.create_text(BW//2, BH//2, text="START QUESTIONS  ->",
                           font=("Segoe UI", 14, "bold"),
                           fill="#FFFFFF", anchor="center")
            cv["cursor"] = "hand2"
            cv.bind("<Button-1>", lambda e: self._go_questions())
        else:
            pil = pill(BW, BH, "#C8D0DC", BH//2)
            self._refs["cont"] = ImageTk.PhotoImage(pil)
            cv.create_image(0, 0, anchor="nw", image=self._refs["cont"])
            cv.create_text(BW//2, BH//2,
                           text=("Nhuma djäma bäpa tap ga nhuma" if self.app.lang.get()=="Yolngu Matha" else "Speak or tap a symptom to continue"),
                           font=("Segoe UI", 12),
                           fill="#6B7A8D", anchor="center")
            cv["cursor"] = "arrow"
            cv.unbind("<Button-1>")

    def _go_questions(self):
        if not self._sel_key:
            return
        # Speak path → voice-driven question flow
        self.app.input_method.set("speak")
        self.app.go("S4_Questions_Voice")


class S_NLP_Type(Frame):
    """
    Type-your-symptom screen — 6 questions one per slide.
    Q1: What is your main symptom?
    Q2: Where does it hurt?
    Q3: How long have you had it?
    Q4: How bad is it? (1-10)
    Q5: Any other symptoms?
    Q6: Have you taken any medicine?
    """
    QUESTIONS = [
        {
            "q":      "What is your main symptom?",
            "yo_q":   "Nhaltjan nhe wayin?",
            "hint":   "e.g.  headache  /  chest pain  /  fever  /  stomach pain",
            "yo_hint":"e.g.  buku-dhukarr  /  guku-dhukarr  /  dharpa-wuku  /  butu-dhukarr",
            "key":    "symptom",
            "type":   "text",
        },
        {
            "q":      "Where does it hurt?",
            "yo_q":   "Nhaltjan ŋuli nhe dhukarr?",
            "hint":   "e.g.  head  /  chest  /  stomach  /  back  /  throat  /  arms  /  legs",
            "yo_hint":"e.g.  buku (head)  /  guku (chest)  /  butu (stomach)  /  maru (back)",
            "key":    "location",
            "type":   "text",
        },
        {
            "q":      "How long have you had this symptom?",
            "yo_q":   "Nhaltjan warray ga djäma?",
            "hint":   "e.g.  today  /  yesterday  /  2 days  /  a week  /  longer",
            "yo_hint":"e.g.  dhuwali (today)  /  warray (yesterday)  /  rua dhuwala (2 days)",
            "key":    "duration",
            "type":   "text",
        },
        {
            "q":      "How bad is the pain or discomfort?",
            "yo_q":   "Nhaltjan dhukarr? Wanggany ga lurrkun.",
            "hint":   "Type a number from 1 (very mild) to 10 (worst possible)",
            "yo_hint":"Wanggany (1) = mäkitj  ·  Lurrkun (10) = djorra dhukarr",
            "key":    "severity",
            "type":   "number",
        },
        {
            "q":      "Do you have any other symptoms?",
            "yo_q":   "Nhe wayin bäpa ga yolŋu matha?",
            "hint":   "e.g.  vomiting  /  dizziness  /  chills  /  hard to breathe  /  none",
            "yo_hint":"e.g.  gulktji (vomiting)  /  buku-wuku (dizzy)  /  bulu-wuku (chills)  /  yaka (none)",
            "key":    "other",
            "type":   "text",
        },
        {
            "q":      "Have you taken any medicine?",
            "yo_q":   "Nhe märr-djorra ŋunhi?",
            "hint":   "e.g.  Panadol  /  paracetamol  /  antibiotics  /  nothing",
            "yo_hint":"e.g.  Panadol  /  paracetamol  /  yaka (nothing)",
            "key":    "medicine",
            "type":   "text",
        },
    ]

    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app       = app
        self._step     = 0
        self._answers  = {}

    def on_show(self):
        # Stamp input_method immediately
        self.app.input_method.set("type")
        for w in self.winfo_children(): w.destroy()
        self._step    = 0
        self._answers = {}
        self._show_step()

    def _show_step(self):
        for w in self.winfo_children(): w.destroy()
        q_data = self.QUESTIONS[self._step]
        total  = len(self.QUESTIONS)
        step   = self._step

        if step == 0:
            back_dest = lambda: self.app.go("S2_Method")
        else:
            back_dest = lambda: self._go_back()
        NavBar(self, "TYPE YOUR SYMPTOM",
               "Type in English or Yolngu Matha",
               back=back_dest, accent=TERRA)

        # Progress dots
        dot_f = Frame(self, bg=BG)
        dot_f.pack(pady=(8, 0))
        for i in range(total):
            col = TERRA if i == step else (BORDER2 if i > step else GREEN)
            Frame(dot_f, bg=col, width=28 if i == step else 10,
                  height=10).pack(side="left", padx=3)

        # Step counter
        is_yo_ctr = self.app.lang.get() == "Yolngu Matha"
        ctr_txt = f"Dhäruk  {step+1}  /  {total}" if is_yo_ctr else f"Question  {step+1}  of  {total}"
        Label(self, text=ctr_txt,
              font=("Segoe UI", 11), fg=TXT3, bg=BG).pack(pady=(6, 0))

        # Big question
        wrap = Frame(self, bg=BG)
        wrap.pack(expand=1, anchor="center", padx=60)

        is_yo_t = self.app.lang.get() == "Yolngu Matha"
        q_text   = q_data.get("yo_q",   q_data["q"])    if is_yo_t else q_data["q"]
        h_text   = q_data.get("yo_hint", q_data["hint"]) if is_yo_t else q_data["hint"]

        Label(wrap, text=q_text,
              font=("Segoe UI", 22, "bold"), fg=TXT1, bg=BG,
              wraplength=700, justify="center").pack(pady=(0, 4))

        if is_yo_t:
            # Show English sub-label in grey below the Yolnu title
            Label(wrap, text=q_data["q"],
                  font=("Segoe UI", 13), fg=TXT3, bg=BG,
                  wraplength=700, justify="center").pack(pady=(0, 4))

        Label(wrap, text=h_text,
              font=("Segoe UI", 12), fg=TXT3, bg=BG,
              wraplength=640, justify="center").pack(pady=(0, 24))

        # Input box
        ef = Frame(wrap, bg=BORDER, width=560, height=60)
        ef.pack(); ef.pack_propagate(False)
        prev = self._answers.get(q_data["key"], "")
        entry = Entry(ef, font=("Segoe UI", 16), fg=TXT1, bg=BG_CARD,
                      relief="flat", bd=0, insertbackground=TERRA)
        entry.pack(fill="both", expand=1, padx=2, pady=2, ipady=10)
        if prev:
            entry.insert(0, prev)
        entry.focus()

        self._entry = entry

        # Status label
        self._status = Label(wrap, text="", font=("Segoe UI", 11), fg=TERRA, bg=BG)
        self._status.pack(pady=(8, 0))

        # Navigation buttons — packed BEFORE expand frame
        nav = Frame(self, bg=BG)
        nav.pack(side="bottom", pady=16, fill="x", padx=40)

        # Back button (not on first step)
        if step > 0:
            BW, BH = 160, 52
            bc = Canvas(nav, width=BW, height=BH, bg=BG,
                        highlightthickness=0, bd=0, cursor="hand2")
            bc.pack(side="left")
            pn = pill(BW, BH, BORDER2, BH//2)
            self._back_img = ImageTk.PhotoImage(pn)
            bc.create_image(0, 0, anchor="nw", image=self._back_img)
            bc.create_text(BW//2, BH//2, text="← Back",
                           font=("Segoe UI", 13, "bold"), fill=TXT1, anchor="center")
            bc.bind("<Button-1>", lambda e: self._go_back())

        # Next / Analyse button
        is_last = (step == total - 1)
        lbl_btn = "ANALYSE  →" if is_last else "NEXT  →"
        col_btn = TERRA if is_last else SKY
        BW2, BH2 = 220, 52
        nc = Canvas(nav, width=BW2, height=BH2, bg=BG,
                    highlightthickness=0, bd=0, cursor="hand2")
        nc.pack(side="right")
        pn2 = pill(BW2, BH2, col_btn, BH2//2)
        self._next_img = ImageTk.PhotoImage(pn2)
        nc.create_image(0, 0, anchor="nw", image=self._next_img)
        nc.create_text(BW2//2, BH2//2, text=lbl_btn,
                       font=("Segoe UI", 14, "bold"), fill="#FFFFFF", anchor="center")
        nc.bind("<Button-1>", lambda e: self._go_next())
        entry.bind("<Return>", lambda e: self._go_next())

    def _go_back(self):
        q_data = self.QUESTIONS[self._step]
        self._answers[q_data["key"]] = self._entry.get().strip()
        self._step -= 1
        self._show_step()

    def _go_next(self):
        q_data = self.QUESTIONS[self._step]
        val    = self._entry.get().strip()

        # Validate severity is a number 1-10
        if q_data["type"] == "number":
            try:
                n = int(val)
                if not 1 <= n <= 10:
                    raise ValueError
            except ValueError:
                self._status.configure(text="Please type a number between 1 and 10")
                return

        # First question must have something
        if self._step == 0 and not val:
            self._status.configure(text="Please type your symptom first")
            return

        # Accept blank for optional questions (steps 2+)
        self._answers[q_data["key"]] = val

        if self._step < len(self.QUESTIONS) - 1:
            self._step += 1
            self._show_step()
        else:
            self._analyse_all()

    def _analyse_all(self):
        """
        After the 6 text questions, identify the symptom from the typed answers,
        pre-fill what we know (severity, duration, medication, other symptoms),
        then route to S4_Questions so the patient completes the visual question
        cards (When / How bad / Fever / Breathing / Sick-Dizzy / Daily activity).

        This fixes the bug where typing Q6 jumped straight to symptom
        identification / result screen, skipping the visual triage cards.
        """
        sym_text = self._answers.get("symptom",  "")
        loc_text = self._answers.get("location", "")
        dur_text = self._answers.get("duration", "")
        sev_text = self._answers.get("severity", "")
        combined = f"{sym_text} {loc_text} {dur_text}".strip()

        # ── Identify symptom via NLP or keyword fallback ──────────
        lang = "yolngu" if self.app.lang.get() == "Yolngu Matha" else "english"
        r = (_NLP.extract_symptom_from_text(combined, language=lang,
                age=self.app.age_v.get())
             if _NLP else _basic_match(combined))

        if not r["symptom"]:
            # Could not identify — stay on Q6, show helpful error
            self._status.configure(
                text="Could not identify symptom. Try: headache / fever / chest pain / stomach pain / back pain")
            return

        # ── Pre-fill app state from typed answers ─────────────────

        # Severity
        try:
            sev = int(sev_text)
            if 1 <= sev <= 10:
                self.app.sev_v.set(sev)
        except (ValueError, TypeError):
            pass   # S4_Questions will let them pick it visually

        # Duration — pre-fill days_computed from typed duration text
        if r.get("days") is not None:
            try:
                self.app.days_computed = int(r["days"])
            except (TypeError, ValueError):
                self.app.days_computed = 1
        else:
            dur = dur_text.lower()
            if   any(w in dur for w in ["today","just","now","this morning"]):
                self.app.days_computed = 0
            elif any(w in dur for w in ["yesterday","1 day","one day","last night"]):
                self.app.days_computed = 1
            elif any(w in dur for w in ["2 day","two day","2-3","couple"]):
                self.app.days_computed = 2
            elif any(w in dur for w in ["week","7","seven"]):
                self.app.days_computed = 7
            # else leave at default; S4_Questions "When" card will set it properly

        # Medication
        med = self._answers.get("medicine", "").lower()
        if any(w in med for w in ["panadol","paracetamol","ibuprofen",
                                   "antibiotic","yes","took","taken","medicine"]):
            self.app.med_v.set(True)

        # Other symptoms — chills, nausea, breathing difficulty
        other = self._answers.get("other", "").lower()
        if any(w in other for w in ["chill","shiver","cold sweat"]):
            self.app.chills_v.set(True)
        if any(w in other for w in ["vomit","nausea","sick","queas"]):
            self.app.nausea_v.set(True)
        if any(w in other for w in ["breath","wheez","tight chest","can't breathe"]):
            self.app.breathe_v.set(7)
        if any(w in other for w in ["dizz","faint","light head","spinning"]):
            self.app.other_v.set(True)

        # Fever temperature — infer from combined text if mentioned
        all_text = (sym_text + " " + other).lower()
        if any(w in all_text for w in ["very high fever","40","41","burning"]):
            self.app.fever_temp_v.set("40.0")
        elif any(w in all_text for w in ["high fever","39","fever"]):
            self.app.fever_temp_v.set("39.0")
        elif any(w in all_text for w in ["fever","38","feverish","temperature","hot"]):
            self.app.fever_temp_v.set("38.5")
        elif any(w in all_text for w in ["warm","37.5","low grade"]):
            self.app.fever_temp_v.set("37.5")
        else:
            self.app.fever_temp_v.set("37.0")   # normal — no fever mentioned

        # Activity level — default to 3 (mostly OK) unless text suggests otherwise
        if any(w in all_text for w in ["cannot","can't","bed","lying","bedridden","help"]):
            self.app.activity_v.set(1)
        elif any(w in all_text for w in ["struggling","hard","difficult","barely"]):
            self.app.activity_v.set(2)
        else:
            self.app.activity_v.set(3)

        # ── Set symptom on app ────────────────────────────────────
        self.app.symptom = r["symptom"]
        self.app.sym_c   = next(
            (s["c"]   for s in SYMPTOMS if s["en"] == r["symptom"]), OCHRE)
        self.app.sym_key = next(
            (s["key"] for s in SYMPTOMS if s["en"] == r["symptom"]), "fever")
        self.app.input_method.set("type")
        self.app.selected_body_part = self.app.selected_body_part or "fullbody"

        # ── Go straight to analyse ────────────────────────────────
        # S4_Questions.on_show() resets all values on fresh entry,
        # so routing there would wipe everything we just set.
        # We have already filled: symptom, severity, duration, medication,
        # chills, nausea, breathing, other — call analyse() directly.
        self.app.analyse()