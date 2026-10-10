"""Private shelter-facing ML API. The shipped artifact is rejected for target leakage."""
import math
import os
from typing import Any

from fastapi import Depends, FastAPI, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field

VERSION = "mock-0.1.0"
LIMITATIONS = [
    "This is a deterministic development mock, not a validated prediction.",
    "The available Cox artifact contains outcome fields in its feature list and is not used.",
    "Austin Animal Center data (Texas, 2013-2018) does not represent Italian shelter outcomes.",
    "Never use this output for intake refusal, euthanasia, transfer, adopter selection, or any decision about an animal's life.",
]
app = FastAPI(title="PetMatch private ML service", version=VERSION)
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


def predict(features: dict[str, Any]) -> dict[str, Any]:
    """A clearly labelled heuristic-shaped mock. Values are not calibrated probabilities."""
    age = max(0.0, min(float(features.get("age_months_at_intake") or 24), 360.0))
    days_waiting = max(0.0, min(float(features.get("days_in_care") or 0), 3650.0))
    completeness = sum(features.get(name) is not None for name in ("sex", "age_months_at_intake", "is_mixed", "is_sterilized")) / 4
    adoption_probability = max(0.05, min(0.95, 0.72 - age / 900 - days_waiting / 1000 + (0.08 if features.get("has_name") else 0)))
    rate = -math.log(1 - adoption_probability) / 90
    cumulative = [1 - math.exp(-rate * day) for day in (7, 30, 90)]
    probabilities = {
        "lt_7": round(cumulative[0], 4),
        "7_30": round(max(0, cumulative[1] - cumulative[0]), 4),
        "30_90": round(max(0, cumulative[2] - cumulative[1]), 4),
        "gt_90": round(max(0, 1 - cumulative[2]), 4),
    }
    total = sum(probabilities.values())
    probabilities = {key: round(value / total, 4) for key, value in probabilities.items()}
    factors = []
    if age >= 96: factors.append({"feature": "age", "direction": "attention", "label": "Age band suggests extra outreach"})
    if days_waiting >= 30: factors.append({"feature": "days_in_care", "direction": "attention", "label": "Longer time in care"})
    if completeness < 1: factors.append({"feature": "data_completeness", "direction": "data", "label": "Some profile fields are missing"})
    if not factors: factors.append({"feature": "profile", "direction": "data", "label": "No mock risk flags; check the profile and photos"})
    return {
        "adoption_probability": round(adoption_probability, 4),
        "bucket_probabilities": probabilities,
        "days_bucket": max(probabilities, key=probabilities.get),
        "median_days_to_adoption": None,
        "top_factors": factors[:3],
        "data_completeness": round(completeness, 2),
        "prediction_interval": None,
        "model_version": VERSION,
        "mode": "mock",
        "disclaimer_key": "predictions.disclaimer.mock_unvalidated",
    }


@app.get("/health")
def health():
    return {"status": "ok", "model": "mock", "model_version": VERSION}


@app.get("/model-info", dependencies=[Depends(authorized)])
def model_info():
    return {"model_version": VERSION, "mode": "mock", "validated": False, "training_window": None, "feature_list": ["age_months_at_intake", "days_in_care", "sex", "species", "is_mixed", "is_sterilized", "has_name"], "metrics": None, "limitations": LIMITATIONS}


@app.post("/predict", dependencies=[Depends(authorized)])
def predict_one(item: Item):
    return {"ref": item.ref, "prediction": predict(item.features)}


@app.post("/predict/batch", dependencies=[Depends(authorized)])
def predict_batch(batch: Batch):
    return {"predictions": [{"ref": item.ref, "prediction": predict(item.features)} for item in batch.items], "failed": []}
