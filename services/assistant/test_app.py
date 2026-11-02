import unittest
from unittest.mock import patch

from app import answer, retrieve


class RetrievalEvaluationTests(unittest.TestCase):
    def test_food_toxicity_retrieves_aspca_guidance(self):
        self.assertEqual(retrieve("Il cane ha mangiato cioccolato", "it")[0]["id"], "poison-foods-it")

    def test_nutrition_question_retrieves_wsava(self):
        self.assertEqual(retrieve("how should I choose dog food nutrition", "en")[0]["id"], "nutrition-en")

    def test_unknown_question_says_it_does_not_know(self):
        result = answer("Quanto misura la luna di Saturno?", "it")
        self.assertEqual(result["engine"], "no_answer")
        self.assertEqual(result["citations"], [])

    def test_emergency_avoids_model_and_sends_to_veterinarian(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "unused", "ANTHROPIC_MODEL": "unused"}), patch("app._generate") as generate:
            result = answer("My dog ate grapes", "en")
        self.assertEqual(result["engine"], "safety_guidance")
        self.assertIn("contact your veterinarian", result["answer"])
        self.assertEqual(result["citations"][0]["id"], "poison-foods-en")
        generate.assert_not_called()

    def test_dosage_request_never_calls_model(self):
        with patch("app._generate") as generate:
            result = answer("Quanto ibuprofene posso dare al cane?", "it")
        self.assertEqual(result["engine"], "safety_guidance")
        self.assertIn("dose", result["answer"])
        generate.assert_not_called()

    def test_supported_answer_includes_verifiable_citation_and_fallback_state(self):
        result = answer("Come scelgo il cibo per il gatto?", "it")
        self.assertEqual(result["engine"], "retrieval_fallback")
        self.assertTrue(result["citations"])
        self.assertIn("Cornell", " ".join(item["organization"] for item in result["citations"]))


if __name__ == "__main__":
    unittest.main()
