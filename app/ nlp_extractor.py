"""
nlp_extractor.py
Extracts structured fields from free text / voice input for the ML pipeline.
Fields: symptom_text, symptoms, days, severity_score, medication_taken,
        other_body_part, age, gender, body_location, target (mild/moderate/severe)
"""

import re
from typing import Optional

# ── Yolŋu Matha → English symptom map ────────────────────────────────────────
YOLNGU_DICT = {
    "buku-dhukarr": "head pain / headache",
    "butu-dhukarr": "stomach pain",
    "guku-dhukarr": "chest pain",
    "dhukal-dhukarr": "body pain / aches all over",
    "dharpa-wuku": "fever / feeling hot",
    "bulu-wuku": "feeling cold / chills",
    "djama-wirrika": "feeling very tired / fatigue",
    "wirrika": "feeling weak",
    "dhu-wuku": "cannot breathe / breathlessness",
    "guku-guku": "cough",
    "nuru-gapu": "runny nose",
    "laka-dhukarr": "sore throat / painful swallowing",
    "dhakay-dhukarr": "ear pain",
    "mel-dhukarr": "eye pain / sore eyes",
    "gulktji": "vomiting / being sick",
    "gapu-djorra": "diarrhoea",
    "nha-wirrika": "cannot eat / no appetite",
    "yunggurr-wirrika": "cannot drink / very thirsty",
    "gulan-wuku": "bleeding",
    "malk-djorra": "skin rash / skin problem",
    "djorra-wuku": "swollen body part",
    "naraka-djorra": "broken bone / fracture",
    "muu-dhukarr": "knee pain",
    "maru-dhukarr": "back pain",
    "buku-wuku": "feeling dizzy",
    "mel-wirrika": "cannot see properly",
    "winya-wirrika": "cannot hear properly",
    "dhukarr-buku": "feeling scared / anxious",
    "dhipinu": "feeling sad / depressed",
    "gutha-dhakay": "child is sick",
    "djambatj-dhakay": "elder is sick",
    "gumurr-dhawu": "pregnant woman needs help",
    "rom-djama": "i need medicine",
    "djama-wuku": "i need help urgently",
    "dhipinu-wirrika": "i feel better",
}

# ── Known English symptom keywords → canonical label ─────────────────────────
SYMPTOM_KEYWORDS = {
    "headache": "headache",
    "head pain": "headache",
    "head hurts": "headache",
    "stomach pain": "stomach pain",
    "stomach ache": "stomach pain",
    "tummy pain": "stomach pain",
    "chest pain": "chest pain",
    "chest hurts": "chest pain",
    "body pain": "body pain",
    "body ache": "body pain",
    "fever": "fever",
    "feeling hot": "fever",
    "temperature": "fever",
    "chills": "chills",
    "cold": "chills",
    "feeling cold": "chills",
    "tired": "fatigue",
    "fatigue": "fatigue",
    "exhausted": "fatigue",
    "no energy": "fatigue",
    "weak": "weakness",
    "weakness": "weakness",
    "breathless": "breathlessness",
    "cannot breathe": "breathlessness",
    "shortness of breath": "breathlessness",
    "short of breath": "breathlessness",
    "cough": "cough",
    "coughing": "cough",
    "runny nose": "runny nose",
    "sore throat": "sore throat",
    "throat pain": "sore throat",
    "ear pain": "ear pain",
    "earache": "ear pain",
    "eye pain": "eye pain",
    "sore eyes": "eye pain",
    "vomiting": "vomiting",
    "vomit": "vomiting",
    "nausea": "vomiting",
    "diarrhoea": "diarrhoea",
    "diarrhea": "diarrhoea",
    "watery stool": "diarrhoea",
    "no appetite": "no appetite",
    "cannot eat": "no appetite",
    "thirsty": "dehydration",
    "cannot drink": "dehydration",
    "bleeding": "bleeding",
    "skin rash": "skin rash",
    "rash": "skin rash",
    "swollen": "swelling",
    "swelling": "swelling",
    "broken bone": "fracture",
    "fracture": "fracture",
    "knee pain": "knee pain",
    "back pain": "back pain",
    "dizzy": "dizziness",
    "dizziness": "dizziness",
    "cannot see": "vision problem",
    "cannot hear": "hearing problem",
    "anxious": "anxiety",
    "scared": "anxiety",
    "sad": "depression",
    "depressed": "depression",
}

# ── Body location keywords ────────────────────────────────────────────────────
BODY_LOCATIONS = [
    "head", "neck", "throat", "chest", "stomach", "abdomen", "back",
    "knee", "leg", "arm", "shoulder", "ear", "eye", "nose", "skin",
    "foot", "hand", "wrist", "ankle", "hip", "groin", "whole body",
]

# ── Medication keywords ───────────────────────────────────────────────────────
MEDICATION_KEYWORDS = [
    "panadol", "paracetamol", "ibuprofen", "aspirin", "amoxicillin",
    "antibiotic", "tablet", "medicine", "medication", "pill", "injection",
    "cream", "spray", "inhaler", "ventolin", "metformin", "insulin",
]

# ── Severity rules ────────────────────────────────────────────────────────────
SEVERE_KEYWORDS = [
    "cannot breathe", "breathless", "chest pain", "bleeding", "unconscious",
    "collapsed", "broken bone", "fracture", "severe", "emergency", "urgent",
    "very bad", "extremely", "djama-wuku", "naraka-djorra", "dhu-wuku",
]
MODERATE_KEYWORDS = [
    "moderate", "quite bad", "getting worse", "few days", "vomiting",
    "diarrhoea", "fever", "cannot eat", "cannot drink", "swollen",
]


# ── Core extraction function ──────────────────────────────────────────────────

def extract_fields(
    raw_text: str,
    age: Optional[int] = None,
    gender: Optional[str] = None,
    days: Optional[int] = None,
    medication_taken: Optional[str] = None,
    severity_score: Optional[int] = None,
) -> dict:
    """
    Extract all structured fields from raw symptom text.
    Optional fields can be passed in directly from form inputs.
    Returns a dict ready to be written as a CSV row.
    """
    text = raw_text.strip().lower()

    # 1. Translate Yolŋu words first
    translated = text
    for yolngu, english in YOLNGU_DICT.items():
        translated = translated.replace(yolngu, english)

    # 2. Extract symptoms
    found_symptoms = []
    for keyword, label in SYMPTOM_KEYWORDS.items():
        if keyword in translated and label not in found_symptoms:
            found_symptoms.append(label)

    # 3. Extract days mentioned (e.g. "3 days", "two days")
    if days is None:
        day_match = re.search(
            r'(\d+|one|two|three|four|five|six|seven)\s*day', translated
        )
        if day_match:
            word = day_match.group(1)
            word_map = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7}
            days = int(word) if word.isdigit() else word_map.get(word, None)

    # 4. Extract body location
    body_location = None
    for loc in BODY_LOCATIONS:
        if loc in translated:
            body_location = loc
            break

    # 5. Extract medication
    if medication_taken is None:
        meds_found = [m for m in MEDICATION_KEYWORDS if m in translated]
        medication_taken = ", ".join(meds_found) if meds_found else "none"

    # 6. Extract age from text if not provided
    if age is None:
        age_match = re.search(r'(\d+)\s*(year|yr)', translated)
        if age_match:
            age = int(age_match.group(1))

    # 7. Extract gender from text if not provided
    if gender is None:
        if any(w in translated for w in ["male", "man", "boy", "he", "his"]):
            gender = "male"
        elif any(w in translated for w in ["female", "woman", "girl", "she", "her"]):
            gender = "female"
        else:
            gender = "unknown"

    # 8. Auto severity score (1-10) if not provided
    if severity_score is None:
        score = 3  # default low
        if any(k in translated for k in SEVERE_KEYWORDS):
            score = 8
        elif any(k in translated for k in MODERATE_KEYWORDS):
            score = 5
        severity_score = score

    # 9. Derive target label from severity score
    if severity_score >= 7:
        target = "severe"
    elif severity_score >= 4:
        target = "moderate"
    else:
        target = "mild"

    # 10. Other body parts (anything not in primary location)
    other_body_part = None
    all_locations = [loc for loc in BODY_LOCATIONS if loc in translated]
    if len(all_locations) > 1:
        other_body_part = ", ".join(all_locations[1:])

    return {
        "symptom_text": raw_text.strip(),
        "translated_text": translated.strip(),
        "symptoms": "; ".join(found_symptoms) if found_symptoms else "unknown",
        "days": days,
        "severity_score": severity_score,
        "medication_taken": medication_taken,
        "other_body_part": other_body_part,
        "age": age,
        "gender": gender,
        "body_location": body_location,
        "target": target,
    }