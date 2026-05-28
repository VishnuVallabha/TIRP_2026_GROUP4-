"""
SACA — S3_BodyPart: Body-region picker.
Click image OR side button → selects region → enables START QUESTIONS.
"""
import os
import tkinter as tk
from tkinter import Canvas, Frame, Label, StringVar, BooleanVar, IntVar
from PIL import Image, ImageDraw, ImageTk
from constants import *
from helpers  import mkcard, pill, h2r, r2h, lerp, _dir, draw_hd_icon
from widgets  import SF, NavBar, voice_bar, progress_timeline
from tts      import speak, speak_lang

# ── All clickable regions
ALL_REGIONS = [
    ("head",     "Head",        "Nuthu",        "🧠", SKY),
    ("throat",   "Throat",      "Dhawu",        "🗣", OCHRE),
    ("chest",    "Chest",       "Buku-djarrka", "❤",  TERRA),
    ("stomach",  "Stomach",     "Wana",         "🤢", GOLD),
    ("arms",     "Arms / Hands","Gurrku",       "💪", "#5B8DB8"),
    ("legs",     "Legs / Feet", "Warray",       "🦵", "#5B7A6B"),
    ("back",     "Back",        "Galk",         "🦴", "#795548"),
    ("fullbody", "Whole Body",  "Marr-yukurra", "🌡", GREEN),
]

# Region → (symptom name, colour, symptom key for S4)
REGION_TO_SYMPTOM = {
    "head":     ("Headache",     "#6D4C41", "headache"),
    "throat":   ("Sore Throat",  OCHRE,     "throat"),
    "chest":    ("Chest Pain",   TERRA,     "chest"),
    "stomach":  ("Stomach Pain", GOLD,      "stomach"),
    "arms":     ("Back Pain",    "#C19A6B", "back"),
    "legs":     ("Stomach Pain", GOLD,      "stomach"),
    "back":     ("Back Pain",    "#C19A6B", "back"),
    "fullbody": ("Fever",        TERRA,     "fever"),
}

# Native image size
IMG_W, IMG_H = 534, 1242

# Hit zones in native pixel space (from pixel scan)
# NOTE: "back" is intentionally NOT in hit zones (selected only via button)
HIT_ZONES = {
    "head":     (195,   0, 340,  130),
    "throat":   (215, 130, 320,  210),
    "chest":    (155, 210, 378,  490),
    "stomach":  (155, 490, 378,  730),
    "fullbody": ( 80,   0, 454, 1242),
}
ARM_ZONES = [(0, 210, 153, 720), (381, 210, 534, 720)]
LEG_ZONES = [(155, 730, 267, 1242), (267, 730, 378, 1242)]

HL_R, HL_G, HL_B = 27, 117, 188


class S3_BodyPart(Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=BG)
        self.app      = app
        self._refs    = {}
        self._sel_key = None

    def on_show(self):
        # Clear any global button binds leaked from S0_Cover
        try: self.unbind_all("<Button-1>")
        except: pass
        for w in self.winfo_children(): w.destroy()
        self._refs    = {}
        self._sel_key = None
        self._build()

    def _build(self):
        lang  = self.app.lang.get()
        is_yo = lang == "Yolngu Matha"

        NavBar(self,
               "WHERE DOES IT HURT?" if not is_yo else "NHUMA DHAWU BAYNU?",
               "Tap the body part to begin  |  Select, then we ask questions",
               back=lambda: self.app.go("S2_Method"), accent=SKY)

        progress_timeline(self, current_step=0)
        voice_bar(self,
                  "Where does it hurt? Tap the part of the body that is hurting.",
                  accent=SKY)

        hdr = Frame(self, bg=BG)
        hdr.pack(pady=(6, 2))
        Label(hdr,
              text="Where does it hurt?" if not is_yo else "Nhuma dhawu baynu?",
              font=("Segoe UI", 22, "bold"), fg=TXT1, bg=BG).pack()
        Label(hdr, text="Tap the body part or choose from the list",
              font=("Segoe UI", 11, "italic"), fg=TXT3, bg=BG).pack(pady=(2, 0))

        # ── Continue button MUST be packed FIRST (before expand=1 frame)
        # so tkinter reserves space for it at the bottom ──────────
        BW, BH = 380, 54
        bot = Frame(self, bg=BG)
        bot.pack(side="bottom", fill="x", pady=(6, 10))
        btn_frame = Frame(bot, bg=BG)
        btn_frame.pack(anchor="center")
        self._cont_cv = Canvas(btn_frame, width=BW, height=BH, bg=BG,
                               highlightthickness=0, bd=0)
        self._cont_cv.pack()
        self._refresh_continue(enabled=False)

        # 3-column layout (packed AFTER bottom button)
        outer = Frame(self, bg=BG)
        outer.pack(fill="both", expand=1, padx=10, pady=(4, 0))

        left_col = Frame(outer, bg=BG, width=185)
        left_col.pack(side="left", fill="y", anchor="n", pady=4)
        left_col.pack_propagate(False)

        skel_wrap = Frame(outer, bg=BG)
        skel_wrap.pack(side="left", fill="both", expand=1, padx=8)

        right_col = Frame(outer, bg=BG, width=185)
        right_col.pack(side="left", fill="y", anchor="n", pady=4)
        right_col.pack_propagate(False)

        left_keys  = ["head", "throat", "chest", "stomach"]
        right_keys = ["arms", "legs", "back", "fullbody"]

        for reg in ALL_REGIONS:
            if reg[0] in left_keys:
                self._region_btn(left_col, reg)
            elif reg[0] in right_keys:
                self._region_btn(right_col, reg)

        self._skel_cv = Canvas(skel_wrap, bg=BG, highlightthickness=0,
                               bd=0, width=300, height=520)
        self._skel_cv.pack(fill="both", expand=1)
        self._skel_cv.bind("<Configure>", lambda e: self._draw_body())
        self._skel_cv.bind("<Button-1>",  self._on_body_click)
        self._skel_cv.bind("<Motion>",    self._on_body_hover)

    # ── Side button ───────────────────────────────────────────────
    def _region_btn(self, parent, region_data):
        key, en, yo, icon, color = region_data
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
            # Icon badge
            ic = 36
            ix_, iy_ = 10, (BH_ - ic) // 2
            dr.rounded_rectangle([ix_, iy_, ix_+ic, iy_+ic], radius=9,
                                   fill=(rr, gg, bb, 230 if selected else 195))
            base = Image.new("RGBA", (BW_, BH_), (247, 248, 252, 0))
            return Image.alpha_composite(base, img)

        k = "rb_" + key
        self._refs[k+"_n"] = ImageTk.PhotoImage(_render(False))
        self._refs[k+"_s"] = ImageTk.PhotoImage(_render(True))

        bid = cv.create_image(0, 0, anchor="nw", image=self._refs[k+"_n"])
        # HD vector icon
        try:
            ic_pil = draw_hd_icon(key, size=ic, bg_col=color, fg_col="#FFFFFF")
            ic_ref = ImageTk.PhotoImage(ic_pil)
            self._refs[k+"_icon"] = ic_ref
            cv.create_image(10, (BH_-ic)//2, anchor="nw", image=ic_ref)
        except Exception:
            cv.create_text(10+17, BH_//2, text=icon,
                           font=("Segoe UI Emoji", 14), fill="#FFFFFF", anchor="center")
        cv.create_text(10+34+10, BH_//2-9, text=en,
                       font=("Segoe UI", 12, "bold"), fill=TXT1, anchor="w")
        cv.create_text(10+34+10, BH_//2+8, text=yo,
                       font=("Segoe UI", 9, "italic"), fill=TXT3, anchor="w")

        self._refs[k+"_cv"]  = cv
        self._refs[k+"_bid"] = bid

        cv.bind("<Button-1>",
                lambda e, k_=key, c_=color, n_=en: self._select(k_, c_, n_))

    # ── Central selection handler ─────────────────────────────────
    def _select(self, key, color, en):
        self._sel_key = key
        # Update all button states
        for reg in ALL_REGIONS:
            k    = "rb_" + reg[0]
            rcv  = self._refs.get(k+"_cv")
            rbid = self._refs.get(k+"_bid")
            if rcv and rbid:
                rcv.itemconfig(rbid,
                    image=self._refs[k+("_s" if reg[0]==key else "_n")])
        # Redraw body image with highlight
        self._draw_body(highlight=key)
        # Show the continue button
        self._refresh_continue(enabled=True, color=color)
        speak_lang(f"You selected {en}. Tap Start Questions to begin.")

    # ── Image transform ───────────────────────────────────────────
    def _img_transform(self, W, H):
        avail_h = H - 22
        ratio   = min(W / IMG_W, avail_h / IMG_H)
        iw      = int(IMG_W * ratio)
        ih      = int(IMG_H * ratio)
        ox      = (W - iw) // 2
        oy      = (avail_h - ih) // 2
        return ox, oy, ratio, iw, ih

    # ── Draw body image ───────────────────────────────────────────
    def _draw_body(self, highlight=None):
        cv = self._skel_cv
        W  = cv.winfo_width()  or 300
        H  = cv.winfo_height() or 520
        if W < 20 or H < 20:
            return
        cv.delete("all")
        img = self._render_body_pil(W, H, highlight)
        self._refs["body_img"] = ImageTk.PhotoImage(img)
        cv.create_image(0, 0, anchor="nw", image=self._refs["body_img"])
        if highlight:
            reg  = next((r for r in ALL_REGIONS if r[0]==highlight), None)
            name = reg[1] if reg else highlight
            cv.create_text(W//2, H-8,
                           text=f"✓  {name}  selected",
                           font=("Segoe UI", 10, "bold"),
                           fill=SKY, anchor="center")

    def _render_body_pil(self, W, H, highlight=None):
        img_path = os.path.join(_dir(), "human_body.png")
        try:
            human = Image.open(img_path).convert("RGBA")
        except Exception:
            human = Image.new("RGBA", (W, H), (210, 210, 210, 255))

        ox, oy, ratio, iw, ih = self._img_transform(W, H)
        human = human.resize((iw, ih), Image.LANCZOS)

        bg = Image.new("RGBA", (W, H), (247, 248, 252, 255))
        bg.paste(human, (ox, oy), human)

        if highlight:
            overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ov_dr   = ImageDraw.Draw(overlay)

            def draw_box(x1, y1, x2, y2, r=14):
                cx1 = ox + int(x1 * ratio)
                cy1 = oy + int(y1 * ratio)
                cx2 = ox + int(x2 * ratio)
                cy2 = oy + int(y2 * ratio)
                ov_dr.rounded_rectangle([cx1, cy1, cx2, cy2], radius=r,
                                         fill=(HL_R, HL_G, HL_B, 65),
                                         outline=(HL_R, HL_G, HL_B, 210), width=3)

            if highlight == "arms":
                for z in ARM_ZONES:
                    draw_box(*z, r=18)
            elif highlight == "legs":
                for z in LEG_ZONES:
                    draw_box(*z, r=14)
            elif highlight == "back":
                # Highlight spine/back area on torso
                draw_box(200, 210, 334, 730, r=14)
            elif highlight == "fullbody":
                draw_box(80, 0, 454, 1242, r=20)
            else:
                box = HIT_ZONES.get(highlight)
                if box:
                    draw_box(*box, r=16)

            bg = Image.alpha_composite(bg, overlay)

        return bg.convert("RGB")

    # ── Click/hover on body image ─────────────────────────────────
    def _canvas_to_image(self, px, py, W, H):
        ox, oy, ratio, iw, ih = self._img_transform(W, H)
        return (px - ox) / ratio, (py - oy) / ratio

    def _zone_for_point(self, ix, iy):
        if ix < 0 or ix > IMG_W or iy < 0 or iy > IMG_H:
            return None
        # HEAD
        if 0 <= iy <= 130 and 195 <= ix <= 340:
            return "head"
        # THROAT
        if 130 < iy <= 210 and 215 <= ix <= 320:
            return "throat"
        # ARMS (before torso check)
        for (x1, y1, x2, y2) in ARM_ZONES:
            if x1 <= ix <= x2 and y1 <= iy <= y2:
                return "arms"
        # CHEST
        if 210 < iy <= 490 and 155 <= ix <= 378:
            return "chest"
        # STOMACH
        if 490 < iy <= 730 and 155 <= ix <= 378:
            return "stomach"
        # LEGS
        for (x1, y1, x2, y2) in LEG_ZONES:
            if x1 <= ix <= x2 and y1 <= iy <= y2:
                return "legs"
        return None

    def _on_body_click(self, event):
        cv   = self._skel_cv
        W, H = cv.winfo_width(), cv.winfo_height()
        ix, iy = self._canvas_to_image(event.x, event.y, W, H)
        key = self._zone_for_point(ix, iy)
        if not key:
            return
        reg = next((r for r in ALL_REGIONS if r[0]==key), None)
        if reg:
            self._select(reg[0], reg[4], reg[1])

    def _on_body_hover(self, event):
        cv   = self._skel_cv
        W, H = cv.winfo_width(), cv.winfo_height()
        ix, iy = self._canvas_to_image(event.x, event.y, W, H)
        cv["cursor"] = "hand2" if self._zone_for_point(ix, iy) else "arrow"

    # ── Continue button ───────────────────────────────────────────
    def _refresh_continue(self, enabled=False, color=SKY):
        cv = self._cont_cv
        BW, BH = int(cv["width"]), int(cv["height"])
        cv.delete("all")

        if enabled:
            pil = pill(BW, BH, color, BH//2)
            self._refs["cont"] = ImageTk.PhotoImage(pil)
            cv.create_image(0, 0, anchor="nw", image=self._refs["cont"])
            cv.create_text(BW//2, BH//2,
                           text="START QUESTIONS  ->",
                           font=("Segoe UI", 14, "bold"),
                           fill="#FFFFFF", anchor="center")
            cv["cursor"] = "hand2"
            cv.bind("<Button-1>", lambda e: self._go_direct())
        else:
            # Grey disabled state — clearly visible
            pil = pill(BW, BH, "#C8D0DC", BH//2)
            self._refs["cont"] = ImageTk.PhotoImage(pil)
            cv.create_image(0, 0, anchor="nw", image=self._refs["cont"])
            cv.create_text(BW//2, BH//2,
                           text="Select a body part to continue",
                           font=("Segoe UI", 12),
                           fill="#6B7A8D", anchor="center")
            cv["cursor"] = "arrow"
            cv.unbind("<Button-1>")

    def _go_direct(self):
        key = self._sel_key
        if not key:
            return
        sym_name, sym_color, sym_key = REGION_TO_SYMPTOM.get(
            key, ("Fever", TERRA, "fever"))
        self.app.symptom            = sym_name
        self.app.sym_c              = sym_color
        self.app.sym_key            = sym_key
        self.app.input_method.set("photo")
        self.app.selected_body_part = key
        # Provide symptom filter list for S3_Symptom if user navigates there
        region_keys = {
            "head":     ["headache","fever","dizziness","throat"],
            "throat":   ["throat","cough","breathless","fever"],
            "chest":    ["chest","cough","breathless","fever"],
            "stomach":  ["stomach","vomiting","fever"],
            "back":     ["back","fatigue"],
            "arms":     ["back","fatigue"],
            "legs":     ["stomach","fatigue"],
            "fullbody": None,
        }
        self.app.body_part_symptoms = region_keys.get(key)
        self.app.go("S4_Questions")
