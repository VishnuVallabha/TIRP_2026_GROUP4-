# ============================================================
# ml_config.py  —  SACA ML configuration
# All ML file paths and column names live here.
# ============================================================

DATASET_FILE = "saca_symptom_data.csv"

MODEL_FILES = {
    "preprocessor":  "saca_preprocessor.pkl",
    "label_encoder": "saca_label_encoder.pkl",
    "best_model":    "saca_best_model.pkl",
    "all_models":    "saca_all_models.pkl",
    "results":       "saca_results.csv",
}

TEXT_FEATURE     = "symptom_text"
NUMERIC_FEATURES = ["age", "heart_rate", "temperature", "breathing_rate"]
TARGET_COLUMN    = "severity"
