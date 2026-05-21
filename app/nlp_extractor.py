import re

YOLNGU_PHRASES = {
    "buku-dhukarr": "head pain headache",
    "butu-dhukarr": "stomach pain",
    "guku-dhukarr": "chest pain",
    "dhukal-dhukarr": "body pain aches all over",
    "dharpa-wuku": "fever feeling hot body heating",
    "bulu-wuku": "feeling cold chills",
    "djama-wirrika": "feeling very tired fatigue no energy",
    "wirrika": "feeling weak",
    "dhu-wuku": "cannot breathe breathlessness",
    "guku-guku": "cough coughing",
    "nuru-gapu": "runny nose",
    "laka-dhukarr": "sore throat",
    "dhakay-dhukarr": "ear pain",
    "mel-dhukarr": "eye pain sore eyes",
    "gulktji": "vomiting being sick",
    "gapu-djorra": "diarrhoea watery stool",
    "nha-wirrika": "cannot eat no appetite",
    "yunggurr-wirrika": "cannot drink very thirsty",
    "gulan-wuku": "bleeding",
    "malk-djorra": "skin rash",
    "djorra-wuku": "swollen swelling",
    "naraka-djorra": "broken bone fracture",
    "muu-dhukarr": "knee pain",
    "maru-dhukarr": "back pain",
    "buku-wuku": "feeling dizzy dizziness",
    "mel-wirrika": "cannot see properly",
    "winya-wirrika": "cannot hear properly",
    "dhukarr-buku": "feeling scared anxious worried",
    "dhipinu": "feeling sad depressed",
    "gutha-dhakay": "child is sick",
    "djambatj-dhakay": "elder is sick",
    "gumurr-dhawu": "pregnant woman needs help",
    "rom-djama": "need medicine",
    "djama-wuku": "need help urgently emergency",
    "dhipinu-wirrika": "feeling better recovered",
    "marrtjin": "not feeling well",
    "wayin": "sick unwell",
    "nhe": "i am", "ga": "and", "rua": "two",
    "wanggany": "one", "dhuwala": "days",
    "gurrung": "body", "yothu": "child",
}

SYMPTOM_KEYWORDS = {
    "headache": "headache", "head pain": "headache", "head hurts": "headache",
    "stomach pain": "stomach pain", "stomach ache": "stomach pain",
    "tummy pain": "stomach pain", "stomach hurts": "stomach pain",
    "chest pain": "chest pain", "chest tight": "chest pain",
    "body pain": "body pain", "body ache": "body pain",
    "body aches": "body pain", "body heating": "fever",
    "fever": "fever", "feeling hot": "fever", "temperature": "fever",
    "heating": "fever", "hot": "fever", "sweating": "fever",
    "chills": "chills", "feeling cold": "chills", "shivering": "chills",
    "tired": "fatigue", "fatigue": "fatigue", "exhausted": "fatigue",
    "no energy": "fatigue", "very tired": "fatigue",
    "weak": "weakness", "very weak": "weakness", "no strength": "weakness",
    "breathless": "breathlessness", "cannot breathe": "breathlessness",
    "cant breathe": "breathlessness", "hard to breath": "breathlessness",
    "hard to breathe": "breathlessness", "difficulty breathing": "breathlessness",
    "shortness of breath": "breathlessness",
    "cough": "cough", "coughing": "cough", "lot of cough": "cough",
    "runny nose": "runny nose", "nose running": "runny nose",
    "sore throat": "sore throat", "throat pain": "sore throat",
    "ear pain": "ear pain", "earache": "ear pain",
    "eye pain": "eye pain", "sore eyes": "eye pain",
    "vomiting": "vomiting", "nausea": "vomiting", "throwing up": "vomiting",
    "diarrhoea": "diarrhoea", "diarrhea": "diarrhoea",
    "no appetite": "no appetite", "cannot eat": "no appetite",
    "tastebuds": "no appetite", "loss of taste": "no appetite",
    "thirsty": "dehydration", "cannot drink": "dehydration",
    "bleeding": "bleeding",
    "skin rash": "skin rash", "rash": "skin rash",
    "swollen": "swelling", "fracture": "fracture", "broken bone": "fracture",
    "knee pain": "knee pain", "back pain": "back pain",
    "dizzy": "dizziness", "dizziness": "dizziness",
    "cannot see": "vision problem", "cannot hear": "hearing problem",
    "anxious": "anxiety", "scared": "anxiety", "worried": "anxiety",
    "sad": "depression", "depressed": "depression",
    "not feeling well": "unwell", "not feeling okay": "unwell",
    "not feeling good": "unwell", "not okay": "unwell",
    "feel bad": "unwell", "feeling bad": "unwell",
    "feel sick": "unwell", "feeling sick": "unwell",
    "something is wrong": "unwell", "unwell": "unwell",
    "i am sick": "unwell", "i am ill": "unwell",
}

BODY_LOCATIONS = ["head","neck","throat","chest","stomach","abdomen","back",
    "knee","leg","arm","shoulder","ear","eye","nose","skin",
    "foot","hand","wrist","ankle","hip","whole body","body"]

MEDICATION_KEYWORDS = ["panadol","paracetamol","ibuprofen","aspirin","amoxicillin",
    "antibiotic","tablet","medicine","medication","pill","injection","cream","inhaler","ventolin"]

SEVERE_KEYWORDS = ["cannot breathe","breathless","chest pain","bleeding",
    "unconscious","collapsed","fracture","broken bone","severe","emergency",
    "urgent","very bad","hard to breathe","difficulty breathing"]

MODERATE_KEYWORDS = ["vomiting","diarrhoea","fever","cannot eat","cannot drink",
    "swollen","few days","lot of cough","two day","three day","body heating","throwing up"]


def translate_to_english(text):
    result = text.strip().lower()
    for yolngu, english in YOLNGU_PHRASES.items():
        result = result.replace(yolngu, english)
    return result.strip()


def understand_natural_sentence(text):
    t = text.strip().lower()
    clues = []
    days_found = None
    duration = re.search(
        r"(since|from|for|past|last)\s*(a\s*)?(few|couple|\d+|one|two|three|four|five|six|seven)\s*(day|days|week|weeks)", t)
    if duration:
        w = duration.group(3)
        wmap = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"few":3,"couple":2}
        days_found = int(w) if w.isdigit() else wmap.get(w, 2)
    unwell_phrases = ["not okay","not feeling okay","not feeling well","not feeling good",
        "feel bad","feeling bad","not good","not right","something wrong","something is wrong",
        "not myself","i am sick","i am ill","i am unwell","not well","not doing well",
        "feeling terrible","feeling awful"]
    for phrase in unwell_phrases:
        if phrase in t:
            clues.append("unwell")
            break
    return clues, days_found


def extract_fields(raw_text, age=None, gender=None, days=None,
                   medication_taken=None, severity_score=None):
    text = raw_text.strip().lower()
    translated = translate_to_english(text)
    natural_clues, natural_days = understand_natural_sentence(translated)
    if days is None and natural_days:
        days = natural_days
    found_symptoms = []
    for keyword, label in SYMPTOM_KEYWORDS.items():
        if keyword in translated and label not in found_symptoms:
            found_symptoms.append(label)
    for clue in natural_clues:
        if clue not in found_symptoms:
            found_symptoms.append(clue)
    if days is None:
        m = re.search(r"(few|\d+|one|two|three|four|five|six|seven)\s*(day|days)", translated)
        if m:
            w = m.group(1)
            wmap = {"one":1,"two":2,"three":3,"four":4,"five":5,"six":6,"seven":7,"few":3}
            days = int(w) if w.isdigit() else wmap.get(w)
    body_location = next((l for l in BODY_LOCATIONS if l in translated), None)
    all_locs = [l for l in BODY_LOCATIONS if l in translated]
    other_body_part = ", ".join(all_locs[1:]) if len(all_locs) > 1 else None
    if medication_taken is None:
        meds = [m for m in MEDICATION_KEYWORDS if m in translated]
        medication_taken = ", ".join(meds) if meds else "none"
    if age is None:
        am = re.search(r"(\d+)\s*(year|yr)", translated)
        if am:
            age = int(am.group(1))
    if gender is None:
        if any(w in translated for w in ["male","man","boy"]):
            gender = "male"
        elif any(w in translated for w in ["female","woman","girl"]):
            gender = "female"
        else:
            gender = "unknown"
    if severity_score is None:
        if any(k in translated for k in SEVERE_KEYWORDS):
            severity_score = 8
        elif any(k in translated for k in MODERATE_KEYWORDS):
            severity_score = 5
        else:
            severity_score = 3
    target = "severe" if severity_score >= 7 else "moderate" if severity_score >= 4 else "mild"
    return {
        "symptom_text": raw_text.strip(),
        "translated_text": translated.strip(),
        "symptoms": "; ".join(found_symptoms) if found_symptoms else "unknown",
        "days": days, "severity_score": severity_score,
        "medication_taken": medication_taken, "other_body_part": other_body_part,
        "age": age, "gender": gender, "body_location": body_location, "target": target,
    }
