# ============================================================
# ml_train.py  —  Train 7 algorithm combinations, keep best 3
#
#  A   = Logistic Regression       (individual)
#  B   = Random Forest             (individual)
#  C   = XGBoost                   (individual)
#  AB  = LR + RF                   (2-way ensemble)
#  AC  = LR + XGB                  (2-way ensemble)
#  BC  = RF + XGB                  (2-way ensemble)
#  ABC = LR + RF + XGB             (3-way ensemble)
#
#  Ranked by: Severe Recall → F1 → Accuracy
#  Top 3 saved → best model used for live triage
# ============================================================

import os
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

from ml_config import DATASET_FILE, MODEL_FILES, TEXT_FEATURE, NUMERIC_FEATURES, TARGET_COLUMN


# ── Model factories ───────────────────────────────────────────────
def _lr():
    return LogisticRegression(max_iter=1000, class_weight="balanced")

def _rf():
    return RandomForestClassifier(
        n_estimators=200, max_depth=12, class_weight="balanced", random_state=42)

def _xgb(n):
    return XGBClassifier(
        n_estimators=200, max_depth=6, learning_rate=0.1,
        objective="multi:softprob", num_class=n,
        eval_metric="mlogloss", random_state=42, verbosity=0)


def train_and_save():
    """
    Load dataset → train all 7 combos → rank → keep top 3 → save.
    Returns: preprocessor, label_encoder, best_model, top3_models, results_df, best_name
    """
    # ── Load ─────────────────────────────────────────────────────
    base = os.path.dirname(os.path.abspath(__file__))
    csv  = os.path.join(base, DATASET_FILE)
    df   = pd.read_csv(csv)
    df   = df.dropna(subset=[TEXT_FEATURE, TARGET_COLUMN])
    for col in NUMERIC_FEATURES:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col].median())

    X = df[[TEXT_FEATURE] + NUMERIC_FEATURES]
    y = df[TARGET_COLUMN].str.strip().str.lower()

    # ── Encode ───────────────────────────────────────────────────
    le = LabelEncoder()
    y_enc  = le.fit_transform(y)
    n_cls  = len(le.classes_)

    X_train, X_test, y_train, y_test = train_test_split(
        X, y_enc, test_size=0.2, random_state=42, stratify=y_enc)

    # ── Preprocess ───────────────────────────────────────────────
    pre = ColumnTransformer([
        ("text", TfidfVectorizer(max_features=3000), TEXT_FEATURE),
        ("num",  "passthrough", NUMERIC_FEATURES),
    ])
    Xtr = pre.fit_transform(X_train)
    Xte = pre.transform(X_test)

    sev_idx = list(le.classes_).index("severe") if "severe" in le.classes_ else None

    # ── All 7 combos ─────────────────────────────────────────────
    combos = {
        "A_LogisticRegression": _lr(),
        "B_RandomForest":       _rf(),
        "C_XGBoost":            _xgb(n_cls),
        "AB_LR+RF":  VotingClassifier(
            [("lr", _lr()), ("rf", _rf())], voting="soft"),
        "AC_LR+XGB": VotingClassifier(
            [("lr", _lr()), ("xgb", _xgb(n_cls))], voting="soft"),
        "BC_RF+XGB": VotingClassifier(
            [("rf", _rf()), ("xgb", _xgb(n_cls))], voting="soft"),
        "ABC_LR+RF+XGB": VotingClassifier(
            [("lr", _lr()), ("rf", _rf()), ("xgb", _xgb(n_cls))], voting="soft"),
    }

    rows, trained = [], {}
    print("\n[SACA ML] Training 7 algorithm combinations...")
    for name, mdl in combos.items():
        print(f"  → {name}")
        mdl.fit(Xtr, y_train)
        yp = mdl.predict(Xte)
        acc            = accuracy_score(y_test, yp)
        p, r, f1, _    = precision_recall_fscore_support(y_test, yp, average="weighted", zero_division=0)
        _, rc, _, _    = precision_recall_fscore_support(y_test, yp, average=None, zero_division=0)
        sev_r          = rc[sev_idx] if sev_idx is not None else 0.0
        rows.append({"Model": name,
                     "Accuracy": round(acc, 4),
                     "Precision_Weighted": round(p, 4),
                     "Recall_Weighted": round(r, 4),
                     "F1_Weighted": round(f1, 4),
                     "Severe_Recall": round(sev_r, 4)})
        trained[name] = mdl

    # ── Rank → top 3 ─────────────────────────────────────────────
    all_df = pd.DataFrame(rows).sort_values(
        ["Severe_Recall","F1_Weighted","Accuracy"], ascending=False
    ).reset_index(drop=True)

    print("\n[SACA ML] === All 7 Ranked ===")
    print(all_df[["Model","Accuracy","F1_Weighted","Severe_Recall"]].to_string(index=False))

    top3_names  = all_df.head(3)["Model"].tolist()
    results_df  = all_df.head(3).reset_index(drop=True)
    top3        = {n: trained[n] for n in top3_names}
    best_name   = results_df.iloc[0]["Model"]
    best_mdl    = top3[best_name]

    print(f"\n[SACA ML] ✓ Top 3 : {top3_names}")
    print(f"[SACA ML] ✓ Best  : {best_name}\n")

    # ── Save ─────────────────────────────────────────────────────
    joblib.dump(pre,       MODEL_FILES["preprocessor"])
    joblib.dump(le,        MODEL_FILES["label_encoder"])
    joblib.dump(best_mdl,  MODEL_FILES["best_model"])
    joblib.dump(top3,      MODEL_FILES["all_models"])
    results_df.to_csv(MODEL_FILES["results"], index=False)

    return pre, le, best_mdl, top3, results_df, best_name


if __name__ == "__main__":
    train_and_save()
