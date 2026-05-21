import os
_BASE = os.path.dirname(os.path.abspath(__file__))
DATASET_FILE = os.path.join(_BASE,"..","data","saca_symptom_data.csv")
MODEL_FILES = {
    "preprocessor":  os.path.join(_BASE,"saca_preprocessor.pkl"),
    "label_encoder": os.path.join(_BASE,"saca_label_encoder.pkl"),
    "best_model":    os.path.join(_BASE,"saca_best_model.pkl"),
    "all_models":    os.path.join(_BASE,"saca_all_models.pkl"),
    "results":       os.path.join(_BASE,"saca_results.csv"),
}
TEXT_FEATURE = "symptom_text"
NUMERIC_FEATURES = ["age","heart_rate","temperature","breathing_rate"]
TARGET_COLUMN = "severity"
