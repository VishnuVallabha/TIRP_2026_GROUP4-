"""SACA — S3_Symptom: Symptom identification via real human photos."""
import tkinter as tk
from tkinter import Canvas, Frame, Label, Entry, StringVar, BooleanVar, IntVar
from PIL import Image, ImageDraw, ImageTk, ImageFilter
from constants import *
from helpers  import mkcard, pill, h2r, r2h, lerp, _dir, draw_hd_icon
from widgets  import SF, NavBar, voice_bar, progress_timeline
from tts      import speak


class S3_Symptom(Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app   = app
        self._cards = {}
        self._built = False
        self._built_region = None

    def on_show(self):
        # Rebuild if body-part filter has changed since last build
        new_region = getattr(self.app, 'selected_body_part', None)
        if self._built and new_region == self._built_region:
            return
        self._built = True
        self._built_region = new_region
        for w in self.winfo_children(): w.destroy()
        self._build()

    def _build(self):
        lang  = self.app.lang.get()
        is_yo = lang == "Yolngu Matha"

        NavBar(self, "CHOOSE YOUR SYMPTOM" if not is_yo else "YIRRA DHÄRUK",
               "Tap the photo that matches what you feel" if not is_yo else "Tap yolŋu matha djäma",
               back=lambda: self.app.go("S3_BodyPart"), accent=OCHRE)

        progress_timeline(self, current_step=1)
        voice_bar(self,
                  "Look at the pictures. Tap the symptom that best matches what you are feeling.",
                  accent=OCHRE)

        # Body-part filter notice
        region_key  = getattr(self.app, "selected_body_part", None)
        region_syms = getattr(self.app, "body_part_symptoms", None)
        if region_key and region_key != "fullbody":
            region_name = next((r[1] for r in BODY_REGIONS if r[0]==region_key), region_key)
            info = Canvas(self, height=42, bg="#EEF6FF",
                          highlightthickness=0, bd=0)
            info.pack(fill="x")
            info.create_text(20, 21,
                text=f"📍  Showing symptoms for: {region_name}  ·  Tap 'Back' to see all",
                font=("Segoe UI", 11, "bold"), fill=SKY, anchor="w")
        else:
            info = Canvas(self, height=42, bg=BG_ALT,
                          highlightthickness=0, bd=0)
            info.pack(fill="x")
            info.create_text(20, 21,
                text="📷  Tap the photo that matches how you feel  ·  12 symptoms  ·  English / Yolŋu Matha",
                font=("Segoe UI", 10), fill=TXT3, anchor="w")

        outer = Frame(self, bg=BG)
        outer.pack(fill="both", expand=1, padx=14, pady=10)
        sf = SF(outer)
        sf.pack(fill="both", expand=1)

        # Top 6 most common symptoms shown by default (2 rows of 3)
        # If a body part filter is active, show filtered set (up to 6)
        TOP_6 = ["headache", "fever", "chest", "stomach", "throat", "back"]
        if region_syms:
            syms_to_show = [s for s in SYMPTOMS if s["key"] in region_syms][:6]
        else:
            # Show top 6 first, then remaining in order
            top    = [s for s in SYMPTOMS if s["key"] in TOP_6]
            others = [s for s in SYMPTOMS if s["key"] not in TOP_6]
            syms_to_show = (top + others)[:6]

        COLS = 3
        for i, sym in enumerate(syms_to_show):
            r, c = divmod(i, COLS)
            self._sym_card(sf.inner, sym, r, c)
            sf.inner.grid_columnconfigure(c, weight=1, uniform="sc")

        # "See all symptoms" link if showing filtered/top 6
        if len(syms_to_show) < len(SYMPTOMS):
            all_btn = Frame(sf.inner, bg=BG)
            all_btn.grid(row=COLS, column=0, columnspan=COLS, pady=(8,4))
            lbl_all = Label(all_btn,
                            text=f"▼  Show all {len(SYMPTOMS)} symptoms",
                            font=("Segoe UI", 11, "underline"),
                            fg=SKY, bg=BG, cursor="hand2")
            lbl_all.pack()
            def _show_all(sf_=sf):
                # Rebuild grid with all symptoms
                for w in sf_.inner.winfo_children(): w.destroy()
                for i2, sym2 in enumerate(SYMPTOMS):
                    r2, c2 = divmod(i2, COLS)
                    self._sym_card(sf_.inner, sym2, r2, c2)
                    sf_.inner.grid_columnconfigure(c2, weight=1, uniform="sc")
            lbl_all.bind("<Button-1>", lambda e: _show_all())

    def _sym_card(self, parent, sym, row, col):
        W_, H_ = 300, 390   # Taller card — more touch-friendly
        color   = sym["c"]
        k       = sym["code"]

        outer = Frame(parent, bg=BG)
        outer.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

        cv = Canvas(outer, width=W_, height=H_, bg=BG,
                    highlightthickness=0, bd=0, cursor="hand2")
        cv.pack(fill="both", expand=1)

        # ── Drop shadow ─────────────────────────────────────────
        sh = Image.new("RGBA",(W_+8,H_+8),(0,0,0,0))
        sh_dr = ImageDraw.Draw(sh)
        for i in range(8):
            a = int(30*(1-i/8))
            sh_dr.rounded_rectangle([i,i,W_+7-i,H_+7-i],
                                     radius=20, outline=(0,0,0,a), width=1)
        setattr(self, "_sh"+k, ImageTk.PhotoImage(sh))
        cv.create_image(-2,-2,anchor="nw",image=getattr(self,"_sh"+k))

        # ── Card base ───────────────────────────────────────────
        pn = mkcard(W_,H_,BORDER,BG_CARD,1,18)
        r2,g2,b2 = lerp(h2r(BG_CARD),h2r(color),0.06)
        ph = mkcard(W_,H_,color,r2h(r2,g2,b2),3,18)
        setattr(self,"_n"+k,ImageTk.PhotoImage(pn))
        setattr(self,"_h"+k,ImageTk.PhotoImage(ph))
        bid = cv.create_image(0,0,anchor="nw",image=getattr(self,"_n"+k))

        # ── HD icon area (top 55% of card) ─────────────────────
        photo_h = int(H_*0.55)
        # Coloured gradient background for icon area
        icon_bg = Image.new("RGBA", (W_, photo_h), (0,0,0,0))
        ibg_dr  = ImageDraw.Draw(icon_bg)
        rr_c,gg_c,bb_c = h2r(color)
        for gy in range(photo_h):
            t   = gy / photo_h
            alpha = int(30 + 60*t)
            ibg_dr.line([(0,gy),(W_,gy)], fill=(rr_c,gg_c,bb_c,alpha))
        # Rounded top mask
        mask_i = Image.new("L",(W_,photo_h),0)
        ImageDraw.Draw(mask_i).rounded_rectangle([0,0,W_-1,photo_h+18],radius=18,fill=255)
        icon_bg.putalpha(mask_i)
        bg_base = Image.new("RGBA",(W_,photo_h),(250,250,255,255))
        bg_base = Image.alpha_composite(bg_base, icon_bg)
        icon_bg_ref = ImageTk.PhotoImage(bg_base.convert("RGB"))
        setattr(self,"_ibg"+k, icon_bg_ref)
        cv.create_image(0,0,anchor="nw",image=icon_bg_ref)
        # Large centred HD icon
        ic_size = min(photo_h-20, W_-20, 110)
        ic_pil  = draw_hd_icon(sym["key"], size=ic_size, bg_col=None, fg_col=color)
        ic_ref  = ImageTk.PhotoImage(ic_pil)
        setattr(self,"_ic"+k, ic_ref)
        cv.create_image(W_//2-ic_size//2, (photo_h-ic_size)//2,
                        anchor="nw", image=ic_ref)

        # ── Symptom code pill on photo ──────────────────────────
        code_pil = pill(48,22,color,radius=11)
        code_ref = ImageTk.PhotoImage(code_pil)
        setattr(self,"_cd"+k,code_ref)
        cv.create_image(10,10,anchor="nw",image=code_ref)
        cv.create_text(34,21,text=sym["code"],
                       font=("Segoe UI",8,"bold"),fill="#FFFFFF",anchor="center")

        # ── Category icon ───────────────────────────────────────
        icons = {"S01":"🌡","S02":"🧠","S03":"❤","S04":"😷",
                 "S05":"🫃","S06":"💨","S07":"😵","S08":"😴",
                 "S09":"🤢","S10":"🔴","S11":"🦴","S12":"🗣"}
        ic_txt = icons.get(sym["code"],"•")
        cv.create_text(W_-18,18,text=ic_txt,
                       font=("Segoe UI Emoji",14),anchor="e")

        # ── English name ────────────────────────────────────────
        cv.create_text(W_//2, photo_h+26,
                       text=sym["en"],
                       font=("Segoe UI",17,"bold"),
                       fill=TXT1,anchor="center")
        # ── Yolngu ─────────────────────────────────────────────
        cv.create_text(W_//2, photo_h+50,
                       text=sym["yo"],
                       font=("Segoe UI",12,"italic"),
                       fill=TXT3,anchor="center")

        # ── SELECT button ───────────────────────────────────────
        btn_w = W_-24; btn_h = 52   # Tall button — easy to tap
        btn_y = H_-btn_h-14
        btn_pil = pill(btn_w,btn_h,color,radius=19)
        # Add white "→" to pill
        bp_dr = ImageDraw.Draw(btn_pil)
        btn_ref = ImageTk.PhotoImage(btn_pil)
        setattr(self,"_btn"+k,btn_ref)
        cv.create_image(12,btn_y,anchor="nw",image=btn_ref,tags="selbtn"+k)
        cv.create_text(W_//2,btn_y+btn_h//2,
                       text="SELECT THIS SYMPTOM  →",
                       font=("Segoe UI",9,"bold"),
                       fill="#FFFFFF",anchor="center",tags="tap"+k)

        self._cards[k] = {"cv":cv,"bid":bid,"color":color}

        def click(s=sym):
            self.app.symptom = s["en"]
            self.app.sym_c   = s["c"]
            self.app.sym_key = s["key"]
            self.app.input_method.set("photo")
            if not self.app.selected_body_part:
                self.app.selected_body_part = "fullbody"
            self.app.go("S4_Questions")

        cv.bind("<Button-1>",lambda e:click())
        cv.bind("<Enter>",
            lambda e,k_=k,co=color:(
                cv.itemconfig(bid,image=getattr(self,"_h"+k_)),
                cv.itemconfig("tap"+k_,fill="#FFFFFF")))
        cv.bind("<Leave>",
            lambda e,k_=k:(
                cv.itemconfig(bid,image=getattr(self,"_n"+k_)),
                cv.itemconfig("tap"+k_,fill="#FFFFFF")))

# ══════════════════════════════════════════════════════════════════
# S4 — QUESTIONS (more options added)
# ══════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════
# S4_Questions — FULL PICTURE-BASED VISUAL QUESTIONS
# Every question = image cards on blurred symptom background
# ══════════════════════════════════════════════════════════════════
