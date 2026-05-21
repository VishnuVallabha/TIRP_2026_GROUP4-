"""SACA — S0: Full-screen Aboriginal cover / splash screen."""
import tkinter as tk
from tkinter import Canvas, Frame, Label, Entry, StringVar, BooleanVar, IntVar
from PIL import Image, ImageDraw, ImageTk, ImageFilter
from constants import *
from helpers  import mkcard, pill, h2r, r2h, lerp, load_cover, _dir
from widgets  import SF, NavBar, voice_bar, progress_timeline
from tts      import speak

class S0_Cover(Frame):
    def __init__(self,parent,app):
        super().__init__(parent,bg=BG)
        self.app=app
        self.cv=Canvas(self,bg=BG,highlightthickness=0,bd=0)
        self.cv.place(relx=0,rely=0,relwidth=1,relheight=1)
        self.cv.bind("<Configure>",self._draw)

    def _draw(self,e=None):
        W=self.cv.winfo_width(); H=self.cv.winfo_height()
        if W<10 or H<10: return
        self.cv.delete("all")

        # Full screen Aboriginal painting
        art=load_cover(W,H)
        # Subtle dark overlay so text reads clearly
        ov=Image.new("RGBA",(W,H),(0,0,0,0))
        dv=ImageDraw.Draw(ov)
        # Gradient overlay — more transparent at top, darker at bottom third
        for y in range(H):
            t=y/H
            a=int(30+140*t*t)  # gentle vignette
            dv.line([(0,y),(W,y)],fill=(0,0,0,a))
        art=Image.alpha_composite(art.convert("RGBA"),ov).convert("RGB")
        self._bg=ImageTk.PhotoImage(art)
        self.cv.create_image(0,0,anchor="nw",image=self._bg)

        cx=W//2

        # Top badge
        self.cv.create_text(cx,int(H*0.18),
            text="✚  SACA",
            font=("Segoe UI",48,"bold"),
            fill="#FFFFFF",anchor="center")

        self.cv.create_text(cx,int(H*0.27),
            text="Swin Smart Adaptive Clinical Assistant",
            font=("Segoe UI",18),
            fill="#FFE8CC",anchor="center")

        # Divider line
        lw=320
        self.cv.create_line(cx-lw//2,int(H*0.33),cx+lw//2,int(H*0.33),
                            fill="#E8A040",width=2)

        # Welcome text
        self.cv.create_text(cx,int(H*0.40),
            text="Welcome to SACA",
            font=("Segoe UI",26,"bold"),
            fill="#FFF0D8",anchor="center")

        self.cv.create_text(cx,int(H*0.47),
            text="A health triage tool for the Yirrkala Community",
            font=("Segoe UI",13),
            fill="#FFCC99",anchor="center")

        self.cv.create_text(cx,int(H*0.52),
            text="Arnhem Land  ·  Northern Territory  ·  Australia",
            font=("Segoe UI",11),
            fill="#CC9966",anchor="center")

        # Info pills
        for i,(txt_) in enumerate([
            "✓  Available in English and Yolŋu Matha",
            "✓  Quick symptom check in under 2 minutes",
            "✓  Emergency alerts for serious conditions",
        ]):
            self.cv.create_text(cx,int(H*0.60)+i*28,text=txt_,
                font=("Segoe UI",12),fill="#FFE0B0",anchor="center")

        # Get Started button (drawn directly on canvas)
        bw=280; bh=58
        bx=cx-bw//2; by=int(H*0.75)
        # button background
        btn_img=pill(bw,bh,OCHRE)
        self._btn=ImageTk.PhotoImage(btn_img)
        btn_id=self.cv.create_image(bx,by,anchor="nw",image=self._btn)

        # hover version
        r,g,b=lerp(OCHRE,"#8B3A10",0.25)
        btn_h=pill(bw,bh,r2h(r,g,b))
        self._btnh=ImageTk.PhotoImage(btn_h)

        self.cv.create_text(cx,by+bh//2,
            text="GET STARTED  →",
            font=("Segoe UI",15,"bold"),
            fill="#FFFFFF",anchor="center",tags="btn_txt")

        # bind — use only canvas-scoped binds, never bind_all
        def click(e=None): self.app.go("S1_Lang")
        def enter(e): self.cv.itemconfig(btn_id,image=self._btnh)
        def leave(e): self.cv.itemconfig(btn_id,image=self._btn)
        for tag in ["btn_txt"]:
            self.cv.tag_bind(tag,"<Button-1>",click)
            self.cv.tag_bind(tag,"<Enter>",enter)
            self.cv.tag_bind(tag,"<Leave>",leave)
        self.cv.tag_bind(btn_id,"<Button-1>",click)
        # Invisible click overlay rectangle covers the whole button area
        overlay = self.cv.create_rectangle(bx,by,bx+bw,by+bh,
                                            fill="",outline="",tags="btn_overlay")
        self.cv.tag_bind("btn_overlay","<Button-1>",click)
        self.cv.tag_bind("btn_overlay","<Enter>",enter)
        self.cv.tag_bind("btn_overlay","<Leave>",leave)

        # footer
        self.cv.create_text(cx,H-22,
            text="COS70008  ·  Swinburne University of Technology  ·  Semester 1, 2026",
            font=("Segoe UI",9),fill="#AA7744",anchor="center")


# ══════════════════════════════════════════════════════════════════
