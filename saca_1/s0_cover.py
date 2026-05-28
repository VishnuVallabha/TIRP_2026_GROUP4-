"""SACA — S0: Full-screen Aboriginal cover / splash screen.
   Premium cinematic redesign — Yirrkala Community Edition.
"""
import tkinter as tk
from tkinter import Canvas, Frame, Label, Entry, StringVar, BooleanVar, IntVar
from PIL import Image, ImageDraw, ImageTk, ImageFilter
from constants import *
from helpers  import mkcard, pill, h2r, r2h, lerp, load_cover, _dir
from widgets  import SF, NavBar, voice_bar, progress_timeline
from tts      import speak

# ── Design tokens ────────────────────────────────────────────────
_NAVY      = "#0A0E1A"
_ORANGE    = "#FF6B35"
_CREAM     = "#F2C07A"
_TEAL      = "#5BC8A0"
_WHITE     = "#FFFFFF"
_MUTED     = "#7A6650"
_CARD_BG   = (10, 18, 35, 210)   # RGBA – deep navy card
_CARD_BDR  = (255, 107, 53, 180) # RGBA – orange border

# ── Fixed layout constants (pixel-stable) ────────────────────────
_TOP_BAR_H   = 4       # thin accent stripe at very top
_LOGO_Y      = 95      # centre of badge circle
_BADGE_R     = 44      # radius of glow circle  (bottom edge = _LOGO_Y + 44 = 139)
_SACA_Y      = 210     # "SACA" title  — 71 px below badge bottom for clear air
_SUB_Y       = 252     # subtitle      — 42 px below SACA (48pt font ≈ ~58px tall)
_TAGLINE_Y   = 278     # italic tagline — 26 px below subtitle
_DIV_Y       = 304     # decorative divider — 26 px below tagline
_CARD_Y      = 326     # top of feature card
_CARD_H      = 172     # fixed card height
_CARD_PAD_X  = 28      # horizontal padding inside card
_CARD_PAD_Y  = 18      # vertical padding inside card
_BTN_Y       = 518     # top of button row
_BTN_H       = 46      # button height
_BTN_GAP     = 12      # gap between buttons (unused — single button)
_FOOTER_B    = 22      # px from bottom for footer text


class S0_Cover(Frame):
    def __init__(self, parent, app):
        super().__init__(parent, bg=_NAVY)
        self.app = app
        self._refs = []          # keeps all ImageTk.PhotoImage alive

        self.cv = Canvas(self, bg=_NAVY, highlightthickness=0, bd=0)
        self.cv.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.cv.bind("<Configure>", self._draw)

    # ─────────────────────────────────────────────────────────────
    def _draw(self, e=None):
        W = self.cv.winfo_width()
        H = self.cv.winfo_height()
        if W < 10 or H < 10:
            return
        self.cv.delete("all")
        self._refs.clear()

        cx = W // 2

        # ── 1. Background landscape ──────────────────────────────
        art = load_cover(W, H)

        # Fast numpy vignette — same visual result, no pixel loops
        import numpy as np
        arr = np.array(art.convert("RGBA"), dtype=np.float32)
        mask = np.zeros((H, W), dtype=np.float32)
        mid  = H // 2
        # Top half: alpha 110→170 (same as original loop)
        t_top  = np.linspace(0, 1, mid, dtype=np.float32)
        mask[:mid, :] = ((110 + 60 * t_top * t_top) / 255.0)[:, None]
        # Bottom half: alpha 170→240
        t_bot  = np.linspace(0, 1, H - mid, dtype=np.float32)
        mask[mid:, :] = ((170 + 70 * t_bot) / 255.0)[:, None]
        dark = np.array([8, 12, 24], dtype=np.float32)
        for c in range(3):
            arr[:, :, c] = arr[:, :, c] * (1 - mask) + dark[c] * mask
        art = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGB")
        _bg = ImageTk.PhotoImage(art)
        self._refs.append(_bg)
        self.cv.create_image(0, 0, anchor="nw", image=_bg)

        # ── 2. Top accent bar ────────────────────────────────────
        self.cv.create_rectangle(
            0, 0, W, _TOP_BAR_H,
            fill=_ORANGE, outline=""
        )

        # ── 3. Logo – glowing badge + cross ─────────────────────
        # Outer soft glow (blurred circle)
        glow_d = (_BADGE_R + 22) * 2
        glow_img = Image.new("RGBA", (glow_d, glow_d), (0, 0, 0, 0))
        gi = ImageDraw.Draw(glow_img)
        for shrink, alpha in [(0, 28), (4, 40), (8, 55), (12, 35)]:
            gi.ellipse(
                [shrink, shrink, glow_d - 1 - shrink, glow_d - 1 - shrink],
                fill=(255, 107, 53, alpha)
            )
        glow_img = glow_img.filter(ImageFilter.GaussianBlur(radius=10))
        _glow = ImageTk.PhotoImage(glow_img)
        self._refs.append(_glow)
        self.cv.create_image(cx, _LOGO_Y, anchor="center", image=_glow)

        # Main badge circle
        bd_d = _BADGE_R * 2
        badge = Image.new("RGBA", (bd_d, bd_d), (0, 0, 0, 0))
        bd = ImageDraw.Draw(badge)
        # Radial-ish gradient: inner lighter orange
        bd.ellipse([0, 0, bd_d - 1, bd_d - 1], fill=(255, 120, 60, 230))
        bd.ellipse([6, 6, bd_d - 7, bd_d - 7], fill=(255, 107, 53, 255))
        _badge = ImageTk.PhotoImage(badge)
        self._refs.append(_badge)
        self.cv.create_image(cx, _LOGO_Y, anchor="center", image=_badge)

        # Medical cross drawn with two rectangles
        arm = 9; bar = 24
        self.cv.create_rectangle(
            cx - arm, _LOGO_Y - bar,
            cx + arm, _LOGO_Y + bar,
            fill=_WHITE, outline=""
        )
        self.cv.create_rectangle(
            cx - bar, _LOGO_Y - arm,
            cx + bar, _LOGO_Y + arm,
            fill=_WHITE, outline=""
        )

        # ── 4. "SACA" wordmark ───────────────────────────────────
        self.cv.create_text(
            cx, _SACA_Y,
            text="SACA",
            font=("Segoe UI", 48, "bold"),
            fill=_WHITE, anchor="center"
        )

        # Subtitle
        self.cv.create_text(
            cx, _SUB_Y,
            text="Swin Smart Adaptive Clinical Assistant",
            font=("Segoe UI", 13),
            fill=_CREAM, anchor="center"
        )

        # ── 5. Italic tagline ────────────────────────────────────
        self.cv.create_text(
            cx, _TAGLINE_Y,
            text="Fast. Trusted. Community-first healthcare.",
            font=("Segoe UI", 11, "italic"),
            fill=_WHITE, anchor="center"
        )

        # ── 6. Decorative orange divider ─────────────────────────
        hw = 160
        self.cv.create_line(
            cx - hw, _DIV_Y, cx - 10, _DIV_Y,
            fill=_ORANGE, width=1
        )
        self.cv.create_oval(
            cx - 5, _DIV_Y - 5,
            cx + 5, _DIV_Y + 5,
            fill=_ORANGE, outline=""
        )
        self.cv.create_line(
            cx + 10, _DIV_Y, cx + hw, _DIV_Y,
            fill=_ORANGE, width=1
        )

        # ── 7. Feature card ──────────────────────────────────────
        card_w = min(W - 64, 500)
        card_x = cx - card_w // 2

        # Card background (dark semi-transparent rounded rect)
        card_img = Image.new("RGBA", (card_w, _CARD_H), (0, 0, 0, 0))
        cd = ImageDraw.Draw(card_img)
        cd.rounded_rectangle(
            [0, 0, card_w - 1, _CARD_H - 1],
            radius=14,
            fill=_CARD_BG,
            outline=(255, 107, 53, 90),
            width=1
        )
        # Orange top border stripe (4 px, inside rounded rect)
        cd.rectangle([1, 0, card_w - 2, 4], fill=(255, 107, 53, 255))
        # Re-clip corners
        cd.rounded_rectangle(
            [0, 0, card_w - 1, _CARD_H - 1],
            radius=14,
            outline=(255, 107, 53, 90),
            width=1
        )
        _card = ImageTk.PhotoImage(card_img)
        self._refs.append(_card)
        self.cv.create_image(card_x, _CARD_Y, anchor="nw", image=_card)

        # "Welcome to SACA" heading inside card
        heading_y = _CARD_Y + _CARD_PAD_Y + 8
        self.cv.create_text(
            card_x + _CARD_PAD_X, heading_y,
            text="Welcome to SACA",
            font=("Segoe UI", 14, "bold"),
            fill=_WHITE, anchor="w"
        )

        # Thin divider below heading
        # Tkinter canvas only accepts hex/named colours — no RGBA tuples.
        # #5a3020 approximates rgba(255,107,53,80) composited over the dark card.
        divider_y = heading_y + 22
        self.cv.create_line(
            card_x + _CARD_PAD_X, divider_y,
            card_x + card_w - _CARD_PAD_X, divider_y,
            fill="#5a3020", width=1
        )

        # Feature rows — centred as a group inside the card.
        # Measure the longest label to compute total row width, then offset
        # from cx so the whole block (circle + gap + text) is horizontally centred.
        features = [
            "Multilingual: English & Yolŋu Matha support",
            "Fast symptom check — results in under 2 minutes",
            "Emergency alerts for serious conditions",
        ]
        ck_d      = 22          # circle diameter
        gap       = 12          # space between circle right-edge and text
        # ~6.8 px/char at 11pt Segoe UI — good enough to centre without a temp widget
        longest   = max(len(f) for f in features)
        est_txt_w = int(longest * 6.8)
        row_w     = ck_d + gap + est_txt_w
        row_x0    = cx - row_w // 2       # left edge of the circle
        ck_cx     = row_x0 + ck_d // 2   # horizontal centre of circle
        tx0       = row_x0 + ck_d + gap  # left edge of label text
        fy        = divider_y + 18

        for feat in features:
            # teal check circle (PIL ImageDraw accepts RGBA)
            ck_img = Image.new("RGBA", (ck_d, ck_d), (0, 0, 0, 0))
            ck = ImageDraw.Draw(ck_img)
            ck.ellipse([0, 0, ck_d - 1, ck_d - 1], fill=(91, 200, 160, 230))
            _ck = ImageTk.PhotoImage(ck_img)
            self._refs.append(_ck)
            # circle centred on fy
            self.cv.create_image(ck_cx, fy, anchor="center", image=_ck)
            # checkmark glyph centred inside circle
            self.cv.create_text(
                ck_cx, fy,
                text="\u2713",
                font=("Segoe UI", 10, "bold"),
                fill=_WHITE, anchor="center"
            )
            # label: anchor="w" = left-middle, so vertical centre aligns with fy
            self.cv.create_text(
                tx0, fy,
                text=feat,
                font=("Segoe UI", 11),
                fill="#E8E8E8", anchor="w"
            )
            fy += 33

        # ── 8. Single centred "GET STARTED →" button ────────────
        btn_w = min(card_w - 60, 300)
        btn_x = cx - btn_w // 2            # centred under the card

        pri_img = pill(btn_w, _BTN_H, _ORANGE)
        _pri = ImageTk.PhotoImage(pri_img)
        self._refs.append(_pri)

        r2c, g2c, b2c = lerp(_ORANGE, "#8B3A10", 0.25)
        pri_h_img = pill(btn_w, _BTN_H, r2h(r2c, g2c, b2c))
        _pri_h = ImageTk.PhotoImage(pri_h_img)
        self._refs.append(_pri_h)

        pri_id = self.cv.create_image(btn_x, _BTN_Y, anchor="nw", image=_pri)
        self.cv.create_text(
            cx, _BTN_Y + _BTN_H // 2,
            text="GET STARTED  →",
            font=("Segoe UI", 13, "bold"),
            fill=_WHITE, anchor="center", tags="pri_btn"
        )
        self.cv.create_rectangle(
            btn_x, _BTN_Y, btn_x + btn_w, _BTN_Y + _BTN_H,
            fill="", outline="", tags="pri_btn"
        )

        # ── Button interactions ──────────────────────────────────
        def on_start(ev=None):
            self.app.go("S1_Lang")

        def pri_enter(ev):
            self.cv.itemconfig(pri_id, image=_pri_h)

        def pri_leave(ev):
            self.cv.itemconfig(pri_id, image=_pri)

        self.cv.tag_bind("pri_btn", "<Button-1>", on_start)
        self.cv.tag_bind("pri_btn", "<Enter>",    pri_enter)
        self.cv.tag_bind("pri_btn", "<Leave>",    pri_leave)
        self.cv.tag_bind(pri_id,    "<Button-1>", on_start)
        self.cv.tag_bind(pri_id,    "<Enter>",    pri_enter)
        self.cv.tag_bind(pri_id,    "<Leave>",    pri_leave)

        # ── 9. Footer ────────────────────────────────────────────
        self.cv.create_text(
            cx, H - _FOOTER_B,
            text="COS70008  ·  Swinburne University of Technology  ·  Semester 1, 2026",
            font=("Segoe UI", 8),
            fill=_MUTED, anchor="center"
        )


# ══════════════════════════════════════════════════════════════════