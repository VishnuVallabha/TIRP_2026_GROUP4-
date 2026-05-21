import os
from pathlib import Path

def get_groq_key():
    env_path = Path(".env")
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("GROQ_API_KEY="):
                return line.split("=", 1)[1].strip()
    return os.getenv("GROQ_API_KEY", "")

def translate_english_to_yolngu(text):
    """Basic dictionary reverse translate for simple words."""
    ENGLISH_TO_YOLNGU = {
        "i am not feeling well": "nhe marrtjin",
        "i am not feeling okay": "nhe marrtjin",
        "not feeling well": "marrtjin",
        "not feeling okay": "marrtjin",
        "not feeling good": "marrtjin",
        "not okay": "marrtjin",
        "feel bad": "marrtjin",
        "i am sick": "nhe wayin",
        "i have": "nhe",
        "i am having": "nhe",
        "i am": "nhe",
        "past 2 days": "rua dhuwala",
        "past two days": "rua dhuwala",
        "two days": "rua dhuwala",
        "2 days": "rua dhuwala",
        "3 days": "warray dhuwala",
        "three days": "warray dhuwala",
        "head pain": "buku-dhukarr", "headache": "buku-dhukarr",
        "stomach pain": "butu-dhukarr",
        "chest pain": "guku-dhukarr",
        "body pain": "dhukal-dhukarr",
        "fever": "dharpa-wuku", "feeling hot": "dharpa-wuku", "hot": "dharpa-wuku",
        "cold": "bulu-wuku", "chills": "bulu-wuku",
        "tired": "djama-wirrika", "fatigue": "djama-wirrika", "very tired": "djama-wirrika",
        "weak": "wirrika", "weakness": "wirrika",
        "cannot breathe": "dhu-wuku", "breathless": "dhu-wuku",
        "hard to breathe": "dhu-wuku",
        "cough": "guku-guku", "runny nose": "nuru-gapu",
        "sore throat": "laka-dhukarr", "ear pain": "dhakay-dhukarr",
        "eye pain": "mel-dhukarr", "vomiting": "gulktji", "nausea": "gulktji",
        "diarrhoea": "gapu-djorra", "diarrhea": "gapu-djorra",
        "no appetite": "nha-wirrika", "cannot eat": "nha-wirrika",
        "thirsty": "yunggurr-wirrika", "bleeding": "gulan-wuku",
        "skin rash": "malk-djorra", "swollen": "djorra-wuku",
        "fracture": "naraka-djorra", "knee pain": "muu-dhukarr",
        "back pain": "maru-dhukarr", "dizzy": "buku-wuku",
        "anxious": "dhukarr-buku", "scared": "dhukarr-buku",
        "sad": "dhipinu", "depressed": "dhipinu",
        "unwell": "marrtjin", "sick": "wayin",
        "and": "ga", "body": "gurrung", "child": "yothu",
        "i need medicine": "rom-djama", "emergency": "djama-wuku",
        "feeling better": "dhipinu-wirrika",
        "cannot see": "mel-wirrika", "cannot hear": "winya-wirrika",
    }
    words = text.strip().lower().split()
    output_parts = []
    while words:
        matched = False
        for length in range(min(5, len(words)), 0, -1):
            phrase = " ".join(words[:length])
            if phrase in ENGLISH_TO_YOLNGU:
                val = ENGLISH_TO_YOLNGU[phrase]
                if val:
                    output_parts.append(val)
                words = words[length:]
                matched = True
                break
        if not matched:
            output_parts.append(words[0])
            words = words[1:]
    return " ".join(output_parts)


def ai_understand_sentence(text):
    """
    Use Groq AI to understand ANY natural sentence and extract:
    - English meaning
    - Yolngu Matha translation
    - Symptoms list
    """
    try:
        from groq import Groq
        client = Groq(api_key=get_groq_key())
        
        prompt = f"""You are a medical translator for Yolngu Matha, an Indigenous Australian language spoken in Yirrkala.

A patient said: "{text}"

Your job:
1. Understand what symptoms they are describing even if they say it in a natural conversational way
2. Translate the meaning into simple clear English
3. Translate into Yolngu Matha using these words:
   - buku-dhukarr = headache/head pain
   - butu-dhukarr = stomach pain  
   - guku-dhukarr = chest pain
   - dhukal-dhukarr = body pain/aches
   - dharpa-wuku = fever/feeling hot
   - bulu-wuku = feeling cold/chills
   - djama-wirrika = very tired/fatigue
   - wirrika = feeling weak
   - dhu-wuku = cannot breathe
   - guku-guku = cough
   - nuru-gapu = runny nose
   - laka-dhukarr = sore throat
   - gulktji = vomiting
   - gapu-djorra = diarrhoea
   - nha-wirrika = no appetite/cannot eat
   - marrtjin = not feeling well
   - wayin = sick/unwell
   - ga = and
   - rua dhuwala = two days
   - wanggany dhuwala = one day
   - nhe = I am

Respond ONLY in this exact JSON format (no other text):
{{
  "english": "clear English description of all symptoms",
  "yolngu": "Yolngu Matha translation using the words above",
  "symptoms": ["symptom1", "symptom2"],
  "days": null or number,
  "severity": "mild" or "moderate" or "severe"
}}"""

        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=300,
        )
        
        import json
        result = json.loads(response.choices[0].message.content.strip())
        return result
        
    except Exception as e:
        return None
