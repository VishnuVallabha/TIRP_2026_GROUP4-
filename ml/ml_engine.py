# ============================================================
# ml_engine.py  —  Load/train ML models + live prediction
#
# Used by triage.py to replace the rule-based score with
# a real ML prediction when models are available.
# ============================================================

import os
import joblib
import pandas as pd

from ml_config import MODEL_FILES
from ml_train  import train_and_save

# ── Module-level state ────────────────────────────────────────────
_preprocessor   = None
_label_encoder  = None
_best_model     = None
_top3_models    = None
_results_df     = None
_best_name      = None
_ml_ready       = False


def load_or_train():
    """Load saved models or train from scratch. Called once at startup."""
    global _preprocessor, _label_encoder, _best_model
    global _top3_models, _results_df, _best_name, _ml_ready

    if all(os.path.exists(p) for p in MODEL_FILES.values()):
        print("[SACA ML] Loading saved models...")
        _preprocessor  = joblib.load(MODEL_FILES["preprocessor"])
        _label_encoder = joblib.load(MODEL_FILES["label_encoder"])
        _best_model    = joblib.load(MODEL_FILES["best_model"])
        _top3_models   = joblib.load(MODEL_FILES["all_models"])
        _results_df    = pd.read_csv(MODEL_FILES["results"])
        _best_name     = _results_df.iloc[0]["Model"]
        _ml_ready      = True
        print(f"[SACA ML] ✓ Ready. Best: {_best_name}\n")
    else:
        try:
            (_preprocessor, _label_encoder, _best_model,
             _top3_models, _results_df, _best_name) = train_and_save()
            _ml_ready = True
        except Exception as e:
            print(f"[SACA ML] ✗ Training failed: {e}")
            print("[SACA ML] Falling back to rule-based triage.\n")
            _ml_ready = False


def force_retrain():
    """Delete saved files and retrain. Called by Retrain button."""
    for path in MODEL_FILES.values():
        if os.path.exists(path):
            os.remove(path)
    load_or_train()


def ml_predict(symptom_text, age, heart_rate, temperature, breathing_rate):
    """
    Run ML prediction for a single patient.
    Returns: (prediction_label, top3_predictions_dict, results_df, best_name)
    or None if ML is not ready.
    """
    if not _ml_ready:
        return None

    import ml_engine as _ml_engine_module
    try:
        # Use patient age from app if available
        actual_age = getattr(_ml_engine_module, "_PATIENT_AGE", age)
        row = pd.DataFrame([{
            "symptom_text":  symptom_text,
            "age":           actual_age,
            "heart_rate":    heart_rate,
            "temperature":   temperature,
            "breathing_rate": breathing_rate,
        }])
        proc = _preprocessor.transform(row)

        # Best model final prediction
        pred  = _best_model.predict(proc)
        label = _label_encoder.inverse_transform(pred)[0]

        # All top-3 predictions
        top3_preds = {}
        for name, mdl in _top3_models.items():
            p = mdl.predict(proc)
            top3_preds[name] = _label_encoder.inverse_transform(p)[0]

        return label, top3_preds, _results_df.copy(), _best_name

    except Exception as e:
        print(f"[SACA ML] Prediction error: {e}")
        return None


def is_ready():
    return _ml_ready


def get_results_df():
    return _results_df.copy() if _results_df is not None else None


def get_best_name():
    return _best_name
