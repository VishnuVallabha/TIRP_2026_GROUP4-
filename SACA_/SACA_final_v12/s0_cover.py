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

        # ── Background: full-screen Aboriginal art ──────────────────
        art=load_cover(W,H)

        # Multi-layer overlay: subtle at top, strong gradient at bottom half
        ov=Image.new("RGBA",(W,H),(0,0,0,0))
        dv=ImageDraw.Draw(ov)

        # Top section – light vignette only
        for y in range(int(H*0.45)):
            t=y/(H*0.45)
            a=int(20+60*t*t)
            dv.line([(0,y),(W,y)],fill=(0,0,0,a))

        # Bottom panel – deep dark band for legibility
        panel_top=int(H*0.45)
        for y in range(panel_top,H):
            t=(y-panel_top)/(H-panel_top)
            a=int(80+160*t)          # 80→240 fade
            dv.line([(0,y),(W,y)],fill=(0,0,0,a))

        art=Image.alpha_composite(art.convert("RGBA"),ov).convert("RGB")
        self._bg=ImageTk.PhotoImage(art)
        self.cv.create_image(0,0,anchor="nw",image=self._bg)

        cx=W//2

        # ── LOGO AREA (upper-centre) ────────────────────────────────
        logo_y=int(H*0.16)

        # Circle badge behind the cross icon
        badge_r=38
        badge=Image.new("RGBA",(badge_r*2,badge_r*2),(0,0,0,0))
        bd=ImageDraw.Draw(badge)
        bd.ellipse([0,0,badge_r*2-1,badge_r*2-1],fill=(255,107,53,210))
        self._badge=ImageTk.PhotoImage(badge)
        self.cv.create_image(cx,logo_y,anchor="center",image=self._badge)

        self.cv.create_text(cx,logo_y,
            text="✚",
            font=("Segoe UI",26,"bold"),
            fill="#FFFFFF",anchor="center")

        # App name
        self.cv.create_text(cx,logo_y+54,
            text="SACA",
            font=("Segoe UI",52,"bold"),
            fill="#FFFFFF",anchor="center")

        # Tagline
        self.cv.create_text(cx,logo_y+102,
            text="Swin Smart Adaptive Clinical Assistant",
            font=("Segoe UI",14),
            fill="#FFD8AA",anchor="center")

        # ── Thin accent divider ─────────────────────────────────────
        div_y=logo_y+128
        hw=180
        self.cv.create_line(cx-hw,div_y,cx-14,div_y,fill="#FF6B35",width=1)
        self.cv.create_oval(cx-6,div_y-4,cx+6,div_y+4,fill="#FF6B35",outline="")
        self.cv.create_line(cx+14,div_y,cx+hw,div_y,fill="#FF6B35",width=1)

        # ── Card panel (frosted feel via semi-transparent rect) ─────
        card_w=min(W-80,520)
        card_x=cx-card_w//2
        card_y=int(H*0.50)
        card_h=int(H*0.36)
        card_pad=28

        # Rounded-rectangle card with alpha
        card_img=Image.new("RGBA",(card_w,card_h),(0,0,0,0))
        cd=ImageDraw.Draw(card_img)
        r=16
        cd.rounded_rectangle([0,0,card_w-1,card_h-1],radius=r,
                              fill=(255,255,255,28),outline=(255,255,255,60),width=1)
        self._card=ImageTk.PhotoImage(card_img)
        self.cv.create_image(card_x,card_y,anchor="nw",image=self._card)

        # Welcome heading inside card
        self.cv.create_text(cx,card_y+card_pad,
            text="Welcome",
            font=("Segoe UI",22,"bold"),
            fill="#FFFFFF",anchor="center")

        self.cv.create_text(cx,card_y+card_pad+30,
            text="Health triage for the Yirrkala Community",
            font=("Segoe UI",12),
            fill="#FFD4A0",anchor="center")

        # Feature rows
        features=[
            ("🌐","English  &  Yolŋu Matha"),
            ("⚡","Symptom check in under 2 minutes"),
            ("🚨","Emergency alerts for serious conditions"),
        ]
        fy=card_y+card_pad+68
        for icon,txt in features:
            # icon circle
            ic_img=Image.new("RGBA",(28,28),(0,0,0,0))
            icd=ImageDraw.Draw(ic_img)
            icd.ellipse([0,0,27,27],fill=(255,107,53,180))
            self._ic=ImageTk.PhotoImage(ic_img)      # note: last ref kept below
            self.cv.create_image(card_x+card_pad,fy,anchor="w",image=self._ic)
            self.cv.create_text(card_x+card_pad+16,fy,
                text=icon,font=("Segoe UI",11),fill="#FFFFFF",anchor="center")
            self.cv.create_text(card_x+card_pad+36,fy,
                text=txt,font=("Segoe UI",12),fill="#FFE8CC",anchor="w")
            fy+=34

        # Keep icon image references alive
        self._icons=[]
        fy2=card_y+card_pad+68
        for icon,txt in features:
            ic_img=Image.new("RGBA",(28,28),(0,0,0,0))
            icd=ImageDraw.Draw(ic_img)
            icd.ellipse([0,0,27,27],fill=(255,107,53,180))
            ref=ImageTk.PhotoImage(ic_img)
            self._icons.append(ref)
            self.cv.create_image(card_x+card_pad,fy2,anchor="w",image=ref)
            self.cv.create_text(card_x+card_pad+16,fy2,
                text=icon,font=("Segoe UI",11),fill="#FFFFFF",anchor="center")
            self.cv.create_text(card_x+card_pad+36,fy2,
                text=txt,font=("Segoe UI",12),fill="#FFE8CC",anchor="w")
            fy2+=34

        # ── GET STARTED button ──────────────────────────────────────
        bw=min(card_w-60,320); bh=52
        bx=cx-bw//2; by=int(H*0.875)

        btn_img=pill(bw,bh,OCHRE)
        self._btn=ImageTk.PhotoImage(btn_img)
        r2,g2,b2=lerp(OCHRE,"#8B3A10",0.22)
        btn_h=pill(bw,bh,r2h(r2,g2,b2))
        self._btnh=ImageTk.PhotoImage(btn_h)

        btn_id=self.cv.create_image(bx,by,anchor="nw",image=self._btn)
        self.cv.create_text(cx,by+bh//2,
            text="GET STARTED  →",
            font=("Segoe UI",14,"bold"),
            fill="#FFFFFF",anchor="center",tags="btn_txt")

        # button interaction
        def click(e=None): self.app.go("S1_Lang")
        def enter(e): self.cv.itemconfig(btn_id,image=self._btnh)
        def leave(e): self.cv.itemconfig(btn_id,image=self._btn)

        self.cv.tag_bind("btn_txt","<Button-1>",click)
        self.cv.tag_bind("btn_txt","<Enter>",enter)
        self.cv.tag_bind("btn_txt","<Leave>",leave)
        self.cv.tag_bind(btn_id,"<Button-1>",click)

        overlay=self.cv.create_rectangle(bx,by,bx+bw,by+bh,
                                          fill="",outline="",tags="btn_overlay")
        self.cv.tag_bind("btn_overlay","<Button-1>",click)
        self.cv.tag_bind("btn_overlay","<Enter>",enter)
        self.cv.tag_bind("btn_overlay","<Leave>",leave)

        # ── Footer ──────────────────────────────────────────────────
        self.cv.create_text(cx,H-16,
            text="COS70008  ·  Swinburne University of Technology  ·  Semester 1, 2026",
            font=("Segoe UI",8),fill="#997755",anchor="center")


# ══════════════════════════════════════════════════════════════════
