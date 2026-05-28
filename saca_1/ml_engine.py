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
    All parameters must be supplied by the caller — no monkey-patching.
    Returns: (prediction_label, top3_predictions_dict, results_df, best_name)
    or None if ML is not ready.
    """
    if not _ml_ready:
        return None

    try:
        row = pd.DataFrame([{
            "symptom_text":   str(symptom_text) if symptom_text else "unknown",
            "age":            int(age),
            "heart_rate":     float(heart_rate),
            "temperature":    float(temperature),
            "breathing_rate": float(breathing_rate),
        }])
        proc = _preprocessor.transform(row)

        # Best model only — skip top3 loop (not used by result screen)
        pred  = _best_model.predict(proc)
        label = _label_encoder.inverse_transform(pred)[0]

        # Return minimal result — avoids copying the full DataFrame
        return label, {}, None, _best_name

    except Exception as e:
        print(f"[SACA ML] Prediction error: {e}")
        import traceback; traceback.print_exc()
        return None


def is_ready():
    return _ml_ready


def get_results_df():
    return _results_df.copy() if _results_df is not None else None


def get_best_name():
    return _best_name