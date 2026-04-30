from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_FILE = BASE_DIR / "data" / "triage_training_data.csv"
MODEL_DIR = BASE_DIR / "models"
TRANSLATION_FILE = BASE_DIR / "data" / "yolngu_dictionary.json"
