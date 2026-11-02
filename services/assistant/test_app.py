import unittest
from unittest.mock import patch

from app import answer, retrieve


class RetrievalEvaluationTests(unittest.TestCase):
    def test_food_toxicity_retrieves_aspca_guidance(self):
        result = answer("Il cane ha mangiato cioccolato", "it")
        self.assertEqual(result["engine"], "safety_guidance")
        self.assertEqual(result["citations"][0]["id"], "poison-foods-it")

    def test_nutrition_question_retrieves_wsava(self):
        self.assertEqual(retrieve("how should I choose dog food nutrition", "en")[0]["id"], "nutrition-en")

    def test_official_breed_standards_topic_is_retrievable(self):
        self.assertEqual(retrieve("standard ufficiali FCI ENCI razze canine", "it")[0]["id"], "breed-standards-it")

    def test_store_brand_question_abstains_instead_of_using_emergency_source(self):
        result = answer("Quale negozio di animali a Torino vende Royal Canin?", "it")
        self.assertEqual(result["engine"], "no_answer")
        self.assertEqual(result["citations"], [])

    def test_rabbit_food_question_abstains_instead_of_showing_cat_guidance(self):
        result = answer("Quale cibo per un coniglio?", "it")
        self.assertEqual(result["engine"], "no_answer")
        self.assertEqual(result["citations"], [])

    def test_normal_food_does_not_trigger_emergency(self):
        result = answer("Il mio cane ha mangiato cibo normale", "it")
        self.assertNotEqual(result["engine"], "safety_guidance")

    def test_unknown_question_says_it_does_not_know(self):
        result = answer("Quanto misura la luna di Saturno?", "it")
        self.assertEqual(result["engine"], "no_answer")
        self.assertEqual(result["citations"], [])
        self.assertTrue(result["abstained"])

    def test_emergency_avoids_model_and_sends_to_veterinarian(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "unused", "ANTHROPIC_MODEL": "unused"}), patch("app._generate") as generate:
            result = answer("My dog ate grapes", "en")
        self.assertEqual(result["engine"], "safety_guidance")
        self.assertIn("contact your veterinarian", result["answer"])
        self.assertIn(result["citations"][0]["id"], {"poison-foods-en", "emergency-en"})
        generate.assert_not_called()

    def test_dosage_request_never_calls_model(self):
        with patch("app._generate") as generate:
            result = answer("Quanto ibuprofene posso dare al cane?", "it")
        self.assertEqual(result["engine"], "safety_guidance")
        self.assertIn("dose", result["answer"])
        generate.assert_not_called()

    def test_fallback_cites_only_the_source_used(self):
        result = answer("Come scelgo il cibo per il gatto?", "it")
        self.assertEqual(result["engine"], "retrieval_fallback")
        self.assertEqual(len(result["citations"]), 1)
        self.assertEqual(result["claims"][0]["source_ids"], [result["citations"][0]["id"]])

    def test_model_claim_without_source_support_is_rejected(self):
        unsupported = [{"text": "Buy this product at the best store today", "source_ids": ["nutrition-en"]}]
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "unused", "ANTHROPIC_MODEL": "unused"}), patch("app._generate", return_value=unsupported):
            result = answer("How should I choose dog food nutrition?", "en")
        self.assertEqual(result["engine"], "retrieval_fallback")
        self.assertNotIn("best store", result["answer"])

    def test_supported_model_claim_has_its_source_attached(self):
        claims = [{"text": "Nutrition guidelines advise checking food quality and completeness.", "source_ids": ["nutrition-en"]}]
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "unused", "ANTHROPIC_MODEL": "unused"}), patch("app._generate", return_value=claims):
            result = answer("How should I choose dog food nutrition?", "en")
        self.assertEqual(result["engine"], "pretrained_model_rag")
        self.assertEqual(result["claims"][0]["source_ids"], ["nutrition-en"])
        self.assertEqual([source["id"] for source in result["citations"]], ["nutrition-en"])

    def test_specific_breed_temperament_claim_abstains(self):
        result = answer("Qual e il temperamento del Border Collie?", "it")
        self.assertEqual(result["engine"], "no_answer")
        self.assertEqual(result["citations"], [])

    def test_short_followup_uses_previous_user_question_for_retrieval(self):
        result = answer("How often?", "en", history=[{"role": "user", "content": "How should I choose dog food nutrition?"}])
        self.assertEqual(result["citations"][0]["id"], "nutrition-en")

    def test_catalog_lookup_returns_only_passed_published_matches(self):
        animal = {"name": "Luna", "species": "cat", "breed": "Mixed", "city": "Torino", "shelter": "Rifugio", "slug": "luna"}
        result = answer("Can you find me a cat to adopt?", "en", catalog_animals=[animal])
        self.assertEqual(result["engine"], "catalog_lookup")
        self.assertEqual(result["catalog_animals"], [animal])
        self.assertEqual(result["citations"], [])


if __name__ == "__main__":
    unittest.main()
