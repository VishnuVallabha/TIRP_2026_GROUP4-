package com.example.saca;

public class AppLanguage {

    public static boolean isYolngu(String language) {
        return language != null &&
                (language.equalsIgnoreCase("yolngu")
                        || language.equalsIgnoreCase("yolŋu")
                        || language.equalsIgnoreCase("yolnu"));
    }

    public static String bilingual(String language, String yolngu, String english) {
        if (isYolngu(language)) return yolngu + "\n" + english;
        return english;
    }

    public static String back(String language) {
        return bilingual(language, "← Roŋiyirr", "← Back");
    }

    public static String next(String language) {
        return bilingual(language, "Ŋäthil →", "NEXT →");
    }

    public static String analyse(String language) {
        return bilingual(language, "Dhäwu nhäma →", "ANALYSE →");
    }

    public static String methodTitle(String language) {
        return bilingual(language, "MÄRR DHÄRUK YOLŊUNHA", "SYMPTOM CLASSIFICATION");
    }

    public static String methodSubtitle(String language) {
        return bilingual(language, "Nhaltjan yolŋu matha djäma?", "How would you like to identify your symptom?");
    }

    public static String symptomIdentification(String language) {
        return bilingual(language, "🩺 01. YIRRA DHÄRUK", "🩺 01. SYMPTOM IDENTIFICATION");
    }

    public static String symptomIdSub1(String language) {
        return bilingual(language, "Yirra dhäruk märr-yuŋupuy", "Tap a body part, then choose your symptom");
    }

    public static String symptomIdSub2(String language) {
        return bilingual(language, "Yolŋu matha djäma", "Visual selection — best for all users");
    }

    public static String speak(String language) {
        return bilingual(language, "🎤 02. ŊUNHI DJÄMA", "🎤 02. SPEAK YOUR SYMPTOM");
    }

    public static String speakSub1(String language) {
        return bilingual(language, "Ŋunhi Djäma — NLP", "Say your symptom — NLP will identify it");
    }

    public static String speakSub2(String language) {
        return bilingual(language, "NLP module — English ga Yolŋu matha", "Powered by NLP  ·  English & Yolŋu Matha");
    }

    public static String type(String language) {
        return bilingual(language, "⌨ 03. ŊUNHI MÄRR", "⌨ 03. TYPE YOUR SYMPTOM");
    }

    public static String typeSub1(String language) {
        return bilingual(language, "Ŋunhi märr — NLP dhäruk", "Type your symptom — NLP will classify it");
    }

    public static String typeSub2(String language) {
        return bilingual(language, "NLP module — nhakun djäma", "Powered by keyword NLP  ·  English & Yolŋu Matha");
    }

    public static String selectBodyPart(String language) {
        return bilingual(language, "Rumbal nhäma", "Select Body Part");
    }

    public static String startQuestions(String language) {
        return bilingual(language, "Dhäwu gaḏaman →", "START QUESTIONS →");
    }

    // Body part labels
    public static String head(String language)      { return bilingual(language, "🧠 Mulkurr",    "🧠 Head"); }
    public static String throat(String language)    { return bilingual(language, "🗣 Gorrmur",    "🗣 Throat"); }
    public static String chest(String language)     { return bilingual(language, "❤ Birrka",     "❤ Chest"); }
    public static String stomach(String language)   { return bilingual(language, "◎ Bäyŋu",      "◎ Stomach"); }
    public static String arms(String language)      { return bilingual(language, "💪 Maḻa",       "💪 Arms"); }
    public static String legs(String language)      { return bilingual(language, "🦵 Luku",       "🦵 Legs"); }
    public static String backBody(String language)  { return bilingual(language, "🦴 Gäna",       "🦴 Back"); }
    public static String wholeBody(String language) { return bilingual(language, "🧍 Rumbal",     "🧍 Whole Body"); }

    // Result titles — EXACT strings from desktop constants.py CFG dict
    public static String mildTitle(String language) {
        return bilingual(language, "😊 Märr Mäkitj", "😊 MILD");
    }

    public static String moderateTitle(String language) {
        return bilingual(language, "😟 Märr Djuy'yun", "😟 MODERATE");
    }

    public static String severeTitle(String language) {
        return bilingual(language, "🚨 Märr Djorra'", "🚨 EMERGENCY");
    }

    // Result advice — exact from desktop
    public static String mildAdvice(String language) {
        return bilingual(language,
                "Wäŋaŋur nhina. Räl märr-yuŋupuy.",
                "Rest at home. Monitor your symptoms.");
    }

    public static String moderateAdvice(String language) {
        return bilingual(language,
                "Clinic-lil marrtji — 24 ŋärra räl.",
                "Visit the Yirrkala clinic within 24 hours.");
    }

    public static String severeAdvice(String language) {
        return bilingual(language,
                "000 guḻkuŋa. Yaka baḻanyara.",
                "Call 000 immediately. Do not wait.");
    }

    public static String yourResult(String language) {
        return bilingual(language, "Nhumaŋgal märr", "Your Result");
    }

    public static String saveReport(String language) {
        return bilingual(language, "💾 Dhäwu marŋgithirr", "💾 SAVE REPORT");
    }

    public static String startOver(String language) {
        return bilingual(language, "↩ Yaka gaḏaman", "↩ START OVER");
    }

    // Patient info screen
    public static String aboutYou(String language) {
        return bilingual(language, "NHUMAŊGAL DHÄWU", "ABOUT YOU");
    }

    public static String howOld(String language) {
        return bilingual(language, "Nhuma ŋänha ŋärra?", "How old are you?");
    }

    public static String yourGender(String language) {
        return bilingual(language, "Nhuma wäŋa?", "What is your gender?");
    }
}
