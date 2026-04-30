class SimpleTranslator:
    def __init__(self, translation_file=None):
        self.dictionary = {
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
            "laka-dhukarr": "sore throat",
            "dhakay-dhukarr": "ear pain",
            "mel-dhukarr": "eye pain",
            "gulktji": "vomiting",
            "gapu-djorra": "diarrhoea",
            "nha-wirrika": "no appetite",
            "yunggurr-wirrika": "dehydration",
            "gulan-wuku": "bleeding",
            "malk-djorra": "skin rash",
            "djorra-wuku": "swollen",
            "naraka-djorra": "fracture",
            "muu-dhukarr": "knee pain",
            "maru-dhukarr": "back pain",
            "buku-wuku": "dizzy",
            "mel-wirrika": "cannot see",
            "winya-wirrika": "cannot hear",
            "dhukarr-buku": "anxious",
            "dhipinu": "sad",
            "djama-wuku": "emergency",
        }
        self.known_symptoms = [
            "headache", "head pain", "stomach pain", "chest pain",
            "body pain", "fever", "chills", "fatigue", "tired",
            "weak", "breathless", "cough", "runny nose", "sore throat",
            "ear pain", "eye pain", "vomiting", "diarrhoea", "no appetite",
            "thirsty", "bleeding", "skin rash", "swollen", "back pain",
            "knee pain", "dizzy", "anxious", "sad", "cold", "fracture",
            "cannot breathe", "shortness of breath", "cannot see", "cannot hear",
            "not feeling well", "unwell", "tastebuds", "heating", "lot of cough",
            "not okay", "not feeling okay", "feel bad", "feeling bad",
            "feel sick", "feeling sick", "something wrong", "not good",
            "hard to breathe", "hard to breath", "difficulty breathing",
            "body aches", "body heating", "throwing up", "loss of taste",
            "runny nose", "shivering", "very tired", "very weak",
            "pain in chest", "pain in stomach", "pain in head", "pain in back",
        ]

    def translate(self, text):
        full = text.strip().lower()
        if full in self.dictionary:
            return self.dictionary[full]
        translated = full
        for yolngu, english in self.dictionary.items():
            translated = translated.replace(yolngu, english)
        return translated

    def extract_symptoms(self, text):
        found = []
        text_lower = text.strip().lower()
        for symptom in self.known_symptoms:
            if symptom in text_lower and symptom not in found:
                found.append(symptom)
        return found
