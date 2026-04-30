import csv
import os
from datetime import datetime
from pathlib import Path

DATASET_PATH = Path("data/nlp_dataset.csv")

FIELDNAMES = [
    "id", "timestamp", "symptom_text", "translated_text",
    "symptoms", "days", "severity_score", "medication_taken",
    "other_body_part", "age", "gender", "body_location", "target",
]

def _ensure_file():
    DATASET_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not DATASET_PATH.exists():
        with open(DATASET_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()

def save_record(record: dict) -> dict:
    _ensure_file()
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        row_count = sum(1 for _ in f) - 1
    row = {
        "id": row_count + 1,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        **{k: record.get(k, "") for k in FIELDNAMES if k not in ("id", "timestamp")},
    }
    with open(DATASET_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writerow(row)
    return row

def get_all_records() -> list:
    _ensure_file()
    with open(DATASET_PATH, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))

def get_dataset_path() -> str:
    return str(DATASET_PATH.resolve())
