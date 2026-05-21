"""SACA — S1: Language selection (English / Yolŋu Matha)."""
import tkinter as tk
from tkinter import Canvas, Frame, Label, Entry, StringVar, BooleanVar, IntVar
from PIL import Image, ImageDraw, ImageTk, ImageFilter
from constants import *
from helpers  import mkcard, pill, h2r, r2h, lerp
from widgets  import SF, NavBar, voice_bar, progress_timeline
from tts      import speak

class S1_Lang(Frame):
    def __init__(self,parent,app):
        super().__init__(parent,bg=BG)
        self.app=app
        self._ph={}
        self._build()

    def _build(self):
        # Warm gradient background
        bg_cv=Canvas(self,bg=BG,highlightthickness=0,bd=0)
        bg_cv.place(relx=0,rely=0,relwidth=1,relheight=1)
        bg_cv.bind("<Configure>",lambda e:self._draw_bg(bg_cv,e.width,e.height))

        # Center content
        wrap=Frame(self,bg=BG)
        wrap.place(relx=0.5,rely=0.5,anchor="center")

        # Heading
        Label(wrap,text="🌏",font=("Segoe UI Emoji",64),bg=BG).pack(pady=(0,12))

        Label(wrap,text="Choose Your Language",
              font=("Segoe UI",30,"bold"),fg=TXT1,bg=BG).pack()

        Label(wrap,text="Nhuma dhäruk yolŋunha bili?",
              font=("Segoe UI",16,"italic"),fg=TXT3,bg=BG).pack(pady=(4,8))

        # Divider
        Frame(wrap,height=2,bg=OCHRE,width=400).pack(pady=14)

        Label(wrap,text="Select the language you would like to use throughout the app",
              font=("Segoe UI",12),fg=TXT3,bg=BG).pack(pady=(0,28))

        # English button
        self._lang_btn(wrap,"ENGLISH","Continue in English",
                       "Read and answer in English",
                       OCHRE,
                       lambda:(self.app.lang.set("English"),self.app.go("S2_Method")))
        Label(wrap,bg=BG).pack(pady=6)

        # Yolngu button
        self._lang_btn(wrap,"YOLŊU MATHA","Yirra dhäruk Yolŋunha djäma",
                       "Dhäruk ga yolŋu matha djäma",
                       GREEN,
                       lambda:(self.app.lang.set("Yolngu Matha"),self.app.go("S2_Method")))

        Frame(wrap,height=1,bg=BORDER,width=520).pack(pady=(20,8))
        Label(wrap,
              text="⚠  Yolŋu Matha translations are approximate — community review pending.",
              font=("Segoe UI",9,"italic"),fg=TXT3,bg=BG).pack()
        Label(wrap,text="← Back",font=("Segoe UI",11),
              fg=TXT3,bg=BG,cursor="hand2").pack(pady=(14,0))
        wrap.winfo_children()[-1].bind("<Button-1>",lambda e:self.app.go("S0_Cover"))

    def _lang_btn(self,parent,title,native,desc,col,cmd):
        BW,BH=520,90
        cv=Canvas(parent,width=BW,height=BH,bg=BG,highlightthickness=0,bd=0,cursor="hand2")
        cv.pack(pady=4)

        pn=mkcard(BW,BH,col,BG_CARD,2,18)
        r,g,b=lerp(BG_CARD,col,0.08)
        ph=mkcard(BW,BH,col,r2h(r,g,b),3,18)
        # left coloured strip
        for p in (pn,ph):
            dr=ImageDraw.Draw(p); rr,gg,bb=h2r(col)
            dr.rounded_rectangle([0,0,10,BH-1],radius=9,fill=(rr,gg,bb,255))

        k=title[:2]
        self._ph["n"+k]=ImageTk.PhotoImage(pn)
        self._ph["h"+k]=ImageTk.PhotoImage(ph)
        bid=cv.create_image(0,0,anchor="nw",image=self._ph["n"+k])

        cv.create_text(30,BH//2-16,text=title,
                       font=("Segoe UI",20,"bold"),fill=TXT1,anchor="w")
        cv.create_text(30,BH//2+6,text=native,
                       font=("Segoe UI",13),fill=col,anchor="w")
        cv.create_text(30,BH//2+24,text=desc,
                       font=("Segoe UI",10),fill=TXT3,anchor="w")
        cv.create_text(BW-22,BH//2,text="→",
                       font=("Segoe UI",26,"bold"),fill=col,anchor="e")

        cv.bind("<Button-1>",lambda e:cmd())
        cv.bind("<Enter>",lambda e:cv.itemconfig(bid,image=self._ph["h"+k]))
        cv.bind("<Leave>",lambda e:cv.itemconfig(bid,image=self._ph["n"+k]))

    def _draw_bg(self,cv,W,H):
        if W<2 or H<2: return
        grad=Image.new("RGB",(W,H))
        dr=ImageDraw.Draw(grad)
        for y in range(H):
            t=y/H
            r=int(255-15*t); g=int(248-20*t); b=int(240-25*t)
            dr.line([(0,y),(W,y)],fill=(r,g,b))
        cv._bg=ImageTk.PhotoImage(grad)
        cv.delete("bg")
        cv.create_image(0,0,anchor="nw",image=cv._bg,tags="bg")
        cv.tag_lower("bg")

# ══════════════════════════════════════════════════════════════════
# S2 — SYMPTOM CLASSIFICATION  (renamed from Input Method)
