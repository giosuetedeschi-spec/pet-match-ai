import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app import authorized, predict, predict_compatibility


class FakeClassifier:
    def predict_proba(self, frame):
        self.last_frame = frame
        return [[0.7, 0.3]]


class FakeRegressor:
    def predict(self, frame):
        self.last_frame = frame
        return [42.0]


class PredictionTests(unittest.TestCase):
    def setUp(self):
        self.models = {
            "austin_outcome": FakeClassifier(),
            "austin_adoption_days": FakeRegressor(),
            "return_risk": FakeClassifier(),
            "metadata": {
                "animal_adoption_outcome": {
                    "version": "austin-demo-test",
                    "features": ["species", "breed", "sex", "age_months"],
                    "adoption_days_if_adopted": {"mae_days": 19.5},
                    "test_metrics": {"roc_auc": 0.65},
                    "limitations": ["demo"],
                },
                "compatibility_return_risk": {
                    "version": "kaggle-demo-test",
                    "features": ["age_years", "size"],
                    "limitations": ["synthetic"],
                },
            },
        }

    def test_animal_prediction_is_staff_only_and_uses_intake_features(self):
        with patch("app._models", return_value=self.models):
            result = predict({"species": "DOG", "breed": "Mix", "gender": "F", "age_months": 15})
        self.assertEqual(result["adoption_probability"], 0.3)
        self.assertEqual(result["bucket_probabilities"], {"adoption": 0.3, "other_observed_outcome": 0.7})
        self.assertEqual(result["data_completeness"], 1.0)
        self.assertEqual(result["top_factors"], [])
        self.assertEqual(result["estimated_days_if_adopted"], 42.0)
        self.assertEqual(result["audience"], "shelter_staff_only")
        self.assertEqual(self.models["austin_outcome"].last_frame.loc[0, "sex"], "female")

    def test_pair_prediction_is_internal_and_discloses_synthetic_model(self):
        with patch("app._models", return_value=self.models):
            result = predict_compatibility({"age_years": 4, "size": "medium"})
        self.assertEqual(result["return_risk_score"], 0.3)
        self.assertEqual(result["mode"], "trained_synthetic_demo")
        self.assertEqual(result["audience"], "shelter_staff_only")

    def test_bearer_token_is_required(self):
        with patch.dict(os.environ, {"ML_SERVICE_TOKEN": "ci-secret"}):
            with self.assertRaises(HTTPException) as missing:
                authorized(None)
            self.assertEqual(missing.exception.status_code, 401)
            authorized(HTTPAuthorizationCredentials(scheme="Bearer", credentials="ci-secret"))


if __name__ == "__main__":
    unittest.main()
