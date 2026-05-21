# ============================================================
# train_model.py  —  Train 7 combinations, keep best 3
#
# Algorithms:
#   A   = Logistic Regression
#   B   = Random Forest
#   C   = XGBoost
#   AB  = LR + RF  (2-way ensemble)
#   AC  = LR + XGB (2-way ensemble)
#   BC  = RF + XGB (2-way ensemble)
#   ABC = LR + RF + XGB (3-way ensemble)
#
# Ranked by: Severe Recall → F1 → Accuracy
# ============================================================

import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from xgboost import XGBClassifier

from config import (
    DATASET_FILE, MODEL_FILES,
    TEXT_FEATURE, NUMERIC_FEATURES, TARGET_COLUMN,
)


def make_lr():
    return LogisticRegression(max_iter=1000, class_weight="balanced")

def make_rf():
    return RandomForestClassifier(
        n_estimators=200, max_depth=12,
        class_weight="balanced", random_state=42
    )

def make_xgb(num_classes):
    return XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.1,
        objective="multi:softprob", num_class=num_classes,
        eval_metric="mlogloss", random_state=42, verbosity=0
    )


def train_and_save_models():
    # ── Load & clean ─────────────────────────────────────────
    df = pd.read_csv(DATASET_FILE)
    df = df.dropna(subset=[TEXT_FEATURE, TARGET_COLUMN])
    for col in NUMERIC_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col].median())

    X = df[[TEXT_FEATURE] + NUMERIC_FEATURES]
    y = df[TARGET_COLUMN].str.strip().str.lower()

    # ── Encode labels ─────────────────────────────────────────
    label_encoder = LabelEncoder()
    y_encoded  = label_encoder.fit_transform(y)
    num_classes = len(label_encoder.classes_)

    # ── Split ─────────────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y_encoded, test_size=0.2, random_state=42, stratify=y_encoded
    )

    # ── Preprocessor ──────────────────────────────────────────
    preprocessor = ColumnTransformer(transformers=[
        ("text", TfidfVectorizer(max_features=3000), TEXT_FEATURE),
        ("num",  "passthrough", NUMERIC_FEATURES),
    ])
    X_train_proc = preprocessor.fit_transform(X_train)
    X_test_proc  = preprocessor.transform(X_test)

    severe_index = (
        list(label_encoder.classes_).index("severe")
        if "severe" in label_encoder.classes_ else None
    )

    # ── All 7 combinations ────────────────────────────────────
    combos = {
        "A_LogisticRegression": make_lr(),
        "B_RandomForest":       make_rf(),
        "C_XGBoost":            make_xgb(num_classes),
        "AB_LR+RF":  VotingClassifier(
            estimators=[("lr", make_lr()), ("rf", make_rf())], voting="soft"),
        "AC_LR+XGB": VotingClassifier(
            estimators=[("lr", make_lr()), ("xgb", make_xgb(num_classes))], voting="soft"),
        "BC_RF+XGB": VotingClassifier(
            estimators=[("rf", make_rf()), ("xgb", make_xgb(num_classes))], voting="soft"),
        "ABC_LR+RF+XGB": VotingClassifier(
            estimators=[("lr", make_lr()), ("rf", make_rf()), ("xgb", make_xgb(num_classes))],
            voting="soft"),
    }

    results, trained = [], {}
    print("\nTraining all 7 combinations...")

    for name, model in combos.items():
        print(f"  → {name}")
        model.fit(X_train_proc, y_train)
        y_pred = model.predict(X_test_proc)

        acc = accuracy_score(y_test, y_pred)
        prec, rec, f1, _ = precision_recall_fscore_support(
            y_test, y_pred, average="weighted", zero_division=0)
        _, rec_cls, _, _ = precision_recall_fscore_support(
            y_test, y_pred, average=None, zero_division=0)
        sev_rec = rec_cls[severe_index] if severe_index is not None else 0.0

        results.append({
            "Model": name,
            "Accuracy":           round(acc,     4),
            "Precision_Weighted": round(prec,    4),
            "Recall_Weighted":    round(rec,     4),
            "F1_Weighted":        round(f1,      4),
            "Severe_Recall":      round(sev_rec, 4),
        })
        trained[name] = model

    # ── Rank → top 3 ──────────────────────────────────────────
    all_df = pd.DataFrame(results).sort_values(
        by=["Severe_Recall", "F1_Weighted", "Accuracy"],
        ascending=False
    ).reset_index(drop=True)

    print("\n=== All 7 Ranked ===")
    print(all_df[["Model","Accuracy","F1_Weighted","Severe_Recall"]].to_string(index=False))

    top3_names  = all_df.head(3)["Model"].tolist()
    results_df  = all_df.head(3).reset_index(drop=True)
    top3_models = {n: trained[n] for n in top3_names}
    best_name   = results_df.iloc[0]["Model"]
    best_model  = top3_models[best_name]

    print(f"\n✓ Top 3 : {top3_names}")
    print(f"✓ Best  : {best_name}\n")

    # ── Save ──────────────────────────────────────────────────
    joblib.dump(preprocessor,  MODEL_FILES["preprocessor"])
    joblib.dump(label_encoder, MODEL_FILES["label_encoder"])
    joblib.dump(best_model,    MODEL_FILES["best_model"])
    joblib.dump(top3_models,   MODEL_FILES["all_models"])
    results_df.to_csv(MODEL_FILES["results"], index=False)

    return preprocessor, label_encoder, best_model, top3_models, results_df, best_name


if __name__ == "__main__":
    train_and_save_models()
