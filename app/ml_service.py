import sys, os
ML_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "ml")
if ML_DIR not in sys.path:
    sys.path.insert(0, ML_DIR)

class MLService:
    def __init__(self):
        self._ready = False
        self._best_name = "rule_based"
        self._results_df = None
        self._load()

    def _load(self):
        try:
            import ml_engine as ml
            ml.load_or_train()
            self._ready = ml.is_ready()
            if self._ready:
                import pandas as pd
                from ml_config import MODEL_FILES
                self._results_df = pd.read_csv(MODEL_FILES["results"])
                self._best_name = self._results_df.iloc[0]["Model"]
                print(f"[SACA] ML ready — best model: {self._best_name}")
            else:
                print("[SACA] ML not ready — using rule-based triage")
        except Exception as e:
            print(f"[SACA] ML load error: {e} — using rule-based triage")
            self._ready = False

    def is_ready(self): return self._ready
    def get_best_model_name(self): return self._best_name

    def get_metrics(self):
        if self._results_df is not None:
            try:
                row = self._results_df.iloc[0]
                return {"model": row.get("Model",""), "accuracy": round(float(row.get("Accuracy",0)),3), "f1": round(float(row.get("F1",0)),3)}
            except: pass
        return {}

    def predict(self, symptom_text, age=35, severity_score=5, days=1, fever_temp=37.0):
        heart_rate = min(70 + (severity_score * 5), 140)
        breathing_rate = 16 + int((severity_score / 10) * 8)
        target = "mild"
        if self._ready:
            try:
                import ml_engine as ml
                result = ml.ml_predict(symptom_text=symptom_text, age=age, heart_rate=heart_rate, temperature=fever_temp, breathing_rate=breathing_rate)
                if result is not None:
                    label, _, _, _ = result
                    target = label.lower()
            except Exception as e:
                print(f"[SACA] ML predict error: {e}")
                target = self._rule_based(symptom_text, severity_score, days)
        else:
            target = self._rule_based(symptom_text, severity_score, days)
        precautions = {
            "severe": ["Seek emergency care immediately","Do not leave patient alone","Call 000 or Royal Flying Doctor: 1800 625 800"],
            "moderate": ["Visit Yirrkala Health Clinic within 24 hours","Rest and drink plenty of fluids","Monitor symptoms closely"],
            "mild": ["Rest at home","Drink plenty of water","Return if symptoms worsen"],
        }
        return {"target": target, "severity": target.upper(), "precautions": precautions.get(target, precautions["mild"]), "model_used": self._best_name}

    def _rule_based(self, symptom_text, severity_score, days):
        text = symptom_text.lower()
        if any(k in text for k in ["chest pain","cannot breathe","breathless","bleeding","fracture","emergency"]) or severity_score >= 8:
            return "severe"
        if any(k in text for k in ["fever","vomiting","diarrhoea","cannot eat","swollen","cough","fatigue"]) or severity_score >= 5 or days >= 3:
            return "moderate"
        return "mild"

_service = None
def get_ml_service():
    global _service
    if _service is None:
        _service = MLService()
    return _service
