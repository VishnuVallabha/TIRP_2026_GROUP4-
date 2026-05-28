"""SACA — S2: Symptom classification method selection."""
import tkinter as tk
from tkinter import Canvas, Frame, Label, Entry, StringVar, BooleanVar, IntVar
from PIL import Image, ImageDraw, ImageTk, ImageFilter
from constants import *
from helpers  import mkcard, pill, h2r, r2h, lerp
from widgets  import SF, NavBar, voice_bar, progress_timeline
from tts      import speak

class S2_Method(Frame):
    def __init__(self,parent,app):
        super().__init__(parent,bg=BG)
        self.app=app
        self._ph={}
        self._nav=None; self._wrap=None

    def on_show(self):
        # Clear any global button binds leaked from S0_Cover
        try: self.unbind_all("<Button-1>")
        except: pass
        for w in self.winfo_children(): w.destroy()
        self._ph={}
        lang=self.app.lang.get()
        is_yo=lang=="Yolngu Matha"

        NavBar(self,
               "SYMPTOM CLASSIFICATION" if not is_yo else "MÄRR DHÄRUK YOLŊUNHA",
               "How would you like to identify your symptom?" if not is_yo else "Nhaltjan yolŋu matha djäma?",
               back=lambda:self.app.go("S1_Lang"),accent=OCHRE)

        wrap=Frame(self,bg=BG)
        wrap.pack(expand=1,fill="both")
        inner=Frame(wrap,bg=BG)
        inner.place(relx=0.5,rely=0.5,anchor="center")

        methods=[
            ("01",
             "SYMPTOM IDENTIFICATION" if not is_yo else "YIRRA DHÄRUK",
             "Tap a body part, then choose your symptom" if not is_yo else "Yirra dhäruk märr-yuŋupuy",
             "Visual selection — best for all users" if not is_yo else "Yolŋu matha djäma",
             OCHRE,True,"S3_BodyPart","🩺"),
            ("02",
             "SPEAK YOUR SYMPTOM" if not is_yo else "ŊUNHI DJÄMA",
             "Say your symptom — NLP will identify it" if not is_yo else "Ŋunhi Djäma — Sai Chetan Kari NLP",
             "Powered by XLM-R NLP  ·  English & Yolŋu Matha" if not is_yo else "NLP module — English ga Yolŋu matha",
             SKY,True,"nlp_speak","🎙"),
            ("03",
             "TYPE YOUR SYMPTOM" if not is_yo else "ŊUNHI MÄRR",
             "Type your symptom — NLP will classify it" if not is_yo else "Ŋunhi märr — NLP dhäruk",
             "Powered by keyword NLP  ·  English & Yolŋu Matha" if not is_yo else "NLP module — nhakun djäma",
             TERRA,True,"nlp_type","⌨"),
        ]
        for args in methods:
            self._card(inner,*args)

    def _card(self,parent,num,title,sub1,sub2,col,active,target,icon):
        W_,H_=720,100
        cv=Canvas(parent,width=W_,height=H_,bg=BG,highlightthickness=0,bd=0,
                  cursor="hand2" if active else "arrow")
        cv.pack(pady=10)
        bc=col if active else BORDER
        pn=mkcard(W_,H_,bc,BG_CARD,1 if not active else 2,14)
        ph=mkcard(W_,H_,bc,r2h(*lerp(h2r(BG_CARD),h2r(col),0.09)),3,14) if active else pn
        for p in (pn,ph):
            dr=ImageDraw.Draw(p); rr,gg,bb=h2r(bc)
            dr.rounded_rectangle([0,0,8,H_-1],radius=7,fill=(rr,gg,bb,255))
        k="m"+num
        self._ph["n"+k]=ImageTk.PhotoImage(pn)
        self._ph["h"+k]=ImageTk.PhotoImage(ph)
        bid=cv.create_image(0,0,anchor="nw",image=self._ph["n"+k])

        # Professional icon box
        ic_sz = 72
        ic_pil = Image.new("RGBA",(ic_sz,ic_sz),(0,0,0,0))
        ic_dr  = ImageDraw.Draw(ic_pil)
        if active:
            ic_dr.rounded_rectangle([0,0,ic_sz-1,ic_sz-1],radius=16,
                                     fill=h2r(col)+(255,))
            # subtle inner glow
            ic_dr.rounded_rectangle([2,2,ic_sz-3,ic_sz-3],radius=14,
                                     outline=(255,255,255,60),width=2)
        else:
            ic_dr.rounded_rectangle([0,0,ic_sz-1,ic_sz-1],radius=16,
                                     fill=h2r(BG_ALT)+(255,),
                                     outline=h2r(BORDER)+(200,),width=2)
        ic_ref = ImageTk.PhotoImage(ic_pil)
        setattr(self, f"_ic{num}", ic_ref)
        cv.create_image(16, H_//2-ic_sz//2, anchor="nw", image=ic_ref)
        cv.create_text(16+ic_sz//2, H_//2, text=icon,
                       font=("Segoe UI Emoji", 28),
                       fill="#FFFFFF" if active else TXT4,
                       anchor="center")

        tx=104
        cv.create_text(tx,H_//2-22,text=f"{num}.  {title}",
                       font=("Segoe UI",15,"bold"),
                       fill=TXT1 if active else TXT4,anchor="w")
        cv.create_text(tx,H_//2+2,text=sub1,
                       font=("Segoe UI",11),fill=col if active else TXT4,anchor="w")
        cv.create_text(tx,H_//2+20,text=sub2,
                       font=("Segoe UI",9),fill=TXT3 if active else TXT4,anchor="w")
        if active:
            cv.create_text(W_-20,H_//2,text="→",font=("Segoe UI",22,"bold"),
                           fill=col,anchor="e")
        else:
            cv.create_text(W_-30,H_//2,text="Coming soon",
                           font=("Segoe UI",9,"italic"),fill=TXT4,anchor="e")

        if active and target:
            # Map target → input_method value before navigating
            _method_map = {
                "S3_BodyPart": "photo",
                "nlp_speak":   "speak",
                "nlp_type":    "type",
            }
            def _go(t=target):
                m = _method_map.get(t, "photo")
                self.app.input_method.set(m)
                self.app.go(t)
            cv.bind("<Button-1>", lambda e: _go())
            cv.bind("<Enter>",lambda e:cv.itemconfig(bid,image=self._ph["h"+k]))
            cv.bind("<Leave>",lambda e:cv.itemconfig(bid,image=self._ph["n"+k]))

