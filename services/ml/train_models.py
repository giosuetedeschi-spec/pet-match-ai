"""Train the demonstrative Austin adoption and Kaggle return-risk models."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, brier_score_loss, mean_absolute_error, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor

SCRIPT_DIR = Path(__file__).resolve().parent
# In the repository this file lives at services/ml/train_models.py; in the
# Docker image it is copied directly to /app/train_models.py. Resolve both
# layouts, and keep the image's /app/data directory as its default data source.
if SCRIPT_DIR.name == "ml" and SCRIPT_DIR.parent.name == "services":
    PROJECT_ROOT = SCRIPT_DIR.parents[1]
    DATA_DIR = PROJECT_ROOT / "training-data"
else:
    PROJECT_ROOT = SCRIPT_DIR
    DATA_DIR = SCRIPT_DIR / "data"
MODEL_DIR = SCRIPT_DIR / "models"

PAIR_FEATURES = [
    "age_years", "size", "medical_needs", "neutered", "energy_level",
    "first_time_owner", "household_has_kids", "household_has_pets", "home_type",
    "has_yard", "hours_alone_per_day", "adopter_activity_level",
    "visits_before_adoption", "met_resident_pets", "adoption_counseling",
    "expectation_score",
]
PAIR_CATEGORICAL = ["size", "medical_needs", "home_type"]
PAIR_NUMERIC = [column for column in PAIR_FEATURES if column not in PAIR_CATEGORICAL]


def _preprocessor(categorical: list[str], numeric: list[str]) -> ColumnTransformer:
    return ColumnTransformer([
        ("categorical", Pipeline([
            ("impute", SimpleImputer(strategy="most_frequent")),
            ("encode", OneHotEncoder(handle_unknown="ignore", min_frequency=10)),
        ]), categorical),
        ("numeric", Pipeline([
            ("impute", SimpleImputer(strategy="median", add_indicator=True)),
            ("scale", StandardScaler()),
        ]), numeric),
    ])


def _metrics(y_true, probabilities) -> dict[str, float]:
    return {
        "roc_auc": round(float(roc_auc_score(y_true, probabilities)), 4),
        "average_precision": round(float(average_precision_score(y_true, probabilities)), 4),
        "brier_score": round(float(brier_score_loss(y_true, probabilities)), 4),
        "rows": int(len(y_true)),
        "positive_rate": round(float(np.mean(y_true)), 4),
    }


def train_return_risk(data_dir: Path, output_dir: Path) -> dict:
    frame = pd.read_csv(data_dir / "dog_adoption_master.csv")
    # Exclude IDs and every field recorded only after a return. Also omit the
    # synthetic precomputed mismatch columns to avoid shortcut learning.
    X = frame[PAIR_FEATURES].copy()
    y = frame["returned"].astype(int)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y,
    )
    pipeline = Pipeline([
        ("preprocess", _preprocessor(PAIR_CATEGORICAL, PAIR_NUMERIC)),
        ("model", RandomForestClassifier(
            n_estimators=250, min_samples_leaf=8, max_features="sqrt",
            n_jobs=1, random_state=42,
        )),
    ])
    pipeline.fit(X_train, y_train)
    probabilities = pipeline.predict_proba(X_test)[:, 1]
    joblib.dump(pipeline, output_dir / "return_risk.joblib")
    return {
        "version": "kaggle-dog-return-0.1.0",
        "dataset": "sergionefedov/dog-adoption-success-does-the-match-last",
        "dataset_is_synthetic": True,
        "target": "returned",
        "features": PAIR_FEATURES,
        "excluded_outcome_fields": ["adoption_id", "return_reason", "days_to_return", "returned", "energy_mismatch", "size_home_mismatch"],
        "split": "stratified random 80/20, seed=42",
        "metrics": _metrics(y_test, probabilities),
        "limitations": [
            "The Kaggle dataset is synthetic and intended for education; scores are not real-world estimates.",
            "Dog-only training data; do not apply to cats.",
            "Predicts return risk after adoption, not objective adopter-animal compatibility or adoption success.",
            "Use only as an internal discussion aid; a score must not reject an adopter or animal.",
        ],
    }


def _age_months(value) -> float:
    if pd.isna(value):
        return np.nan
    match = re.match(r"\s*(\d+)\s*(year|month|week|day)", str(value).lower())
    if not match:
        return np.nan
    amount, unit = int(match.group(1)), match.group(2)
    return float(amount * 12 if unit == "year" else amount if unit == "month" else amount / 4.345 if unit == "week" else amount / 30.4375)


def _sex(value) -> str:
    value = str(value or "").lower()
    if "female" in value:
        return "female"
    if "male" in value:
        return "male"
    return "unknown"


def _austin_features(frame: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "species": frame["animal_type"].astype(str).str.lower(),
        "breed": frame["breed"].fillna("unknown").astype(str).str.lower(),
        "sex": frame["sex_upon_intake"].map(_sex),
        "age_months": frame["age_upon_intake"].map(_age_months),
    })


def train_austin_outcome(data_dir: Path, output_dir: Path) -> dict:
    frame = pd.read_csv(data_dir / "aac_intakes_outcomes.csv", low_memory=False)
    frame["intake_datetime"] = pd.to_datetime(frame["intake_datetime"], errors="coerce")
    frame["animal_type"] = frame["animal_type"].astype(str).str.title()
    frame["outcome_type"] = frame["outcome_type"].fillna("").astype(str).str.strip()
    allowed = {"Adoption", "Rto-Adopt", "Transfer", "Return to Owner", "Euthanasia", "Died", "Relocate"}
    frame = frame[frame["animal_type"].isin(["Dog", "Cat"]) & frame["outcome_type"].isin(allowed)]
    frame = frame.dropna(subset=["intake_datetime"])
    X = _austin_features(frame)
    y = frame["outcome_type"].isin(["Adoption", "Rto-Adopt"]).astype(int)
    dates = frame["intake_datetime"]
    train_mask = dates < "2017-01-01"
    val_mask = (dates >= "2017-01-01") & (dates < "2017-07-01")
    test_mask = dates >= "2017-07-01"
    fit_mask = train_mask | val_mask
    categorical = ["species", "breed", "sex"]
    numeric = ["age_months"]
    pipeline = Pipeline([
        ("preprocess", _preprocessor(categorical, numeric)),
        ("model", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
    ])
    pipeline.fit(X.loc[fit_mask], y.loc[fit_mask])
    probabilities = pipeline.predict_proba(X.loc[test_mask])[:, 1]
    joblib.dump(pipeline, output_dir / "austin_outcome.joblib")
    adopted = y.eq(1) & frame["time_in_shelter_days"].notna()
    regression = Pipeline([
        ("preprocess", _preprocessor(categorical, numeric)),
        ("model", RandomForestRegressor(
            n_estimators=120, min_samples_leaf=15, max_features=0.8,
            n_jobs=1, random_state=42,
        )),
    ])
    regression_fit = adopted & fit_mask
    regression_test = adopted & test_mask
    regression.fit(X.loc[regression_fit], frame.loc[regression_fit, "time_in_shelter_days"])
    predicted_days = regression.predict(X.loc[regression_test])
    joblib.dump(regression, output_dir / "austin_adoption_days.joblib")
    return {
        "version": "austin-adoption-outcome-0.1.1",
        "dataset": "Austin Animal Center Shelter Intakes and Outcomes (Kaggle)",
        "dataset_is_synthetic": False,
        "target": "eventual_adoption_among_records_with_observed_outcome",
        "features": ["species", "breed", "sex", "age_months"],
        "excluded_outcome_fields": ["outcome_type", "outcome_subtype", "outcome_datetime", "time_in_shelter_days", "animal_id"],
        "split": "train before 2017-01; validation 2017-01 to 2017-06; test from 2017-07",
        "training_rows": int(fit_mask.sum()),
        "test_metrics": _metrics(y.loc[test_mask], probabilities),
        "adoption_days_if_adopted": {
            "mae_days": round(float(mean_absolute_error(frame.loc[regression_test, "time_in_shelter_days"], predicted_days)), 2),
            "test_rows": int(regression_test.sum()),
            "interpretation": "Estimated length of stay conditional on a recorded adoption, not a guaranteed date.",
        },
        "limitations": [
            "Austin, Texas historical data from 2013-2018; not representative of Italian shelters.",
            "The joined file contains completed outcomes only; animals still in care at export are censored and absent.",
            "Predicts adoption versus another observed outcome, not an adopter-specific match or exact time-to-adoption.",
            "Use only internally for planning; never use to reject or deprioritize an animal.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--output-dir", type=Path, default=MODEL_DIR)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    report = {
        "compatibility_return_risk": train_return_risk(args.data_dir, args.output_dir),
        "animal_adoption_outcome": train_austin_outcome(args.data_dir, args.output_dir),
    }
    (args.output_dir / "model_metadata.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
