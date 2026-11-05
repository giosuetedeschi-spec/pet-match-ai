"""Private shelter-facing API for two explicitly demonstrative ML models."""
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

VERSION = "petmatch-demo-ml-0.1.0"
MODEL_DIR = Path(os.getenv("ML_MODEL_DIR", Path(__file__).resolve().parent / "models"))
app = FastAPI(title="PetMatch internal ML demo", version=VERSION)
bearer = HTTPBearer(auto_error=False)


class Item(BaseModel):
    ref: str = Field(min_length=1, max_length=80)
    features: dict[str, Any]


class Batch(BaseModel):
    items: list[Item] = Field(min_length=1, max_length=500)


def authorized(credentials: HTTPAuthorizationCredentials | None = Depends(bearer)):
    expected = os.getenv("ML_SERVICE_TOKEN", "local-development-token")
    if not credentials or credentials.scheme.lower() != "bearer" or credentials.credentials != expected:
        raise HTTPException(status_code=401, detail="unauthorized")


@lru_cache(maxsize=1)
def _models():
    try:
        models = {
            "return_risk": joblib.load(MODEL_DIR / "return_risk.joblib"),
            "austin_outcome": joblib.load(MODEL_DIR / "austin_outcome.joblib"),
            "austin_adoption_days": joblib.load(MODEL_DIR / "austin_adoption_days.joblib"),
            "metadata": json.loads((MODEL_DIR / "model_metadata.json").read_text(encoding="utf-8")),
        }
    except (OSError, ValueError, KeyError) as exc:
        raise HTTPException(status_code=503, detail="Trained demo models are unavailable; run train_models.py.") from exc
    return models


def _probability(model, features: dict[str, Any], columns: list[str]) -> float:
    row = pd.DataFrame([{key: features.get(key) for key in columns}], columns=columns)
    return float(model.predict_proba(row)[0][1])


def _austin_factors(model, row: dict[str, Any]) -> list[dict[str, Any]]:
    """Return per-field logistic contributions in log-odds space."""
    try:
        preprocessor = model.named_steps["preprocess"]
        classifier = model.named_steps["model"]
        transformed = preprocessor.transform(pd.DataFrame([row]))
        values = transformed.toarray().reshape(-1) if hasattr(transformed, "toarray") else np.asarray(transformed).reshape(-1)
        names = preprocessor.get_feature_names_out()
        contributions: dict[str, float] = {}
        for name, value, coefficient in zip(names, values, classifier.coef_[0]):
            encoded_name = str(name).split("__", 1)[-1]
            source = next((field for field in ("age_months", "species", "breed", "sex") if encoded_name == field or encoded_name.startswith(field + "_")), None)
            if source:
                contributions[source] = contributions.get(source, 0.0) + float(value * coefficient)
        display = {"age_months": "età (mesi)", "species": "specie", "breed": "razza", "sex": "sesso"}
        return [
            {"label": f"{display[field]}: {row[field]}", "contribution": round(value, 4), "direction": "positive" if value >= 0 else "negative"}
            for field, value in sorted(contributions.items(), key=lambda item: abs(item[1]), reverse=True)[:4]
        ]
    except (AttributeError, KeyError, TypeError, ValueError):
        return []


def _normalise_austin(features: dict[str, Any]) -> dict[str, Any]:
    species = str(features.get("species") or features.get("animal_type") or "unknown").lower()
    species = {"dog": "dog", "cane": "dog", "cat": "cat", "gatto": "cat"}.get(species, species)
    gender = str(features.get("gender") or features.get("sex") or "").lower()
    sex = "male" if gender in {"m", "male", "intact male", "neutered male"} else "female" if gender in {"f", "female", "spayed female"} else "unknown"
    return {
        "species": species,
        "breed": str(features.get("breed") or "unknown").lower(),
        "sex": sex,
        "age_months": features.get("age_months", features.get("age_months_at_intake")),
        "has_name": int(bool(features.get("has_name", features.get("name")))),
    }


def predict(features: dict[str, Any]) -> dict[str, Any]:
    models = _models()
    record = models["metadata"]["animal_adoption_outcome"]
    row = _normalise_austin(features)
    probability = _probability(models["austin_outcome"], row, record["features"])
    expected_days = float(models["austin_adoption_days"].predict(pd.DataFrame([row]))[0])
    raw_values = {
        "species": features.get("species") or features.get("animal_type"),
        "breed": features.get("breed"),
        "sex": features.get("gender") or features.get("sex"),
        "age_months": features.get("age_months", features.get("age_months_at_intake")),
    }
    data_completeness = sum(value not in (None, "", "unknown", "Unknown") for value in raw_values.values()) / len(raw_values)
    return {
        "adoption_probability": round(probability, 4),
        "bucket_probabilities": {"adoption": round(probability, 4), "other_observed_outcome": round(1 - probability, 4)},
        "top_factors": _austin_factors(models["austin_outcome"], row),
        "data_completeness": round(data_completeness, 4),
        "estimated_days_if_adopted": round(max(0.0, expected_days), 1),
        "days_mae_on_test": record["adoption_days_if_adopted"]["mae_days"],
        "test_roc_auc": record["test_metrics"]["roc_auc"],
        "model_version": record["version"],
        "mode": "trained_demo",
        "prediction_target": "adoption_vs_other_observed_outcome",
        "audience": "shelter_staff_only",
        "limitations": record["limitations"],
    }


def predict_compatibility(features: dict[str, Any]) -> dict[str, Any]:
    models = _models()
    record = models["metadata"]["compatibility_return_risk"]
    score = _probability(models["return_risk"], features, record["features"])
    return {
        "return_risk_score": round(score, 4),
        "model_version": record["version"],
        "mode": "trained_synthetic_demo",
        "prediction_target": "post_adoption_return",
        "audience": "shelter_staff_only",
        "limitations": record["limitations"],
    }


@app.get("/health")
def health():
    try:
        _models()
    except HTTPException as exc:
        raise HTTPException(status_code=503, detail="Trained demo models are unavailable.") from exc
    return {"status": "ok", "model": "trained_demo_models", "model_version": VERSION}


@app.get("/model-info", dependencies=[Depends(authorized)])
def model_info():
    return _models()["metadata"]


@app.post("/predict", dependencies=[Depends(authorized)])
def predict_one(item: Item):
    return {"ref": item.ref, "prediction": predict(item.features)}


@app.post("/predict/compatibility", dependencies=[Depends(authorized)])
def predict_compatibility_one(item: Item):
    return {"ref": item.ref, "prediction": predict_compatibility(item.features)}


@app.post("/predict/batch", dependencies=[Depends(authorized)])
def predict_batch(batch: Batch):
    return {"predictions": [{"ref": item.ref, "prediction": predict(item.features)} for item in batch.items], "failed": []}
