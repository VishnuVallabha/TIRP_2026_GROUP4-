"""
saca_nlp_bridge.py — Accurate Yolŋu Matha + English NLP for SACA.

PIPELINE (in order):
  1. Normalise  — strip macrons, fix aspirates, collapse spaces
  2. Dictionary — exact + hyphen-space variants (YOLNGU_DICT)
  3. Phonetic   — known Google/Whisper output variants (PHONETIC_MAP)
  4. Fuzzy      — rapidfuzz similarity on all Yolŋu stems (catches new variants)
  5. AI         — Groq Llama (online, optional, best context understanding)
  6. Keyword    — English keyword matching on translated text (offline fallback)

For Indigenous healthcare: never silently fail.
If confidence < threshold, return low-confidence so UI can ask again.
"""

import re
import os
import unicodedata
from pathlib import Path

# ── Groq key ─────────────────────────────────────────────────────
def _get_groq_key():
    for p in [Path(__file__).parent / ".env",
              Path(__file__).parent.parent / ".env"]:
        if p.exists():
            for line in p.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.startswith("GROQ_API_KEY="):
                    k = line.split("=", 1)[1].strip()
                    if k and k not in ("YOUR_KEY_HERE", ""):
                        return k
    return os.getenv("GROQ_API_KEY", "")


# ══════════════════════════════════════════════════════════════════
# YOLŊU MATHA MASTER DICTIONARY
# Keys: exact Yolŋu spelling (with hyphens)
# Values: English medical terms for NLP matching
# ══════════════════════════════════════════════════════════════════
YOLNGU_DICT = {
    # Pain — dhukarr
    "buku-dhukarr":      "headache head pain",
    "butu-dhukarr":      "stomach pain abdominal pain",
    "guku-dhukarr":      "chest pain",
    "maru-dhukarr":      "back pain",
    "laka-dhukarr":      "sore throat throat pain",
    "dhakay-dhukarr":    "ear pain earache",
    "mel-dhukarr":       "eye pain",
    "muu-dhukarr":       "knee pain",
    "dhukal-dhukarr":    "body pain whole body aches",

    # Fever / temperature
    "dharpa-wuku":       "fever feeling hot temperature",
    "bulu-wuku":         "chills cold shivering",
    "märr":              "fever",
    "marr":              "fever",
    "dharpa-djorra":     "high fever very hot",

    # Breathing
    "dhu-wuku":          "cannot breathe breathless shortness of breath",
    "gurrku":            "hard to breathe difficulty breathing",

    # Fatigue / weakness
    "wirrika":           "weak fatigue tired no energy",
    "djama-wirrika":     "very tired exhausted fatigue",
    "djaka":             "tired fatigue",

    # Stomach / digestion
    "gulktji":           "vomiting nausea throwing up",
    "guku-guku":         "cough coughing",
    "nuru-gapu":         "runny nose",
    "gapu-djorra":       "diarrhoea",
    "nha-wirrika":       "no appetite cannot eat",
    "yunggurr-wirrika":  "thirsty very thirsty",

    # Skin / other
    "buku-wuku":         "dizzy dizziness spinning",
    "malk-djorra":       "skin rash rash",
    "gulan-wuku":        "bleeding blood",
    "naraka-djorra":     "fracture broken bone",

    # General
    "marrtjin":          "not feeling well sick unwell",
    "wayin":             "sick unwell",

    # Severity
    "mäkitj":            "mild not bad",
    "djorra":            "bad serious",
    "djorra-bukmak":     "very bad worst",
    "bukmak":            "both everything",

    # Time
    "dhuwali":           "today",
    "warray":            "yesterday",
    "wanggany":          "one",
    "rua":               "two",
    "lurrkun":           "three",
    "dhuwala":           "days",
    "ga":                "and",

    # Body parts (when spoken alone)
    "nuthu":             "head headache",
    "buku":              "head",
    "butu":              "stomach",
    "guku":              "chest",
    "maru":              "back",
    "laka":              "throat",
    "galk":              "back",
    "dhawu":             "cough throat",
    "wana":              "stomach",
}

# ══════════════════════════════════════════════════════════════════
# PHONETIC MAP
# Exactly what Google Speech / Whisper returns when it hears Yolŋu.
# Built from real testing — every "Heard:" screenshot variant.
# Keys are NORMALISED (lowercase, no macrons, no extra punctuation)
# ══════════════════════════════════════════════════════════════════
PHONETIC_MAP = {
    # ── HEAD / HEADACHE ───────────────────────────────────────────
    "buku dukar":           "headache head pain",
    "buku dukhar":          "headache head pain",
    "buku duka":            "headache head pain",
    "bhuku dukar":          "headache head pain",
    "bhuku dukhar":         "headache head pain",   # screenshot
    "bhuku duka":           "headache head pain",
    "boo koo doo kar":      "headache head pain",
    "bukudhukarr":          "headache head pain",
    "nuthu":                "headache head pain",

    # ── STOMACH PAIN ─────────────────────────────────────────────
    "butu dukar":           "stomach pain",
    "butu dukhar":          "stomach pain",
    "butu dhukar":          "stomach pain",
    "bhutu dukar":          "stomach pain",
    "bhutu dukhar":         "stomach pain",
    "bhutu dhukar":         "stomach pain",         # screenshot Image 2
    "bhutudhukar":          "stomach pain",         # screenshot Image 1
    "bu tu dukar":          "stomach pain",
    "bu tu dukhar":         "stomach pain",
    "bu tu dhukar":         "stomach pain",
    "boo too doo kar":      "stomach pain",
    "wana":                 "stomach pain",

    # ── CHEST PAIN ───────────────────────────────────────────────
    "guku dukar":           "chest pain",
    "guku dukhar":          "chest pain",
    "guku dhukar":          "chest pain",
    "goo koo doo kar":      "chest pain",

    # ── BACK PAIN ────────────────────────────────────────────────
    "maru dukar":           "back pain",
    "maru dukhar":          "back pain",
    "maru dhukar":          "back pain",
    "galk":                 "back pain",

    # ── SORE THROAT ──────────────────────────────────────────────
    "laka dukar":           "sore throat",
    "laka dukhar":          "sore throat",
    "laka dhukar":          "sore throat",
    "laka dhukhar":         "sore throat",          # screenshot

    # ── FEVER ────────────────────────────────────────────────────
    "darpa wuku":           "fever feeling hot",
    "darpa woku":           "fever feeling hot",
    "darpa wookoo":         "fever feeling hot",    # screenshot
    "darpa wukoo":          "fever feeling hot",
    "dharpa wuku":          "fever feeling hot",
    "dharpa woku":          "fever feeling hot",
    "dharpa wookoo":        "fever feeling hot",    # screenshot
    "dharpa wukoo":         "fever feeling hot",
    "dar pa woo koo":       "fever feeling hot",
    "marr":                 "fever",
    "maar":                 "fever",

    # ── CANNOT BREATHE ───────────────────────────────────────────
    "dhu wuku":             "cannot breathe",
    "dhu woku":             "cannot breathe",
    "dhu wookoo":           "cannot breathe",
    "dhu wukoo":            "cannot breathe",
    "gurrku":               "hard to breathe",
    "gurku":                "hard to breathe",
    "gurrk":                "hard to breathe",

    # ── DIZZY ────────────────────────────────────────────────────
    "buku wuku":            "dizzy dizziness",
    "buku woku":            "dizzy dizziness",
    "buku wookoo":          "dizzy dizziness",      # screenshot
    "buku wukoo":           "dizzy dizziness",
    "boo koo woo koo":      "dizzy dizziness",

    # ── VOMITING ─────────────────────────────────────────────────
    "gulktji":              "vomiting nausea",
    "gulk ji":              "vomiting nausea",
    "gulk jee":             "vomiting nausea",
    "gulp ji":              "vomiting nausea",

    # ── WEAK / TIRED ─────────────────────────────────────────────
    "wirrika":              "weak tired fatigue",
    "wir rika":             "weak tired fatigue",
    "wirrika":              "weak tired fatigue",
    "djaka":                "tired fatigue",
    "jaka":                 "tired fatigue",

    # ── COUGH ────────────────────────────────────────────────────
    "guku guku":            "cough coughing",
    "goo koo goo koo":      "cough coughing",
    "dhawu":                "cough throat",

    # ── SICK / UNWELL ────────────────────────────────────────────
    "wayin":                "sick unwell",
    "why in":               "sick unwell",
    "martjin":              "not feeling well",
    "mar tjin":             "not feeling well",
    "marrtjin":             "not feeling well",

    # ── CHILLS ───────────────────────────────────────────────────
    "bulu wuku":            "chills cold shivering",
    "bulu woku":            "chills cold shivering",
    "bulu wookoo":          "chills cold shivering",

    # ── TIME ─────────────────────────────────────────────────────
    "dhuwali":              "today",
    "doo wa lee":           "today",
    "doo wali":             "today",
    "warray":               "yesterday",
    "war ray":              "yesterday",
}

# ══════════════════════════════════════════════════════════════════
# SYMPTOM DEFINITIONS — maps English phrase → symptom name + key
# ══════════════════════════════════════════════════════════════════
SYMPTOM_KEYWORDS = [
    # (keywords_list, symptom_name, symptom_key)
    (["headache","head pain","head ache","head hurts","nuthu","buku"],
     "Headache", "headache"),
    (["stomach pain","abdominal pain","tummy","belly","stomach ache",
       "stomach hurts","stomach hurt","wana","butu","stomach"],
     "Stomach Pain", "stomach"),
    (["chest pain","chest hurt","chest tight","heart pain","guku"],
     "Chest Pain", "chest"),
    (["fever","temperature","feeling hot","body hot","hot body","dharpa","marr",
       "fever chills","fever and chills"],
     "Fever", "fever"),
    (["cough","coughing","dry cough","guku guku","dhawu"],
     "Cough", "cough"),
    (["cannot breathe","hard to breathe","breathless","shortness","dhu wuku","gurrku"],
     "Hard to Breathe", "breathless"),
    (["dizzy","dizziness","spinning","light headed","buku wuku"],
     "Feeling Dizzy", "dizziness"),
    (["tired","fatigue","exhausted","weak","no energy","wirrika","djaka"],
     "Very Tired", "fatigue"),
    (["vomiting","vomit","throw up","nausea","gulktji"],
     "Vomiting", "vomiting"),
    (["skin rash","rash","itchy","malk"],
     "Skin Rash", "rash"),
    (["back pain","back ache","back hurt","lower back","maru","galk"],
     "Back Pain", "back"),
    (["sore throat","throat pain","throat","laka"],
     "Sore Throat", "throat"),
    (["chills","cold feeling","shivering","bulu wuku"],
     "Chills", "fever"),
    (["bleeding","blood","gulan"],
     "Chest Pain", "chest"),
    (["sick","unwell","not feeling well","wayin","marrtjin"],
     "Fever", "fever"),
    (["ear pain","earache","dhakay"],
     "Sore Throat", "throat"),
    (["eye pain","mel"],
     "Headache", "headache"),
    (["knee pain","muu"],
     "Back Pain", "back"),
]

DURATION_MAP = [
    (["today","just now","this morning","dhuwali"], 0),
    (["yesterday","1 day","one day","warray"], 1),
    (["2 days","two days","rua dhuwala"], 2),
    (["3 days","three days","lurrkun"], 3),
    (["week","7 days","few days"], 7),
    (["2 weeks","fortnight"], 14),
    (["month","long time"], 21),
]

SEVERITY_MAP = [
    (["very mild","little bit","slight","makitj","mäkitj"], 2),
    (["mild","not too bad","ok"], 3),
    (["moderate","medium","some"], 5),
    (["bad","quite bad","painful","djorra"], 7),
    (["severe","very bad","really bad","unbearable"], 9),
    (["extreme","worst","10","djorra bukmak"], 10),
]


# ══════════════════════════════════════════════════════════════════
# NORMALISATION
# ══════════════════════════════════════════════════════════════════
def _normalise(text: str) -> str:
    """
    Normalise speech-to-text output for Yolŋu matching.
    Handles macrons, aspirates, doubled vowels, punctuation, case.
    """
    t = text.lower().strip()

    # Replace diacritics
    for ch, r in [('ū','u'),('ā','a'),('ī','i'),('ō','o'),('ŋ','ng'),
                  ('ä','a'),('ë','e'),('ö','o'),('ü','u'),('â','a'),
                  ('ê','e'),('î','i'),('ô','o'),('û','u'),('ñ','n'),
                  ('\u2019',"'"),('\u2018',"'"),]:
        t = t.replace(ch, r)

    # Unicode NFD strip
    t = unicodedata.normalize('NFD', t)
    t = ''.join(c for c in t if unicodedata.category(c) != 'Mn')

    # Remove punctuation
    t = re.sub(r"[',\\.!?;:\"]", " ", t)

    # Simplify doubled vowels at word ends (wookoo→wuku, dhukarr→dhukar)
    t = re.sub(r'oo\b', 'u', t)
    t = re.sub(r'rr\b', 'r', t)
    t = re.sub(r'kk\b', 'k', t)

    # Collapse spaces
    t = re.sub(r'\s+', ' ', t).strip()
    return t


# ══════════════════════════════════════════════════════════════════
# TRANSLATION PIPELINE
# ══════════════════════════════════════════════════════════════════
def _translate_yolngu(text: str) -> str:
    """
    3-stage translation: exact → phonetic → fuzzy.
    Returns English medical text ready for symptom matching.
    """
    norm = _normalise(text)
    result = norm

    # Stage 1: Exact PHONETIC_MAP match (normalised keys)
    norm_phonetic = {_normalise(k): v for k, v in PHONETIC_MAP.items()}
    for key, val in sorted(norm_phonetic.items(), key=lambda x: -len(x[0])):
        result = result.replace(key, val)

    # Stage 2: YOLNGU_DICT — try hyphenated and space variants
    for yolngu, english in sorted(YOLNGU_DICT.items(), key=lambda x: -len(x[0])):
        norm_key = _normalise(yolngu)
        result = result.replace(norm_key, english)
        result = result.replace(norm_key.replace('-', ' '), english)

    # Stage 3: Fuzzy matching on individual words not yet translated
    result = _fuzzy_word_translate(result, norm)

    return result


def _fuzzy_word_translate(translated: str, original_norm: str) -> str:
    """
    For any word in the original that wasn't translated,
    find the closest Yolŋu dictionary key using fuzzy matching.
    Threshold 78% — high enough to avoid false matches.
    """
    try:
        from rapidfuzz import fuzz, process
    except ImportError:
        return translated

    # Build flat list of (normalised_key, english_value)
    all_keys = {}
    for k, v in PHONETIC_MAP.items():
        all_keys[_normalise(k)] = v
    for k, v in YOLNGU_DICT.items():
        all_keys[_normalise(k)] = v
        all_keys[_normalise(k).replace('-', ' ')] = v

    words = original_norm.split()
    result_words = translated.split()

    # Check each word — if it still looks like an untranslated Yolŋu word
    for i, word in enumerate(words):
        if word in result_words and len(word) > 3:
            # Try fuzzy match against all known keys
            match = process.extractOne(
                word,
                all_keys.keys(),
                scorer=fuzz.ratio,
                score_cutoff=78
            )
            if match:
                matched_key, score, _ = match
                english = all_keys[matched_key]
                # Replace in result
                translated = re.sub(r'\b' + re.escape(word) + r'\b',
                                    english, translated)

    # Also try full phrase fuzzy match
    best = process.extractOne(
        original_norm,
        all_keys.keys(),
        scorer=fuzz.partial_ratio,
        score_cutoff=82
    )
    if best:
        matched_key, score, _ = best
        english = all_keys[matched_key]
        # Only use if the current translation still has untranslated words
        untranslated = any(
            w in [_normalise(k) for k in YOLNGU_DICT]
            or _looks_yolngu(w)
            for w in translated.split()
        )
        if untranslated:
            translated = english + " " + translated

    return translated


def _looks_yolngu(word: str) -> bool:
    """Heuristic: does this word look like untranslated Yolŋu?"""
    # Yolŋu words often contain these patterns
    yolnu_patterns = ['dhukar', 'wuku', 'buku', 'butu', 'guku',
                      'wirrika', 'gulkt', 'dhawa', 'marr', 'djorra']
    return any(p in word for p in yolnu_patterns)


# ══════════════════════════════════════════════════════════════════
# SYMPTOM MATCHING
# ══════════════════════════════════════════════════════════════════
def _match_symptom(text: str):
    """Match translated English text to a symptom using keyword scoring."""
    t = text.lower()
    best_sym, best_key, best_score = None, None, 0

    for keywords, sym_name, sym_key in SYMPTOM_KEYWORDS:
        score = sum(len(kw) for kw in keywords if kw in t)
        if score > best_score:
            best_score = score
            best_sym   = sym_name
            best_key   = sym_key

    return best_sym, best_key, best_score


def _extract_duration(text: str):
    for keywords, d in DURATION_MAP:
        if any(k in text for k in keywords):
            return d
    m = re.search(r'(\d+)\s*(day|days)', text)
    return int(m.group(1)) if m else None


def _extract_severity(text: str):
    for keywords, s in SEVERITY_MAP:
        if any(k in text for k in keywords):
            return s
    return None


# ══════════════════════════════════════════════════════════════════
# AI EXTRACTION (online, optional)
# ══════════════════════════════════════════════════════════════════
def _ai_extract(text: str, language: str = "english", age: int = 30):
    """
    Groq Llama — best for context. Optional, online only.
    Falls back silently if unavailable.
    """
    key = _get_groq_key()
    if not key:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=key)
        prompt = (
            f"You are a medical assistant for Yolŋu Matha speakers in Yirrkala, "
            f"Northern Territory, Australia.\n"
            f"A patient said: \"{text}\"\n"
            f"Language context: {language}. Patient age: {age}.\n"
            f"Extract the main medical symptom. Respond ONLY with valid JSON:\n"
            f"{{\"symptom\": \"Headache\", \"key\": \"headache\", "
            f"\"days\": null, \"severity\": null, \"confidence\": \"high\"}}\n"
            f"Valid symptom names: Headache, Abdominal Pain, Chest Pain, Fever, "
            f"Cough, Hard to Breathe, Feeling Dizzy, Very Tired, Vomiting, "
            f"Skin Rash, Back Pain, Sore Throat\n"
            f"Valid keys: headache, stomach, chest, fever, cough, breathless, "
            f"dizziness, fatigue, vomiting, rash, back, throat"
        )
        r = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=120,
        )
        import json
        return json.loads(r.choices[0].message.content.strip())
    except Exception as e:
        print(f"[NLP] AI unavailable ({type(e).__name__}) — offline mode")
        return None


# ══════════════════════════════════════════════════════════════════
# PUBLIC API
# ══════════════════════════════════════════════════════════════════
def extract_symptom_from_text(text: str, language: str = "english",
                               age: int = 30) -> dict:
    """
    Main entry point. Works fully offline via dictionary + fuzzy matching.
    Uses AI when available for better accuracy.

    Returns dict with keys:
      symptom    — English symptom name or None
      key        — symptom key
      confidence — 'high' / 'medium' / 'low'
      days       — duration in days or None
      severity   — 1–10 or None
      error      — error message or None
    """
    if not text or not text.strip():
        return _empty("Empty input")

    # Translate Yolŋu → English
    translated = _translate_yolngu(text)
    t_lower    = translated.lower()

    # Try AI first (best accuracy when online)
    ai = _ai_extract(text, language, age)
    if ai and ai.get("symptom") and ai.get("key"):
        return {
            "symptom":    ai["symptom"],
            "key":        ai["key"],
            "confidence": ai.get("confidence", "high"),
            "days":       ai.get("days") or _extract_duration(t_lower),
            "severity":   ai.get("severity") or _extract_severity(t_lower),
            "error":      None,
        }

    # Offline keyword matching
    sym, key, score = _match_symptom(t_lower)

    if sym and score >= 3:
        confidence = "high" if score >= 8 else "medium"
        return {
            "symptom":    sym,
            "key":        key,
            "confidence": confidence,
            "days":       _extract_duration(t_lower),
            "severity":   _extract_severity(t_lower),
            "error":      None,
        }

    # Low score match — still return but flag low confidence
    if sym:
        return {
            "symptom":    sym,
            "key":        key,
            "confidence": "low",
            "days":       _extract_duration(t_lower),
            "severity":   _extract_severity(t_lower),
            "error":      "Low confidence — please confirm",
        }

    return _empty(
        "Could not identify symptom. "
        "Try: buku-dhukarr (headache), dharpa-wuku (fever), "
        "butu-dhukarr (stomach pain), guku-dhukarr (chest pain)"
    )


def _empty(error: str) -> dict:
    return {"symptom": None, "key": None, "confidence": "low",
            "days": None, "severity": None, "error": error}
