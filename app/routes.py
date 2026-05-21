from __future__ import annotations
from pathlib import Path
from flask import Blueprint, Flask, jsonify, render_template, request, send_file
from app.translation import SimpleTranslator
from app.nlp_extractor import extract_fields, translate_to_english
from app.reverse_translate import translate_english_to_yolngu
from app.dataset_manager import save_record, get_all_records, get_dataset_path

bp = Blueprint("main", __name__)
translator = SimpleTranslator()

@bp.route("/")
def index():
    return render_template("index.html")

@bp.route("/api/translate", methods=["POST"])
def translate():
    payload = request.get_json(force=True)
    raw_text = payload.get("text", "")
    source_language = payload.get("source_language", "english")
    if source_language != "english":
        english_text = translate_to_english(raw_text)
        english_text = translator.translate(english_text)
    else:
        english_text = raw_text
    symptoms = translator.extract_symptoms(english_text)
    return jsonify({"source_text": raw_text, "english_text": english_text, "recognized_symptoms": symptoms})

@bp.route("/api/reverse_translate", methods=["POST"])
def reverse_translate():
    payload = request.get_json(force=True)
    english_text = payload.get("text", "")
    # Try AI first for full sentence understanding
    from app.reverse_translate import ai_understand_sentence, translate_english_to_yolngu
    ai_result = ai_understand_sentence(english_text)
    if ai_result:
        return jsonify({
            "english_text": ai_result.get("english", english_text),
            "yolngu_text": ai_result.get("yolngu", translate_english_to_yolngu(english_text)),
            "symptoms": ai_result.get("symptoms", []),
            "days": ai_result.get("days"),
            "severity": ai_result.get("severity", "mild"),
            "ai_powered": True
        })
    # Fallback to dictionary
    yolngu_text = translate_english_to_yolngu(english_text)
    return jsonify({"english_text": english_text, "yolngu_text": yolngu_text})

@bp.route("/api/triage", methods=["POST"])
def triage():
    payload = request.get_json(force=True)
    raw_text = payload.get("text", "")
    source_language = payload.get("source_language", "english")
    age_group = payload.get("age_group", "adult")
    age = payload.get("age")
    gender = payload.get("gender")
    days = payload.get("days")
    medication = payload.get("medication_taken")
    severity_score = payload.get("severity_score")
    if source_language != "english":
        english_text = translate_to_english(raw_text)
        english_text = translator.translate(english_text)
    else:
        english_text = raw_text
    extracted = extract_fields(raw_text=raw_text, age=int(age) if age else None,
        gender=gender, days=int(days) if days else None,
        medication_taken=medication, severity_score=int(severity_score) if severity_score else None)
    symptoms = translator.extract_symptoms(english_text)
    nlp_symptoms = extracted["symptoms"].split("; ") if extracted["symptoms"] and extracted["symptoms"] != "unknown" else []
    if not symptoms and nlp_symptoms:
        symptoms = nlp_symptoms
    if not extracted["symptoms"] or extracted["symptoms"] == "unknown":
        extracted["symptoms"] = "; ".join(symptoms) if symptoms else "unknown"
    if not symptoms and not nlp_symptoms:
        return jsonify({"error": "No known symptoms detected.", "english_text": english_text}), 400
    saved_row = save_record(extracted)
    return jsonify({"source_text": raw_text, "english_text": english_text,
        "recognized_symptoms": symptoms,
        "nlp": {"symptoms": extracted["symptoms"], "days": extracted["days"],
            "severity_score": extracted["severity_score"], "medication_taken": extracted["medication_taken"],
            "body_location": extracted["body_location"], "other_body_part": extracted["other_body_part"],
            "age": extracted["age"], "gender": extracted["gender"], "target": extracted["target"]},
        "record_id": saved_row["id"]})

@bp.route("/api/dataset", methods=["GET"])
def get_dataset():
    return jsonify({"count": len(get_all_records()), "records": get_all_records()})

@bp.route("/api/dataset/download", methods=["GET"])
def download_dataset():
    return send_file(get_dataset_path(), mimetype="text/csv", as_attachment=True, download_name="nlp_dataset.csv")

def create_app() -> Flask:
    base_dir = Path(__file__).resolve().parent.parent
    app = Flask(__name__, template_folder=str(base_dir / "templates"), static_folder=str(base_dir / "static"))
    app.register_blueprint(bp)
    return app
