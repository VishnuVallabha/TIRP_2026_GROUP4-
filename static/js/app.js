const symptomText  = document.getElementById("symptomText");
const speakBtn     = document.getElementById("speakBtn");
const translateBtn = document.getElementById("translateBtn");
const triageBtn    = document.getElementById("triageBtn");

let currentYolngu  = "";
let currentEnglish = "";

// ── Update all language displays ─────────────────────────────────────────
function updateBothLanguages(yolngu, english) {
    currentYolngu  = yolngu  || "";
    currentEnglish = english || "";
    document.getElementById("yolnguDisplay").textContent  = yolngu  || "—";
    document.getElementById("englishDisplay").textContent = english || "—";
    document.getElementById("staffYolngu").textContent    = yolngu  || "—";
    document.getElementById("englishOutput").textContent  = english || "—";
}

// ── Text-to-speech ────────────────────────────────────────────────────────
function speakText(lang) {
    if (!window.speechSynthesis) { alert("Use Chrome for text-to-speech."); return; }
    window.speechSynthesis.cancel();
    const text = lang === "english" ? currentEnglish : currentYolngu;
    if (!text || text === "—") { alert("Nothing to read. Please translate first."); return; }
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang  = "en-AU";
    utterance.rate  = lang === "yolngu" ? 0.8 : 1.0;
    utterance.pitch = 1.0;
    window.speechSynthesis.speak(utterance);
}

// ── Auto read both after voice input ────────────────────────────────────
function autoReadBoth(yolngu, english) {
    if (!window.speechSynthesis) return;
    window.speechSynthesis.cancel();
    const eng = new SpeechSynthesisUtterance("In English: " + english);
    eng.lang = "en-AU"; eng.rate = 1.0;
    const yol = new SpeechSynthesisUtterance("In Yolngu Matha: " + yolngu);
    yol.lang = "en-AU"; yol.rate = 0.8;
    eng.onend = () => setTimeout(() => window.speechSynthesis.speak(yol), 600);
    window.speechSynthesis.speak(eng);
}

// ── Detect Yolngu or English ─────────────────────────────────────────────
function isYolngu(text) {
    const markers = ["dhukarr","wuku","wirrika","guku","butu","buku","dharpa",
        "bulu","djama","nuru","laka","dhakay","gulktji","gapu","nha","yunggurr",
        "gulan","malk","djorra","naraka","muu","maru","mel","winya","dhipinu",
        "gutha","djambatj","gumurr","rom","marrtjin","wayin","ga "];
    const lower = text.toLowerCase();
    return markers.some(w => lower.includes(w));
}

// ── Get both translations ────────────────────────────────────────────────
async function getBothTranslations(text) {
    let yolnguText, englishText, symptoms = [];

    if (isYolngu(text)) {
        const res = await fetch("/api/translate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text, source_language: "yolngu" }),
        });
        const data = await res.json();
        yolnguText  = text;
        englishText = data.english_text || text;
        symptoms    = data.recognized_symptoms || [];
    } else {
        const [t, r] = await Promise.all([
            fetch("/api/translate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text, source_language: "english" }),
            }),
            fetch("/api/reverse_translate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ text }),
            }),
        ]);
        const td = await t.json();
        const rd = await r.json();
        englishText = text;
        yolnguText  = rd.yolngu_text || text;
        symptoms    = td.recognized_symptoms || [];
    }
    return { yolnguText, englishText, symptoms };
}

// ── Render symptom tags ──────────────────────────────────────────────────
function renderSymptoms(symptoms) {
    const c = document.getElementById("symptomTags");
    if (!c) return;
    c.innerHTML = symptoms.length
        ? symptoms.map(s => "<span class='tag'>" + s + "</span>").join(" ")
        : "<em>None detected</em>";
}

// ── Voice input ──────────────────────────────────────────────────────────
speakBtn.addEventListener("click", () => {
    const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SR) { alert("Please use Chrome for voice input."); return; }
    const rec = new SR();
    rec.lang = "en-AU";
    rec.interimResults = false;
    rec.maxAlternatives = 1;
    speakBtn.textContent = "🎙️ Listening... speak now";
    speakBtn.disabled = true;
    rec.start();
    rec.onresult = async (e) => {
        const spoken = e.results[0][0].transcript;
        symptomText.value = spoken;
        speakBtn.textContent = "🎤 Speak Your Symptoms";
        speakBtn.disabled = false;
        try {
            const { yolnguText, englishText, symptoms } = await getBothTranslations(spoken);
            updateBothLanguages(yolnguText, englishText);
            renderSymptoms(symptoms);
            autoReadBoth(yolnguText, englishText);
        } catch (err) { console.error(err); }
    };
    rec.onerror = (e) => {
        alert("Voice error: " + e.error);
        speakBtn.textContent = "🎤 Speak Your Symptoms";
        speakBtn.disabled = false;
    };
    rec.onend = () => {
        speakBtn.textContent = "🎤 Speak Your Symptoms";
        speakBtn.disabled = false;
    };
});

// ── Translate button ─────────────────────────────────────────────────────
translateBtn.addEventListener("click", async () => {
    const text = symptomText.value.trim();
    if (!text) { alert("Please type or speak symptoms first."); return; }
    try {
        const { yolnguText, englishText, symptoms } = await getBothTranslations(text);
        updateBothLanguages(yolnguText, englishText);
        renderSymptoms(symptoms);
    } catch (e) { alert("Translation error. Is the server running?"); }
});

// ── Triage button ────────────────────────────────────────────────────────
triageBtn.addEventListener("click", async () => {
    const text = symptomText.value.trim();
    if (!text) { alert("Please type or speak symptoms first."); return; }
    try {
        const { yolnguText, englishText, symptoms } = await getBothTranslations(text);
        updateBothLanguages(yolnguText, englishText);
        renderSymptoms(symptoms);

        const res = await fetch("/api/triage", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                text,
                source_language: isYolngu(text) ? "yolngu" : "english",
                age_group: document.getElementById("ageGroup").value,
            }),
        });
        const data = await res.json();
        if (data.error) { alert(data.error); return; }

        const target = data.nlp ? data.nlp.target : "mild";
        const sev = document.getElementById("severityOutput");
        sev.textContent = target ? target.toUpperCase() : "—";
        sev.className = "severity " + (target || "mild");

        const precautions = {
            severe:   ["Seek emergency care immediately", "Do not leave patient alone", "Call clinic now"],
            moderate: ["Visit clinic within 24 hours", "Rest and drink fluids", "Monitor symptoms closely"],
            mild:     ["Rest at home", "Drink plenty of water", "Return if symptoms worsen"],
        };
        const list = document.getElementById("precautionsList");
        list.innerHTML = "";
        (precautions[target] || precautions.mild).forEach(p => {
            const li = document.createElement("li");
            li.textContent = p;
            list.appendChild(li);
        });

        if (data.nlp) {
            const fields = [
                ["Symptoms", data.nlp.symptoms],
                ["Days", data.nlp.days ?? "—"],
                ["Severity Score", data.nlp.severity_score + " / 10"],
                ["Medication", data.nlp.medication_taken],
                ["Body Location", data.nlp.body_location ?? "—"],
                ["Other Parts", data.nlp.other_body_part ?? "—"],
                ["Age", data.nlp.age ?? "—"],
                ["Gender", data.nlp.gender],
                ["Target", data.nlp.target ? data.nlp.target.toUpperCase() : "—"],
            ];
            let html = "<table style='width:100%;border-collapse:collapse;margin-top:10px'>";
            fields.forEach(([l, v]) => {
                html += "<tr><td style='padding:4px 8px;font-weight:bold;color:#555'>"
                      + l + "</td><td style='padding:4px 8px'>" + v + "</td></tr>";
            });
            html += "</table>";
            let nlpDiv = document.getElementById("nlpFields");
            if (!nlpDiv) {
                nlpDiv = document.createElement("div");
                nlpDiv.id = "nlpFields";
                document.getElementById("precautionsList").parentNode.appendChild(nlpDiv);
            }
            nlpDiv.innerHTML = "<h3>NLP Extracted Fields</h3>" + html;
        }

        if (data.record_id) console.log("Saved record ID:", data.record_id);

    } catch (e) { alert("Triage error. Is the server running?"); }
});