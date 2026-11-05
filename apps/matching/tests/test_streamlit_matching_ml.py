import json
import unittest
from pathlib import Path
from unittest.mock import patch

from streamlit_app import (
    load_public_return_risk_model,
    public_return_risk_features,
    score_public_return_risk,
)


class FakeReturnRiskModel:
    def predict_proba(self, frame):
        self.columns = list(frame.columns)
        self.missing_visits = bool(frame["visits_before_adoption"].isna().iloc[0])
        return [[0.38, 0.62]]


class StreamlitPublicReturnRiskTest(unittest.TestCase):
    def test_builds_pair_features_from_answers_and_preserves_unknowns(self):
        animal = {
            "age_years": 3,
            "age_months": 6,
            "size": "LARGE",
            "special_needs": False,
            "is_spayed_neutered": None,
            "energy_level": "HIGH",
        }
        answers = {
            "has_children": False,
            "has_dogs": True,
            "has_cats": False,
            "garden_sqm": 25,
            "hours_away_from_home": 4,
            "activity_level": "MODERATE",
            "ml_first_time_owner": None,
            "ml_home_type": "unknown",
            "ml_visits_before_adoption": None,
            "ml_met_resident_pets": None,
            "ml_adoption_counseling": None,
            "ml_expectation_score": None,
        }

        features = public_return_risk_features(animal, answers)

        self.assertEqual(features["age_years"], 3.5)
        self.assertEqual(features["size"], "large")
        self.assertEqual(features["medical_needs"], "none")
        self.assertIsNone(features["neutered"])
        self.assertEqual(features["household_has_pets"], 1)
        self.assertEqual(features["adopter_activity_level"], 5)
        self.assertIsNone(features["first_time_owner"])
        self.assertIsNone(features["home_type"])
        self.assertIsNone(features["visits_before_adoption"])
        self.assertIsNone(features["met_resident_pets"])
        self.assertIsNone(features["adoption_counseling"])
        self.assertIsNone(features["expectation_score"])

    def test_loads_joblib_model_and_scores_with_missing_inputs(self):
        model_dir = Path("local-models")
        features = ["age_years", "visits_before_adoption"]
        model = FakeReturnRiskModel()
        metadata = json.dumps({
            "compatibility_return_risk": {"version": "test-model", "features": features},
        })
        load_public_return_risk_model.clear()
        with patch.object(Path, "read_text", return_value=metadata), patch(
            "streamlit_app.joblib.load", return_value=model,
        ) as load_joblib:
            result = score_public_return_risk({"age_years": 2.5, "visits_before_adoption": None}, model_dir)

        self.assertEqual(result, {"return_risk_score": 0.62, "model_version": "test-model"})
        self.assertEqual(model.columns, features)
        self.assertTrue(model.missing_visits)
        load_joblib.assert_called_once_with(model_dir / "return_risk.joblib")
        load_public_return_risk_model.clear()


if __name__ == "__main__":
    unittest.main()
