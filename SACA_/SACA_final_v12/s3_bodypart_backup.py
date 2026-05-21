"""
SACA — S3_BodyPart: Body-region picker.
Selecting a region auto-sets the symptom and routes DIRECTLY to S4_Questions.
"""
import os
import tkinter as tk
from tkinter import Canvas, Frame, Label, Entry, StringVar, BooleanVar, IntVar
from PIL import Image, ImageDraw, ImageTk, ImageFilter
from constants import *
from helpers  import mkcard, pill, h2r, r2h, lerp, _dir
from widgets  import SF, NavBar, voice_bar, progress_timeline
from tts      import speak

# Maps region key → (symptom name, symptom colour, symptom key)
REGION_TO_SYMPTOM = {
    "head":     ("Headache",        "#6D4C41",  "headache"),
    "chest":    ("Chest Pain",      TERRA,      "chest"),
    "stomach":  ("Stomach Pain",    GOLD,       "stomach"),
    "back":     ("Back Pain",       "#C19A6B",  "back"),
    "throat":   ("Sore Throat",     OCHRE,      "throat"),
    "fullbody": ("Fever",           TERRA,      "fever"),
}


class S3_BodyPart(Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app      = app
        self._refs    = {}
        self._sel_key = None

    def on_show(self):
        for w in self.winfo_children(): w.destroy()
        self._refs    = {}
        self._sel_key = None
        self._build()

    def _build(self):
        lang  = self.app.lang.get()
        is_yo = lang == "Yolngu Matha"

        NavBar(self,
               "WHERE DOES IT HURT?" if not is_yo else "NHUMA DHÄWU BÄYŊU?",
               "Tap the body part to begin  ·  Select, then we ask questions",
               back=lambda: self.app.go("S2_Method"), accent=SKY)

        progress_timeline(self, current_step=0)
        voice_bar(self,
                  "Where does it hurt? Tap the part of the body that is hurting.",
                  accent=SKY)

        hdr = Frame(self, bg=BG)
        hdr.pack(pady=(10, 4))
        Label(hdr,
              text="Where does it hurt?" if not is_yo else "Nhuma dhäwu bäyŋu?",
              font=("Segoe UI", 26, "bold"), fg=TXT1, bg=BG).pack()
        Label(hdr, text="Tap the body part  ·  Yirra nhuma bäy",
              font=("Segoe UI", 12, "italic"), fg=TXT3, bg=BG).pack(pady=(2, 0))

        # ── 3-column layout: buttons | skeleton | buttons ─────────
        outer = Frame(self, bg=BG)
        outer.pack(fill="both", expand=1, padx=20, pady=6)

        left_col   = Frame(outer, bg=BG, width=200)
        left_col.pack(side="left", fill="y", anchor="n", pady=4)
        left_col.pack_propagate(False)

        skel_wrap  = Frame(outer, bg=BG)
        skel_wrap.pack(side="left", fill="both", expand=1, padx=14)

        right_col  = Frame(outer, bg=BG, width=200)
        right_col.pack(side="left", fill="y", anchor="n", pady=4)
        right_col.pack_propagate(False)

        left_regions  = [r for r in BODY_REGIONS if r[0] in ("head","chest","stomach")]
        right_regions = [r for r in BODY_REGIONS if r[0] in ("back","throat","fullbody")]

        for reg in left_regions:
            self._region_btn(left_col, reg, side="left")
        for reg in right_regions:
            self._region_btn(right_col, reg, side="right")

        # Skeleton canvas (centered)
        self._skel_cv = Canvas(skel_wrap, bg=BG, highlightthickness=0, bd=0, width=320, height=600)
        self._skel_cv.pack(fill="both", expand=1)
        self._skel_cv.bind("<Configure>", lambda e: self._draw_skeleton())

        # Continue button
        bot = Frame(self, bg=BG)
        bot.pack(side="bottom", pady=12)
        BW, BH = 400, 64
        self._cont_cv = Canvas(bot, width=BW, height=BH, bg=BG,
                               highlightthickness=0, bd=0)
        self._cont_cv.pack()
        self._refresh_continue(enabled=False)

    # ── Region button ─────────────────────────────────────────────
    def _region_btn(self, parent, region_data, side="left"):
        key, en, yo, icon, color = region_data
        BW_, BH_ = 218, 100

        cv = Canvas(parent, width=BW_, height=BH_, bg=BG,
                    highlightthickness=0, bd=0, cursor="hand2")
        cv.pack(pady=6, padx=4)

        def _mk(glow=0, sel=False):
            card = mkcard(BW_, BH_, color,
                          r2h(*lerp(h2r(BG_CARD), h2r(color), 0.08 + glow*0.10)),
                          2+glow, 20)
            if sel:
                dr2 = ImageDraw.Draw(card)
                rr, gg, bb = h2r(color)
                for gi in range(5):
                    dr2.rounded_rectangle([gi, gi, BW_-1-gi, BH_-1-gi],
                                           radius=20-gi,
                                           outline=(rr, gg, bb, 95-gi*18), width=1)
            return card

        k = "rb_" + key
        self._refs[k+"_n"] = ImageTk.PhotoImage(_mk(0))
        self._refs[k+"_h"] = ImageTk.PhotoImage(_mk(1))
        self._refs[k+"_s"] = ImageTk.PhotoImage(_mk(2, True))
        bid = cv.create_image(0, 0, anchor="nw", image=self._refs[k+"_n"])

        # Coloured icon badge
        ic_sz = 54
        ic_pil = Image.new("RGBA", (ic_sz, ic_sz), (0,0,0,0))
        ic_dr  = ImageDraw.Draw(ic_pil)
        rr, gg, bb = h2r(color)
        ic_dr.rounded_rectangle([0,0,ic_sz-1,ic_sz-1], radius=14,
                                  fill=(rr,gg,bb,230))
        self._refs[k+"_ic"] = ImageTk.PhotoImage(ic_pil)
        cv.create_image(14, BH_//2-ic_sz//2, anchor="nw",
                        image=self._refs[k+"_ic"])
        cv.create_text(14+ic_sz//2, BH_//2, text=icon,
                       font=("Segoe UI Emoji", 22), fill="#FFFFFF", anchor="center")

        tx = 14 + ic_sz + 10
        cv.create_text(tx, BH_//2-15, text=en,
                       font=("Segoe UI", 15, "bold"), fill=TXT1, anchor="w")
        cv.create_text(tx, BH_//2+9, text=yo,
                       font=("Segoe UI", 10, "italic"), fill=TXT3, anchor="w")
        arrow_x = BW_-14
        cv.create_text(arrow_x, BH_//2, text="→",
                       font=("Segoe UI", 18, "bold"), fill=color, anchor="e")

        self._refs[k+"_cv"]  = cv
        self._refs[k+"_bid"] = bid

        def on_click(k_=k, key_=key, color_=color, en_=en):
            self._sel_key = key_
            # Update button visuals
            for reg in BODY_REGIONS:
                rk = "rb_" + reg[0]
                rcv  = self._refs.get(rk+"_cv")
                rbid = self._refs.get(rk+"_bid")
                if rcv and rbid:
                    rcv.itemconfig(rbid,
                        image=self._refs[rk+("_s" if reg[0]==key_ else "_n")])
            self._draw_skeleton(highlight=key_)
            self._refresh_continue(enabled=True, color=color_)
            speak(f"You selected {en_}. Tap Start Questions to begin.")

        cv.bind("<Button-1>", lambda e: on_click())
        cv.bind("<Enter>", lambda e, k_=k, key_=key: (
            cv.itemconfig(self._refs[k_+"_bid"], image=self._refs[k_+"_h"])
            if self._sel_key != key_ else None))
        cv.bind("<Leave>", lambda e, k_=k, key_=key: (
            cv.itemconfig(self._refs[k_+"_bid"],
                image=self._refs[k_+"_s" if self._sel_key==key_ else k_+"_n"])))

    # ── Human skeleton illustration ───────────────────────────────
    def _draw_skeleton(self, highlight=None):
        cv = self._skel_cv
        W  = cv.winfo_width() or 400
        H  = cv.winfo_height() or 650
        if W < 10 or H < 10: return
        cv.delete("all")

        img = self._render_skeleton_pil(W, H, highlight)
        self._refs["skel"] = ImageTk.PhotoImage(img)
        cv.create_image(0, 0, anchor="nw", image=self._refs["skel"])

        if highlight:
            name = next((r[1] for r in BODY_REGIONS if r[0]==highlight), highlight)
            cv.create_text(W//2, H-16,
                           text=f"✓  {name}  selected",
                           font=("Segoe UI", 11, "bold"),
                           fill=SKY, anchor="center")

        cv.bind("<Button-1>", self._on_body_click)
        cv.bind("<Motion>",   self._on_body_hover)

    def _img_transform(self, W, H):
        """Return (ox, oy, scale) — where image is placed and its scale vs native 534x1242."""
        img_path = os.path.join(_dir(), "human_body.png")
        try:
            native_w, native_h = Image.open(img_path).size
        except Exception:
            native_w, native_h = 534, 1242
        avail_h = H - 30
        ratio   = min(W / native_w, avail_h / native_h)
        iw      = int(native_w * ratio)
        ih      = int(native_h * ratio)
        ox      = (W - iw) // 2
        oy      = (avail_h - ih) // 2
        return ox, oy, ratio, iw, ih

    def _hit_zone(self, px, py, W, H):
        """
        Map a canvas click to a body region using pixel-accurate zones.
        All coordinates are derived from the actual 534x1242 image outline scan.
        Priority: head > throat > left_arm > right_arm > chest > stomach > legs
        """
        ox, oy, r, iw, ih = self._img_transform(W, H)

        # Convert canvas click → image coordinates (native 534x1242 space)
        ix = (px - ox) / r
        iy = (py - oy) / r

        # Out of image bounds
        if ix < 0 or ix > 534 or iy < 0 or iy > 1242:
            return None

        # ── Zones defined in native 534x1242 image pixels ──────────
        # HEAD: y=0-130, x=207-327 (from pixel scan)
        if 0 <= iy <= 130 and 195 <= ix <= 340:
            return "head"

        # THROAT/NECK: y=130-205, x=215-320
        if 130 < iy <= 210 and 215 <= ix <= 320:
            return "throat"

        # LEFT ARM: x=0-155, y=210-710
        if 210 < iy <= 710 and 0 <= ix <= 155:
            return "back"   # map arm → back pain (closest symptom)

        # RIGHT ARM: x=378-534, y=210-710
        if 210 < iy <= 710 and 378 <= ix <= 534:
            return "back"   # map arm → back pain

        # CHEST (torso core): y=205-490, x=155-378
        if 210 < iy <= 490 and 155 <= ix <= 378:
            return "chest"

        # STOMACH (lower torso): y=490-730, x=155-378
        if 490 < iy <= 730 and 155 <= ix <= 378:
            return "stomach"

        # LEFT LEG: y=730-1242, x=155-268
        if 730 < iy <= 1242 and 155 <= ix <= 268:
            return "stomach"  # map leg → stomach/lower body

        # RIGHT LEG: y=730-1242, x=268-378
        if 730 < iy <= 1242 and 268 <= ix <= 378:
            return "stomach"

        return None

    def _on_body_click(self, event):
        cv  = self._skel_cv
        W, H = cv.winfo_width(), cv.winfo_height()
        key  = self._hit_zone(event.x, event.y, W, H)
        if not key:
            return
        reg = next((r for r in BODY_REGIONS if r[0] == key), None)
        if not reg:
            return
        rkey, en, yo, icon, color = reg
        self._sel_key = rkey
        for r2 in BODY_REGIONS:
            rk   = "rb_" + r2[0]
            rcv  = self._refs.get(rk + "_cv")
            rbid = self._refs.get(rk + "_bid")
            if rcv and rbid:
                rcv.itemconfig(rbid,
                    image=self._refs[rk + ("_s" if r2[0] == rkey else "_n")])
        self._draw_skeleton(highlight=rkey)
        self._refresh_continue(enabled=True, color=color)
        speak(f"You selected {en}. Tap Start Questions to begin.")

    def _on_body_hover(self, event):
        cv   = self._skel_cv
        W, H = cv.winfo_width(), cv.winfo_height()
        key  = self._hit_zone(event.x, event.y, W, H)
        cv["cursor"] = "hand2" if key else "arrow"

    def _render_skeleton_pil(self, W, H, highlight=None):
        """Render human body image with pixel-accurate highlight zones."""
        ZONE_B = (27, 117, 188)

        img_path = os.path.join(_dir(), "human_body.png")
        try:
            human = Image.open(img_path).convert("RGBA")
        except Exception:
            human = Image.new("RGBA", (W, H), (220, 220, 220, 255))

        ox, oy, ratio, iw, ih = self._img_transform(W, H)
        human = human.resize((iw, ih), Image.LANCZOS)

        bg = Image.new("RGBA", (W, H), (247, 248, 252, 255))
        bg.paste(human, (ox, oy), human)

        if highlight:
            # Highlight zones in native 534x1242 coords → scale to canvas
            def sc(v): return int(v * ratio)
            cx_img = ox + iw // 2   # canvas centre x

            # Zone boxes: (x1,y1,x2,y2) in canvas coords
            # Derived from actual pixel scan of human_body.png
            zone_boxes = {
                "head":     (cx_img-sc(73),  oy+sc(0),   cx_img+sc(73),  oy+sc(130)),
                "throat":   (cx_img-sc(53),  oy+sc(130), cx_img+sc(53),  oy+sc(210)),
                "chest":    (cx_img-sc(112), oy+sc(210), cx_img+sc(112), oy+sc(490)),
                "stomach":  (cx_img-sc(100), oy+sc(490), cx_img+sc(100), oy+sc(730)),
                "back":     (ox+sc(0),       oy+sc(210), ox+sc(155),     oy+sc(710)),  # left arm
                "fullbody": (ox+sc(0),       oy+sc(0),   ox+sc(534),     oy+sc(1242)),
            }

            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ov_dr   = ImageDraw.Draw(overlay)
            rr, gg, bb = ZONE_B

            if highlight == "back":
                # Highlight BOTH arms
                left_arm  = (ox+sc(0),   oy+sc(210), ox+sc(155),  oy+sc(710))
                right_arm = (ox+sc(378),  oy+sc(210), ox+sc(534), oy+sc(710))
                for arm_box in (left_arm, right_arm):
                    ov_dr.rounded_rectangle(list(arm_box), radius=14,
                                             fill=(rr, gg, bb, 70),
                                             outline=(rr, gg, bb, 200), width=3)
            else:
                box = zone_boxes.get(highlight)
                if box:
                    ov_dr.rounded_rectangle(list(box), radius=16,
                                             fill=(rr, gg, bb, 70),
                                             outline=(rr, gg, bb, 200), width=3)
            bg = Image.alpha_composite(bg, overlay)

        return bg.convert("RGB")

    # ── Continue button ───────────────────────────────────────────
    def _refresh_continue(self, enabled=False, color=SKY):
        cv = self._cont_cv
        BW, BH = int(cv["width"]), int(cv["height"])
        cv.delete("all")
        col = color if enabled else BORDER2
        pil = pill(BW, BH, col, BH//2)
        self._refs["cont"] = ImageTk.PhotoImage(pil)
        cv.create_image(0, 0, anchor="nw", image=self._refs["cont"])
        txt = "START QUESTIONS  →" if enabled else "Please select a body part first"
        cv.create_text(BW//2, BH//2, text=txt,
                       font=("Segoe UI", 15, "bold"),
                       fill="#FFFFFF" if enabled else TXT4, anchor="center")
        if enabled:
            cv["cursor"] = "hand2"
            cv.bind("<Button-1>", lambda e: self._go_direct())
        else:
            cv["cursor"] = "arrow"
            cv.unbind("<Button-1>")

    def _go_direct(self):
        """Set symptom from body part and go DIRECTLY to questions."""
        key = self._sel_key
        if not key:
            return
        sym_name, sym_color, sym_key = REGION_TO_SYMPTOM.get(
            key, ("Fever", TERRA, "fever"))
        self.app.symptom          = sym_name
        self.app.sym_c            = sym_color
        self.app.sym_key          = sym_key
        self.app.input_method.set("photo")
        self.app.selected_body_part = key
        self.app.go("S4_Questions")
