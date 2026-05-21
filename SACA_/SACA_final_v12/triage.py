"""
SACA — Clinical triage engine.
triage(sym, days, sev, med, other, fever_temp, pain_type, breathe_scale, chills)
-> "mild" | "moderate" | "severe"

Connect the ML classifier here when ready.
"""
from constants import *

# Symptom risk weights (updated to match simplified display names)
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
    # Legacy names kept for compatibility
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

def triage(sym, days, sev, med, other, fever_temp, pain_type, breathe_scale, chills, activity=3):
    s = RISK.get(sym, 1)
    s += int(sev * 1.8)
    if days > 14: s += 5
    elif days > 10: s += 4
    elif days > 5:  s += 2
    elif days > 2:  s += 1
    # Activity level: 4=fully normal, 3=mostly OK, 2=struggling, 1=cannot function
    if activity == 1:   s += 4   # cannot do daily activities = serious
    elif activity == 2: s += 2   # struggling
    elif activity == 3: s += 0   # mostly OK
    if other:   s += 2
    _, temp_pts = temp_band(fever_temp)
    s += temp_pts
    if pain_type == "Sharp/Stabbing": s += 2
    elif pain_type == "Burning":      s += 1
    if breathe_scale >= 8:   s += 4
    elif breathe_scale >= 6: s += 3
    elif breathe_scale >= 4: s += 2
    elif breathe_scale >= 2: s += 1
    if chills: s += 2
    return "severe" if s >= 20 else "moderate" if s >= 11 else "mild"
