"""
saca_nlp_bridge.py — Built-in keyword-based symptom extractor.
Replaces the external NLP bridge when the ML model files are not present.
Works for both English and Yolngu Matha inputs.
"""

# ── Keyword → symptom mapping ─────────────────────────────────────
# Each entry: list of keywords → (symptom display name, symptom key)
KEYWORD_MAP = [
    # English keywords
    (["headache","head ache","head pain","migraine","head hurt","skull"],
     ("Headache", "headache")),

    (["chest pain","chest hurt","chest tight","heart pain","chest pressure",
      "chest ache","heart hurt","chest"],
     ("Chest Pain", "chest")),

    (["stomach pain","stomach ache","stomach hurt","belly pain","belly ache",
      "abdominal","tummy","nausea","stomach"],
     ("Stomach Pain", "stomach")),

    (["fever","temperature","hot body","body hot","high temp","sweating fever"],
     ("Fever", "fever")),

    (["cough","coughing","dry cough","wet cough","chest cough"],
     ("Cough", "cough")),

    (["hard to breathe","cant breathe","cannot breathe","breathless",
      "short breath","shortness","breathing","breath"],
     ("Hard to Breathe", "breathless")),

    (["dizzy","dizziness","spinning","light headed","lightheaded","vertigo"],
     ("Feeling Dizzy", "dizziness")),

    (["tired","fatigue","exhausted","no energy","weak","weakness","very tired"],
     ("Very Tired", "fatigue")),

    (["vomit","vomiting","throw up","throwing up","nausea","sick stomach"],
     ("Vomiting", "vomiting")),

    (["rash","skin rash","itchy skin","skin itch","spots","skin spots"],
     ("Skin Rash", "rash")),

    (["back pain","back ache","back hurt","lower back","spine pain","back"],
     ("Back Pain", "back")),

    (["sore throat","throat pain","throat hurt","swollen throat","throat"],
     ("Sore Throat", "throat")),

    # Yolngu Matha keywords
    (["nuthu","buku","ŋuthu","head"],            ("Headache",      "headache")),
    (["buku-djarrka","buku djarrka","chest"],    ("Chest Pain",    "chest")),
    (["wana","wäna","wäŋa","stomach","belly"],   ("Stomach Pain",  "stomach")),
    (["marr","märr","fever","hot"],              ("Fever",         "fever")),
    (["guku","cough"],                           ("Cough",         "cough")),
    (["galk","gälk","back"],                     ("Back Pain",     "back")),
    (["dhawu","dhäwu","throat"],                 ("Sore Throat",   "throat")),
    (["bukmak","vomit"],                         ("Vomiting",      "vomiting")),
    (["djaka","djäka","tired"],                  ("Very Tired",    "fatigue")),
    (["marrtji","dizzy","spin"],                 ("Feeling Dizzy", "dizziness")),
]

# Duration keywords → days
DURATION_MAP = [
    (["today","just now","just started","this morning","tonight"], 0),
    (["yesterday","1 day","one day"],                              1),
    (["2 days","two days","couple days"],                          2),
    (["3 days","three days"],                                      3),
    (["week","7 days","few days"],                                 7),
    (["2 weeks","two weeks","fortnight"],                          14),
    (["month","long time","weeks"],                                21),
]

# Severity keywords → score
SEVERITY_MAP = [
    (["very mild","little bit","tiny bit","slight"],               2),
    (["mild","not too bad","manageable","ok"],                     3),
    (["moderate","medium","some"],                                 5),
    (["bad","quite bad","painful"],                                7),
    (["severe","very bad","really bad","very painful","unbearable"],9),
    (["extreme","worst","emergency","10","ten out of ten"],        10),
]


def extract_symptom_from_text(text, language="english", age=30):
    """
    Match text against keyword lists and return structured result.
    Returns dict: {symptom, key, confidence, days, severity, error}
    """
    if not text:
        return {"symptom": None, "key": None, "confidence": "low",
                "days": None, "severity": None, "error": "Empty input"}

    t = text.lower().strip()

    # ── Symptom match ─────────────────────────────────────────────
    matched_symptom = None
    matched_key     = None
    best_score      = 0

    for keywords, (sym_name, sym_key) in KEYWORD_MAP:
        for kw in keywords:
            if kw in t:
                score = len(kw)   # longer match = more specific = better
                if score > best_score:
                    best_score      = score
                    matched_symptom = sym_name
                    matched_key     = sym_key

    if not matched_symptom:
        return {"symptom": None, "key": None, "confidence": "low",
                "days": None, "severity": None,
                "error": "No symptom recognised — try words like headache, fever, chest pain"}

    confidence = "high" if best_score >= 6 else "medium" if best_score >= 3 else "low"

    # ── Duration match ────────────────────────────────────────────
    days = None
    for keywords, d in DURATION_MAP:
        for kw in keywords:
            if kw in t:
                days = d
                break
        if days is not None:
            break

    # ── Severity match ────────────────────────────────────────────
    severity = None
    for keywords, s in SEVERITY_MAP:
        for kw in keywords:
            if kw in t:
                severity = s
                break
        if severity is not None:
            break

    return {
        "symptom":    matched_symptom,
        "key":        matched_key,
        "confidence": confidence,
        "days":       days,
        "severity":   severity,
        "error":      None,
    }
