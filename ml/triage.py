"""
SACA — Clinical triage engine (ML-powered).

triage(sym, days, sev, med, other, fever_temp, pain_type, breathe_scale, chills, activity)
-> "mild" | "moderate" | "severe"

ML model is used when available.
Falls back to rule-based scoring if ML is not ready.
"""
from constants import *

# ── Symptom risk weights (rule-based fallback) ────────────────────
RISK = {
    "Chest Pain":       5,
    "Hard to Breathe":  5,
    "Feeling Dizzy":    3,
    "Fever":            3,
    "Vomiting":         3,
    "Stomach Pain":     2,
    "Headache":         2,
    "Cough":            1,
    "Very Tired":       1,
    "Skin Rash":        1,
    "Back Pain":        1,
    "Sore Throat":      1,
    "Breathless":       5,
    "Dizziness":        3,
    "Fatigue":          1,
    "Breathlessness":   5,
}


def temp_band(t):
    if t <= 0:   return "not recorded",                    0
    if t < 36.0: return "hypothermia (dangerously low)",   3
    if t < 36.5: return "below normal (mild hypothermia)", 1
    if t < 37.5: return "normal",                          0
    if t < 38.0: return "low-grade fever",                 1
    if t < 38.5: return "mild fever",                      1
    if t < 39.0: return "moderate fever",                  2
    if t < 39.5: return "high fever",                      3
    if t < 40.0: return "very high fever",                 4
    return "dangerously high fever", 5


def _rule_based(sym, days, sev, med, other, fever_temp, pain_type, breathe_scale, chills, activity=3):
    """Original rule-based scoring — used as fallback."""
    s = RISK.get(sym, 1)
    s += int(sev * 1.8)
    if days > 14: s += 5
    elif days > 10: s += 4
    elif days > 5:  s += 2
    elif days > 2:  s += 1
    if activity == 1:   s += 4
    elif activity == 2: s += 2
    if other: s += 2
    _, tp = temp_band(fever_temp)
    s += tp
    if pain_type == "Sharp/Stabbing": s += 2
    elif pain_type == "Burning":      s += 1
    if breathe_scale >= 8:   s += 4
    elif breathe_scale >= 6: s += 3
    elif breathe_scale >= 4: s += 2
    elif breathe_scale >= 2: s += 1
    if chills: s += 2
    return "severe" if s >= 20 else "moderate" if s >= 11 else "mild"


def triage(sym, days, sev, med, other, fever_temp, pain_type, breathe_scale, chills, activity=3):
    """
    Main triage function called by app.py → analyse().
    Uses ML model when available, falls back to rules.
    """
    from ml_engine import is_ready, ml_predict

    if is_ready():
        # ── Map SACA question values → ML feature columns ────────
        # heart_rate estimated from pain severity
        heart_rate = 70 + (sev * 5)
        heart_rate = min(heart_rate, 140)

        # breathing_rate estimated from breathe_scale + activity
        activity_boost = {4: 0, 3: 1, 2: 2, 1: 4}
        breathing_rate = 16 + int(breathe_scale * 1.5) + activity_boost.get(activity, 0)

        result = ml_predict(
            symptom_text  = sym or "unknown",
            age           = 35,          # default age; app sets this via age_v
            heart_rate    = heart_rate,
            temperature   = fever_temp,
            breathing_rate = breathing_rate,
        )

        if result is not None:
            label, _, _, _ = result
            return label.lower()

    # ── Fallback: rule-based ──────────────────────────────────────
    return _rule_based(sym, days, sev, med, other, fever_temp,
                       pain_type, breathe_scale, chills, activity)
