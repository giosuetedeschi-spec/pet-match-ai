import unittest
import json
from unittest.mock import patch

from app import ChatRequest, _generate, answer, chat, retrieve
from commerce import CommerceOffer


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
        with patch("app.lookup_offers", return_value=[]):
            result = answer("Quale negozio di animali a Torino vende Royal Canin?", "it")
        self.assertEqual(result["engine"], "no_answer")
        self.assertEqual(result["citations"], [])

    def test_live_commerce_offer_is_returned_with_online_scope_and_timestamp(self):
        offer = CommerceOffer("L'Isola dei Tesori", "Royal Canin Mini Adult 2 kg", "Royal Canin", "https://www.isoladeitesori.it/prodotto/item.html", "22.49", "EUR", "available", "online", "2026-11-05T00:00:00+00:00")
        with patch("app.lookup_offers", return_value=[offer]):
            result = answer("Prezzo Royal Canin Mini Adult", "it")
        self.assertEqual(result["engine"], "commerce_lookup")
        self.assertEqual(result["commerce_offers"][0]["price_amount"], "22.49")
        self.assertEqual(result["commerce_offers"][0]["availability_scope"], "online")
        self.assertIn("negozi fisici non è inclusa", result["answer"])
        self.assertEqual(result["citations"], [])

    def test_live_commerce_abstains_when_no_offer_is_verified(self):
        with patch("app.lookup_offers", return_value=[]):
            result = answer("Current price for Royal Canin Mini Adult", "en")
        self.assertEqual(result["engine"], "no_answer")
        self.assertEqual(result["commerce_offers"], [])
        self.assertTrue(result["abstained"])
        self.assertIn("can't confirm price or availability", result["answer"])

    def test_rabbit_food_question_abstains_instead_of_showing_cat_guidance(self):
        result = answer("Quale cibo per un coniglio?", "it")
        self.assertEqual(result["engine"], "no_answer")
        self.assertEqual(result["citations"], [])

    def test_normal_food_does_not_trigger_emergency(self):
        result = answer("Il mio cane ha mangiato cibo normale", "it")
        self.assertNotEqual(result["engine"], "safety_guidance")

    def test_cat_lily_ingestion_routes_to_cat_specific_veterinary_guidance(self):
        result = answer("Il mio gatto ha mangiato un giglio", "it")
        self.assertEqual(result["engine"], "safety_guidance")
        self.assertEqual(result["citations"][0]["id"], "lily-cat-it")
        self.assertIn("veterinario", result["answer"])

    def test_dog_paracetamol_ingestion_uses_general_animal_poison_source(self):
        result = answer("Il mio cane ha ingerito paracetamolo", "it")
        self.assertEqual(result["engine"], "safety_guidance")
        self.assertEqual(result["citations"][0]["id"], "pain-relief-it")

    def test_unknown_ingestion_is_routed_prudently(self):
        result = answer("My dog may have eaten something", "en")
        self.assertEqual(result["engine"], "safety_guidance")
        self.assertEqual(result["citations"][0]["id"], "emergency-en")

    def test_unknown_question_says_it_does_not_know(self):
        result = answer("Quanto misura la luna di Saturno?", "it")
        self.assertEqual(result["engine"], "no_answer")
        self.assertEqual(result["citations"], [])
        self.assertTrue(result["abstained"])

    def test_emergency_avoids_model_and_sends_to_veterinarian(self):
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "unused", "ANTHROPIC_MODEL": "unused"}), patch("app._generate") as generate:
            result = answer("My dog ate grapes", "en")
        self.assertEqual(result["engine"], "safety_guidance")
        self.assertIn("contact your veterinarian", result["answer"].lower())
        self.assertIn(result["citations"][0]["id"], {"poison-foods-en", "emergency-en"})
        generate.assert_not_called()

    def test_dosage_request_never_calls_model(self):
        with patch("app._generate") as generate:
            result = answer("Quanto ibuprofene posso dare al cane?", "it")
        self.assertEqual(result["engine"], "safety_guidance")
        self.assertIn("dose", result["answer"])
        generate.assert_not_called()

    def test_fallback_cites_only_the_source_used(self):
        result = answer("Come scelgo un cane adatto al mio stile di vita?", "it")
        self.assertEqual(result["engine"], "retrieval_fallback")
        self.assertEqual(len(result["citations"]), 1)
        self.assertEqual(result["claims"][0]["source_ids"], [result["citations"][0]["id"]])

    def test_model_claim_without_source_support_is_rejected(self):
        unsupported = [{"text": "Lifestyle and exercise should not determine whether a dog is a fit.", "source_ids": ["dog-selection-en"]}]
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "unused", "ANTHROPIC_MODEL": "unused"}), patch("app._generate", return_value=unsupported):
            result = answer("How should I choose a dog that fits my lifestyle?", "en")
        self.assertEqual(result["engine"], "retrieval_fallback")
        self.assertNotIn("should not determine", result["answer"])

    def test_verbatim_model_claim_has_its_source_attached(self):
        claims = [{"text": "Choosing a dog should take into account your family, home, lifestyle, time, exercise, and the veterinary care you can provide long term.", "source_ids": ["dog-selection-en"]}]
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "unused", "ANTHROPIC_MODEL": "unused"}), patch("app._generate", return_value=claims):
            result = answer("How should I choose a dog that fits my lifestyle?", "en")
        self.assertEqual(result["engine"], "pretrained_model_rag")
        self.assertEqual(result["claims"][0]["source_ids"], ["dog-selection-en"])
        self.assertEqual([source["id"] for source in result["citations"]], ["dog-selection-en"])

    def test_generated_paraphrase_uses_controlled_source_fallback(self):
        claims = [{"text": "Consider the household, daily routine and long-term care you can offer.", "source_ids": ["dog-selection-en"]}]
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "unused", "ANTHROPIC_MODEL": "unused"}), patch("app._generate", return_value=claims):
            result = answer("How should I choose a dog that fits my lifestyle?", "en")
        self.assertEqual(result["engine"], "retrieval_fallback")
        self.assertEqual(result["answer"], retrieve("How should I choose a dog that fits my lifestyle?", "en")[0]["text"] + " This is general information, not an individual veterinary assessment.")

    def test_anthropic_messages_adapter_parses_a_generated_answer(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({"content": [{"type": "text", "text": json.dumps({"claims": [{"text": "Choose based on lifestyle, time, and exercise.", "source_ids": ["dog-selection-en"]}]})}]}).encode()

        sources = retrieve("How should I choose a dog that fits my lifestyle?", "en")
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key", "ANTHROPIC_MODEL": "test-model"}), patch("app.urllib.request.urlopen", return_value=FakeResponse()) as urlopen:
            generated = _generate("How should I choose a dog that fits my lifestyle?", sources, "en", [])
        self.assertEqual(generated[0]["source_ids"], ["dog-selection-en"])
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.anthropic.com/v1/messages")
        self.assertEqual(json.loads(request.data)["model"], "test-model")

    def test_generation_prompt_requires_verbatim_complete_source_sentences(self):
        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return json.dumps({"content": [{"type": "text", "text": "{\"claims\": []}"}]}).encode()

        sources = retrieve("How should I choose a dog that fits my lifestyle?", "en")
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key", "ANTHROPIC_MODEL": "test-model"}), patch("app.urllib.request.urlopen", return_value=FakeResponse()) as urlopen:
            _generate("How should I choose a dog that fits my lifestyle?", sources, "en", [])
        payload = json.loads(urlopen.call_args.args[0].data)
        system_prompt = payload["system"]
        self.assertIn("one complete source sentence copied verbatim", system_prompt)
        self.assertIn("copied exactly, including wording and punctuation", system_prompt)
        self.assertIn("do not paraphrase or combine sources", system_prompt)

    def test_health_claim_generation_is_disabled_even_if_it_contradicts_source(self):
        unsafe = [{"text": "Chocolate is safe for dogs.", "source_ids": ["poison-foods-en"]}]
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "configured", "ANTHROPIC_MODEL": "configured"}), patch("app._generate", return_value=unsafe) as generate:
            result = answer("What should I know about dog food and nutrition?", "en")
        self.assertEqual(result["engine"], "controlled_source")
        self.assertNotIn("safe for dogs", result["answer"])
        generate.assert_not_called()

    def test_specific_breed_temperament_claim_abstains(self):
        result = answer("Qual e il temperamento del Border Collie?", "it")
        self.assertEqual(result["engine"], "no_answer")
        self.assertEqual(result["citations"], [])

    def test_short_followup_uses_previous_user_question_for_retrieval(self):
        result = answer("How often?", "en", history=[{"role": "user", "content": "How should I choose dog food nutrition?"}])
        self.assertEqual(result["citations"][0]["id"], "nutrition-en")

    def test_catalog_lookup_returns_only_passed_published_matches(self):
        animal = {"name": "Luna", "species": "cat", "breed": "Mixed", "city": "Torino", "shelter": "Rifugio", "slug": "luna"}
        result = answer("Can you find me a cat to adopt?", "en", catalog_animals=[animal], catalog_filters={"species": "cat", "city": "Torino", "good_with_children": True})
        self.assertEqual(result["engine"], "catalog_lookup")
        self.assertEqual(result["catalog_animals"], [animal])
        self.assertEqual(result["catalog_filters"], {"species": "cat", "city": "Torino", "good_with_children": True})
        self.assertEqual(result["citations"], [])

    def test_chat_preserves_catalog_animal_id(self):
        request = ChatRequest(
            message="Can you find me a cat to adopt?",
            locale="en",
            catalog_animals=[{"id": 42, "name": "Luna", "species": "cat", "slug": "luna"}],
        )
        result = chat(request)
        self.assertEqual(result["engine"], "catalog_lookup")
        self.assertEqual(result["catalog_animals"][0]["id"], 42)


if __name__ == "__main__":
    unittest.main()
