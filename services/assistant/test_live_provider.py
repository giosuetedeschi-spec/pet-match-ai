"""Opt-in smoke test for a real provider call; never enabled by default or in CI."""
import os
import unittest

from app import answer


LIVE_PROVIDER_ENABLED = (
    os.getenv("RUN_LIVE_LLM_TEST") == "1"
    and bool(os.getenv("ANTHROPIC_API_KEY"))
    and bool(os.getenv("ANTHROPIC_MODEL"))
)


@unittest.skipUnless(LIVE_PROVIDER_ENABLED, "Set RUN_LIVE_LLM_TEST=1 and provider credentials to opt in")
class LiveProviderSmokeTest(unittest.TestCase):
    def test_real_model_completes_a_cited_non_health_rag_answer(self):
        result = answer("How should I choose a dog that fits my lifestyle?", "en")
        self.assertEqual(result["engine"], "pretrained_model_rag", result)
        self.assertTrue(result["citations"], result)
        allowed_ids = {doc["id"] for doc in result["retrieved"]}
        self.assertTrue(all(set(claim["source_ids"]) <= allowed_ids for claim in result["claims"]), result)


if __name__ == "__main__":
    unittest.main()
