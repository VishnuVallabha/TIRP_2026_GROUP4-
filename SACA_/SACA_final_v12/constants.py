"""
SACA — Constants, palette, symptom list, and body-region definitions.
Import this module everywhere instead of repeating definitions.
"""
"""
SACA — Swin Smart Adaptive Clinical Assistant
Windows Desktop Application — Full Rebuild
COS70008 Technology Innovation Project — Semester 1, 2026
Developer: Indra Reddy Dyapa

pip install pillow
python saca_app.py

Put these files in the same folder:
  saca_app.py
  aboriginal_cover.jpg  (the Aboriginal painting image)
"""

import tkinter as tk
from tkinter import Canvas, Frame, Label, Entry, StringVar, BooleanVar, IntVar
import tkinter.messagebox
from PIL import Image, ImageDraw, ImageFont, ImageTk, ImageFilter
import math, random, os, sys, threading, urllib.request, io

# ══════════════════════════════════════════════════════════════════
# PALETTE — Warm cream / Indigenous Australian inspired
# ══════════════════════════════════════════════════════════════════
# ── Professional Medical App Palette ────────────────────────────
BG      = "#F7F8FC"          # cool off-white
BG_CARD = "#FFFFFF"          # pure white cards
BG_ALT  = "#EEF1F8"          # subtle blue-grey
BORDER  = "#DDE3F0"          # soft border
BORDER2 = "#B0BDD8"          # stronger border
TXT1    = "#0D1B2A"          # near-black
TXT2    = "#2E4057"          # dark slate
TXT3    = "#607B96"          # medium slate
TXT4    = "#A0B2C6"          # muted
OCHRE   = "#FF6B35"          # vivid coral-orange (CTA)
GREEN   = "#00875A"          # medical green
TERRA   = "#E63946"          # alert red
SKY     = "#1B75BC"          # medical blue
GOLD    = "#F4A261"          # warm amber
RED_EM  = "#D62828"          # emergency red
RED_BG  = "#FFF0F0"
YEL_BG  = "#FFFBEB"
GRN_BG  = "#F0FFF8"
# Extra professional colours
NAVY    = "#0A2342"          # deep navy for headers
TEAL    = "#0097A7"          # teal accent
PURPLE  = "#6C63FF"          # modern purple
CARD_SH = "#E8EDF5"         # card shadow colour

SEV_COLS = ["#4ADE80","#86EFAC","#BEF264","#FDE047","#FCD34D",
             "#FBBF24","#FB923C","#F97316","#EF4444","#DC2626"]

SYMPTOMS = [
    {"en":"Fever",           "yo":"Märr",         "code":"S01","c":TERRA,    "key":"fever",      "region":["fullbody","head","chest"]},
    {"en":"Headache",        "yo":"Ŋuthu·ŋuthu", "code":"S02","c":"#6D4C41","key":"headache",   "region":["head"]},
    {"en":"Chest Pain",      "yo":"Buku·djarrka","code":"S03","c":TERRA,     "key":"chest",      "region":["chest"]},
    {"en":"Cough",           "yo":"Guku",         "code":"S04","c":SKY,      "key":"cough",      "region":["chest","throat"]},
    {"en":"Stomach Pain",    "yo":"Wäŋa·wäŋa",   "code":"S05","c":GOLD,     "key":"stomach",    "region":["stomach"]},
    {"en":"Hard to Breathe", "yo":"Ŋunha",        "code":"S06","c":SKY,      "key":"breathless", "region":["chest","throat"]},
    {"en":"Feeling Dizzy",   "yo":"Marrtji",      "code":"S07","c":"#B87333","key":"dizziness",  "region":["head"]},
    {"en":"Very Tired",      "yo":"Djäka",        "code":"S08","c":"#8B7355","key":"fatigue",    "region":["fullbody","back"]},
    {"en":"Vomiting",        "yo":"Bukmak",       "code":"S09","c":"#CD5C5C","key":"vomiting",   "region":["stomach"]},
    {"en":"Skin Rash",       "yo":"Ŋuli·ŋuli",   "code":"S10","c":GOLD,     "key":"rash",       "region":["fullbody"]},
    {"en":"Back Pain",       "yo":"Gälk",         "code":"S11","c":"#C19A6B","key":"back",       "region":["back"]},
    {"en":"Sore Throat",     "yo":"Dhäwu",        "code":"S12","c":OCHRE,    "key":"throat",     "region":["throat","head"]},
]

# Body-part region definitions for S3_BodyPart screen
BODY_REGIONS = [
    ("head",     "Head",         "Ŋuthu",        "🧠", SKY),
    ("chest",    "Chest",        "Buku-djarrka", "❤",  TERRA),
    ("stomach",  "Stomach",      "Wäŋa",         "🤢", GOLD),
    ("back",     "Back",         "Gälk",         "🦴", "#795548"),
    ("throat",   "Throat",       "Dhäwu",        "🗣", OCHRE),
    ("fullbody", "Whole Body",   "Märr-yukurra", "🌡", GREEN),
]

# Real human photo URLs (Pixabay free license)
PHOTO_URLS = {
    "fever":      "https://cdn.pixabay.com/photo/2018/02/08/22/27/flu-3140375_640.jpg",
    "headache":   "https://cdn.pixabay.com/photo/2017/09/12/11/56/pain-2743965_640.jpg",
    "chest":      "https://cdn.pixabay.com/photo/2017/07/21/18/05/heart-attack-2526890_640.jpg",
    "cough":      "https://cdn.pixabay.com/photo/2020/04/22/15/11/coronavirus-5078139_640.jpg",
    "stomach":    "https://cdn.pixabay.com/photo/2017/06/06/22/37/woman-2378330_640.jpg",
    "breathless": "https://cdn.pixabay.com/photo/2017/10/10/07/48/respiratory-2836395_640.jpg",
    "dizziness":  "https://cdn.pixabay.com/photo/2018/01/26/09/57/dizziness-3108452_640.jpg",
    "fatigue":    "https://cdn.pixabay.com/photo/2018/01/15/07/52/woman-3083379_640.jpg",
    "vomiting":   "https://cdn.pixabay.com/photo/2020/01/22/10/06/stomach-4783741_640.jpg",
    "rash":       "https://cdn.pixabay.com/photo/2019/02/20/10/20/allergy-4009573_640.jpg",
    "back":       "https://cdn.pixabay.com/photo/2018/03/26/17/01/back-3263077_640.jpg",
    "throat":     "https://cdn.pixabay.com/photo/2020/03/16/22/04/sore-throat-4938890_640.jpg",
}

_PHOTO_CACHE = {}
