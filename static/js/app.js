const sourceLanguage = document.getElementById("sourceLanguage");
const symptomText    = document.getElementById("symptomText");
const translateBtn   = document.getElementById("translateBtn");
const triageBtn      = document.getElementById("triageBtn");
const voiceBtn       = document.getElementById("voiceBtn");

// ── English Voice Recognition ─────────────────────────────────────────────
voiceBtn.addEventListener("click", () => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
        alert("Speech recognition not supported. Please use Chrome.");
        return;
    }
    const recognition = new SpeechRecognition();
    recognition.lang = "en-AU";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    voiceBtn.textContent = "🎙️ Listening...";
    voiceBtn.disabled = true;
    recognition.start();

    recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        symptomText.value = transcript;
        voiceBtn.textContent = "🎤 Start Voice Input";
        voiceBtn.disabled = false;
        if (sourceLanguage.value !== "english") {
            autoTranslate(transcript);
        }
    };

    recognition.onerror = (event) => {
        alert("Voice error: " + event.error + ". Please try again.");
        voiceBtn.textContent = "🎤 Start Voice Input";
        voiceBtn.disabled = false;
    };

    recognition.onend = () => {
        voiceBtn.textContent = "🎤 Start Voice Input";
        voiceBtn.disabled = false;
    };
});

async function autoTranslate(text) {
    try {
        const res = await fetch("/api/translate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text, source_language: sourceLanguage.value }),
        });
        const data = await res.json();
        if (data.english_text) {
            document.getElementById("englishOutput").textContent = data.english_text;
            renderSymptoms(data.recognized_symptoms || []);
        }
    } catch (e) {
        console.error("Auto-translate error:", e);
    }
}

// ── Translate Button ──────────────────────────────────────────────────────
translateBtn.addEventListener("click", async () => {
    const text = symptomText.value.trim();
    if (!text) { alert("Please enter or speak symptoms first."); return; }
    try {
        const res = await fetch("/api/translate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ text: text, source_language: sourceLanguage.value }),
        });
        const data = await res.json();
        document.getElementById("englishOutput").textContent = data.english_text || text;
        renderSymptoms(data.recognized_symptoms || []);
    } catch (e) {
        alert("Translation error. Is the server running?");
    }
});

// ── Triage Button ─────────────────────────────────────────────────────────
triageBtn.addEventListener("click", async () => {
    const text = symptomText.value.trim();
    if (!text) { alert("Please enter or speak symptoms first."); return; }
    try {
        const res = await fetch("/api/triage", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                text: text,
                source_language: sourceLanguage.value,
                age_group: document.getElementById("ageGroup").value,
            }),
        });
        const data = await res.json();
        if (data.error) { alert(data.error); return; }

        document.getElementById("englishOutput").textContent = data.english_text || text;
        renderSymptoms(data.recognized_symptoms || []);

        const target = data.nlp ? data.nlp.target : "mild";
        const severityEl = document.getElementById("severityOutput");
        severityEl.textContent = target ? target.toUpperCase() : "—";
        severityEl.className = "severity " + (target || "mild");

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
                ["Symptoms",       data.nlp.symptoms],
                ["Days",           data.nlp.days ?? "—"],
                ["Severity Score", data.nlp.severity_score + " / 10"],
                ["Medication",     data.nlp.medication_taken],
                ["Body Location",  data.nlp.body_location ?? "—"],
                ["Other Parts",    data.nlp.other_body_part ?? "—"],
                ["Age",            data.nlp.age ?? "—"],
                ["Gender",         data.nlp.gender],
                ["Target",         data.nlp.target ? data.nlp.target.toUpperCase() : "—"],
            ];
            let html = "<table style='width:100%;border-collapse:collapse;margin-top:10px'>";
            fields.forEach(([label, value]) => {
                html += "<tr><td style='padding:4px 8px;font-weight:bold;color:#555'>" + label + "</td><td style='padding:4px 8px'>" + value + "</td></tr>";
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

    } catch (e) {
        alert("Triage error. Is the server running?");
    }
});

function renderSymptoms(symptoms) {
    const container = document.getElementById("symptomTags");
    if (!container) return;
    container.innerHTML = symptoms.length
        ? symptoms.map(s => "<span class='tag'>" + s + "</span>").join(" ")
        : "<em>None detected</em>";
}

// ── Yolngu Matha Voice Button (NEW) ──────────────────────────────────────
const yolnguVoiceBtn = document.getElementById("yolnguVoiceBtn");
if (yolnguVoiceBtn) {
    yolnguVoiceBtn.addEventListener("click", () => {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRecognition) {
            alert("Speech recognition not supported. Please use Chrome.");
            return;
        }
        const recognition = new SpeechRecognition();
        recognition.lang = "en-AU";
        recognition.interimResults = false;
        recognition.maxAlternatives = 1;

        yolnguVoiceBtn.textContent = "🎙️ Listening for Yolŋu Matha...";
        yolnguVoiceBtn.disabled = true;
        recognition.start();

        recognition.onresult = async (event) => {
            const spoken = event.results[0][0].transcript;
            symptomText.value = spoken;
            yolnguVoiceBtn.textContent = "🎙️ Speak in Yolŋu Matha";
            yolnguVoiceBtn.disabled = false;

            try {
                const res = await fetch("/api/translate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ text: spoken, source_language: "yolngu" }),
                });
                const data = await res.json();
                if (data.english_text) {
                    document.getElementById("englishOutput").textContent = data.english_text;
                    renderSymptoms(data.recognized_symptoms || []);
                }
            } catch (e) {
                console.error("Yolngu translate error:", e);
            }
        };

        recognition.onerror = (event) => {
            alert("Voice error: " + event.error);
            yolnguVoiceBtn.textContent = "🎙️ Speak in Yolŋu Matha";
            yolnguVoiceBtn.disabled = false;
        };

        recognition.onend = () => {
            yolnguVoiceBtn.textContent = "🎙️ Speak in Yolŋu Matha";
            yolnguVoiceBtn.disabled = false;
        };
    });
}