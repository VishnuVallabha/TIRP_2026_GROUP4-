"""
SACA — App (main Tk window + screen router).
Instantiates all screens, handles go(), analyse(), reset(), save_report().
"""
import tkinter as tk
import tkinter.messagebox
from tkinter import Canvas, Frame, Label, StringVar, BooleanVar, IntVar
import threading
from constants          import *
from tts                import _init_tts, speak
from triage             import triage, temp_band
from widgets            import NavBar

# ── Screen imports ───────────────────────────────────────────────
from s0_cover           import S0_Cover
from s1_lang            import S1_Lang
from s2_method          import S2_Method
from s3_bodypart        import S3_BodyPart
from s3_symptom         import S3_Symptom
from s4_questions       import S4_Questions
from s4_questions_text  import S4_Questions_Text
from s4_questions_voice import S4_Questions_Voice
from s5_result          import S5_Result
from nlp_screens        import S_NLP_Speak, S_NLP_Type

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SACA — Smart Adaptive Clinical Assistant")
        self.geometry("980x800"); self.minsize(880,720)
        self.configure(bg=BG); self.resizable(True,True)
        # state
        self.lang=StringVar(value="English")
        self.symptom=None; self.sym_c=OCHRE; self.sym_key="fever"
        self.age_v=IntVar(value=30)
        self.gender_v=StringVar(value="")
        self.allergy_v=StringVar(value="")
        self.input_method=StringVar(value="photo")  # "photo" | "text" | "speak"
        self.day_v=StringVar(value=""); self.mon_v=StringVar(value="")
        self.days_computed=1
        self.sev_v=IntVar(value=5)
        self.med_v=BooleanVar(value=False)
        self.other_v=BooleanVar(value=False)
        self.fever_temp_v=StringVar(value="37.0")
        self.pain_type_v=StringVar(value="")
        self.breathe_v=IntVar(value=1)
        self.chills_v=BooleanVar(value=False)
        self.nausea_v=BooleanVar(value=False)   # new Q: nausea/vomiting
        self.activity_v=IntVar(value=3)          # Q6: daily activity level 1-4
        # extra state
        self.font_size   = IntVar(value=12)   # accessibility font size
        self.result_key  = None               # last triage result
        self.triage_ts   = None               # timestamp of triage
        # ── Accessibility additions ──────────────────────────────
        self.selected_body_part  = None       # region key from S3_BodyPart
        self.body_part_symptoms  = None       # filtered symptom list (None=all)
        # Initialise TTS in background
        threading.Thread(target=_init_tts, daemon=True).start()
        self._sc={}
        c=Frame(self,bg=BG)
        c.place(relx=0,rely=0,relwidth=1,relheight=1)
        for Cls in [S0_Cover, S1_Lang, S2_Method, S3_BodyPart, S3_Symptom, S4_Questions, S4_Questions_Voice, S5_Result, S_NLP_Speak, S_NLP_Type]:
            s=Cls(c,self); self._sc[Cls.__name__]=s
            s.place(relx=0,rely=0,relwidth=1,relheight=1)
        self.go("S0_Cover")

    def go(self, name):
        """
        Navigation router — canonical flow:
          S0 → S1_Lang → S2_Method
            Photo:  → S3_BodyPart → S3_Symptom → S4_Questions → S5_Result
            Speak:  → S_NLP_Speak ─────────────→ S4_Questions → S5_Result
            Type:   → S_NLP_Type  ─────────────→ S4_Questions → S5_Result
        """
        # Resolve shorthand names
        aliases = {
            "nlp_speak": "S_NLP_Speak",
            "nlp_type":  "S_NLP_Type",
        }
        name = aliases.get(name, name)

        # S4_Questions_Text is retired — redirect to S4_Questions
        if name == "S4_Questions_Text":
            name = "S4_Questions"
        # S4_Questions_Voice is ACTIVE — speak path uses it

        s = self._sc.get(name)
        if s is None:
            print(f"[SACA] go(): unknown screen '{name}'")
            return
        if hasattr(s, "on_show"):
            s.on_show()
        s.lift()
        sym = self.symptom or ""
        self.title(f"SACA — Assessing: {sym}" if sym
                   else "SACA — Smart Adaptive Clinical Assistant")

    def analyse(self):
        # days_computed is set directly by the When question card
        d = max(1, getattr(self, "days_computed", 1) or 1)
        self.days_computed = d
        try: ft = float(self.fever_temp_v.get() or 37.0)
        except: ft = 37.0
        activity = getattr(self, "activity_v", None)
        activity = activity.get() if activity else 3
        res = triage(self.symptom or "", d, self.sev_v.get(),
                     self.med_v.get(), self.other_v.get(),
                     ft, self.pain_type_v.get(),
                     self.breathe_v.get(), self.chills_v.get(), activity)
        from datetime import datetime as _dt
        self.result_key = res
        self.triage_ts  = _dt.now().strftime("%d %b %Y  %H:%M:%S")
        self._sc["S5_Result"].set_result(res)
        self.go("S5_Result")

    def reset(self):
        self.symptom=None; self.sev_v.set(5)
        self.med_v.set(False); self.other_v.set(False)
        self.chills_v.set(False); self.breathe_v.set(1)
        self.nausea_v.set(False)
        self.activity_v.set(3)
        self.day_v.set(""); self.mon_v.set("")
        self.fever_temp_v.set("37.0"); self.pain_type_v.set("")
        self.result_key=None; self.triage_ts=None
        self.selected_body_part=None; self.body_part_symptoms=None
        self.input_method.set("photo")
        self.title("SACA — Smart Adaptive Clinical Assistant")
        self.go("S0_Cover")

    def save_report(self):
        """Save triage result as a .txt file on the desktop."""
        import os
        from datetime import datetime as _dt
        try: ft=float(self.fever_temp_v.get() or 37.0)
        except: ft=37.0
        tb,_=temp_band(ft)
        lines=[
            "="*60,
            "  SACA — TRIAGE REPORT",
            f"  Generated : {self.triage_ts or _dt.now().strftime('%d %b %Y  %H:%M:%S')}",
            "="*60,"",
            f"  Symptom      : {self.symptom or '—'}",
            f"  Onset        : {getattr(self,'days_computed',1)} day(s) ago",
            f"  Severity     : {self.sev_v.get()}/10",
            f"  Temperature  : {ft}°C  ({tb})",
            f"  Pain type    : {self.pain_type_v.get() or 'Not specified'}",
            f"  Breathing    : {self.breathe_v.get()}/10",
            f"  Chills       : {'Yes' if self.chills_v.get() else 'No'}",
            f"  Medication   : {'Yes' if self.med_v.get() else 'No'}",
            f"  Other areas  : {'Yes' if self.other_v.get() else 'No'}","",
            "-"*60,
            f"  RESULT       : {(self.result_key or '').upper()}",
            "-"*60,"",
        ]
        if self.result_key=="mild":
            lines+=["  RECOMMENDATION: Rest at home. Monitor symptoms.",
                    "  If severity increases, re-assess immediately."]
        elif self.result_key=="moderate":
            lines+=["  RECOMMENDATION: Visit Yirrkala Health Clinic within 24 hours.",
                    "  Clinic: Mon–Fri  8:00am – 5:00pm  |  ~2km from community centre",
                    "  Phone: (08) 8987 1000"]
        else:
            lines+=["  *** EMERGENCY — CALL 000 IMMEDIATELY ***",
                    "  Royal Flying Doctor Service: 1800 625 800",
                    "  Stay calm. Stay where you are. Have someone with you."]
        lines+=["","="*60,
                "  This report is generated by SACA (Swinburne University)",
                "  COS70008 Technology Innovation Project — S1 2026",
                "="*60]

        desktop=os.path.join(os.path.expanduser("~"),"Desktop")
        folder=os.path.join(desktop,"SACA_Reports")
        os.makedirs(folder,exist_ok=True)
        ts=_dt.now().strftime("%Y%m%d_%H%M%S")
        path=os.path.join(folder,f"SACA_Report_{ts}.txt")
        with open(path,"w",encoding="utf-8") as f:
            f.write("\n".join(lines))
        # Also save to Downloads as fallback
        dl_path=os.path.join(os.path.expanduser("~"),"Downloads",f"SACA_Report_{ts}.txt")
        with open(dl_path,"w",encoding="utf-8") as f:
            f.write("\n".join(lines))
        tk.messagebox.showinfo("Report Saved",
            f"Triage report saved to:\n{path}\n\nAlso copied to Downloads.")

# ══════════════════════════════════════════════════════════════════
# S0 — FULL SCREEN COVER WITH ABORIGINAL PAINTING
