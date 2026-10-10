import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials

from app import VERSION, authorized, predict


class PredictionTests(unittest.TestCase):
    def test_mock_is_deterministic_and_disclosed(self):
        features = {"age_months_at_intake": 18, "days_in_care": 35, "has_name": True}

        first = predict(features)
        second = predict(features)

        self.assertEqual(first, second)
        self.assertEqual(first["mode"], "mock")
        self.assertEqual(first["model_version"], VERSION)
        self.assertEqual(first["disclaimer_key"], "predictions.disclaimer.mock_unvalidated")

    def test_bucket_probabilities_are_bounded_and_normalized(self):
        result = predict({"age_months_at_intake": 120, "days_in_care": 400})
        probabilities = result["bucket_probabilities"].values()

        self.assertTrue(all(0 <= probability <= 1 for probability in probabilities))
        self.assertAlmostEqual(sum(probabilities), 1.0, places=3)

    def test_bearer_token_is_required(self):
        with patch.dict(os.environ, {"ML_SERVICE_TOKEN": "ci-secret"}):
            with self.assertRaises(HTTPException) as missing:
                authorized(None)
            self.assertEqual(missing.exception.status_code, 401)

            authorized(HTTPAuthorizationCredentials(scheme="Bearer", credentials="ci-secret"))


if __name__ == "__main__":
    unittest.main()
