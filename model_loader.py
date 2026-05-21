# ============================================================
# model_loader.py  —  Load saved models or retrain
# ============================================================

import os
import joblib
import pandas as pd

from config import MODEL_FILES
from train_model import train_and_save_models


def load_or_train():
    """Load from disk if all files exist, else train fresh."""
    if all(os.path.exists(p) for p in MODEL_FILES.values()):
        print("Loading saved models...")
        preprocessor  = joblib.load(MODEL_FILES["preprocessor"])
        label_encoder = joblib.load(MODEL_FILES["label_encoder"])
        best_model    = joblib.load(MODEL_FILES["best_model"])
        top3_models   = joblib.load(MODEL_FILES["all_models"])
        results_df    = pd.read_csv(MODEL_FILES["results"])
        best_name     = results_df.iloc[0]["Model"]
        print(f"✓ Loaded. Best: {best_name}\n")
        return preprocessor, label_encoder, best_model, top3_models, results_df, best_name

    print("No saved models found — training from scratch...")
    return train_and_save_models()


def force_retrain():
    """Delete saved files and retrain from scratch."""
    for path in MODEL_FILES.values():
        if os.path.exists(path):
            os.remove(path)
    return train_and_save_models()
