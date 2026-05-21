class SimpleTranslator:
    def __init__(self, translation_file=None):
        self.dictionary = {
            "buku-dhukarr": "head pain / headache", "butu-dhukarr": "stomach pain",
            "guku-dhukarr": "chest pain", "dhukal-dhukarr": "body pain / aches all over",
            "dharpa-wuku": "fever / feeling hot", "bulu-wuku": "feeling cold / chills",
            "djama-wirrika": "feeling very tired / fatigue", "wirrika": "feeling weak",
            "dhu-wuku": "cannot breathe / breathlessness", "guku-guku": "cough",
            "nuru-gapu": "runny nose", "laka-dhukarr": "sore throat",
            "dhakay-dhukarr": "ear pain", "mel-dhukarr": "eye pain / sore eyes",
            "gulktji": "vomiting", "gapu-djorra": "diarrhoea",
            "nha-wirrika": "no appetite / cannot eat", "yunggurr-wirrika": "very thirsty / cannot drink",
            "gulan-wuku": "bleeding", "malk-djorra": "skin rash",
            "djorra-wuku": "swollen", "naraka-djorra": "broken bone / fracture",
            "muu-dhukarr": "knee pain", "maru-dhukarr": "back pain",
            "buku-wuku": "feeling dizzy", "mel-wirrika": "cannot see properly",
            "winya-wirrika": "cannot hear properly", "dhukarr-buku": "feeling anxious / scared",
            "dhipinu": "feeling sad / depressed", "gutha-dhakay": "child is sick",
            "djambatj-dhakay": "elder is sick", "gumurr-dhawu": "pregnant woman needs help",
            "rom-djama": "need medicine", "djama-wuku": "need help urgently",
            "dhipinu-wirrika": "feeling better", "marrtjin": "not feeling well",
            "wayin": "sick / unwell", "ga": "and", "rua": "two", "wanggany": "one",
            "dhuwala": "days", "gurrung": "body", "yothu": "child", "nhe": "i am",
        }
        self.known_symptoms = [
            "headache","head pain","stomach pain","chest pain","body pain","fever",
            "chills","fatigue","tired","weak","breathless","cough","runny nose",
            "sore throat","ear pain","eye pain","vomiting","diarrhoea","no appetite",
            "thirsty","bleeding","skin rash","swollen","back pain","knee pain","dizzy",
            "anxious","sad","cold","fracture","cannot breathe","shortness of breath",
            "cannot see","cannot hear","not feeling well","unwell","not okay",
            "not feeling okay","feel bad","feeling bad","feel sick","feeling sick",
            "hard to breathe","hard to breath","difficulty breathing","body aches",
            "body heating","throwing up","loss of taste","shivering","very tired",
            "very weak","heating","lot of cough","tastebuds",
        ]

    def translate(self, text):
        full = text.strip().lower()
        if full in self.dictionary: return self.dictionary[full]
        translated = full
        for y, e in self.dictionary.items():
            translated = translated.replace(y, e)
        return translated

    def extract_symptoms(self, text):
        found = []
        text_lower = text.strip().lower()
        for s in self.known_symptoms:
            if s in text_lower and s not in found:
                found.append(s)
        return found
