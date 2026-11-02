# Shared RAG assistant (demo)

The web portal and Streamlit MVP call the same private FastAPI service. It supports Italian and English using a small, curated bilingual corpus. Retrieval works without provider credentials; if `ANTHROPIC_API_KEY` and `ANTHROPIC_MODEL` are configured, Claude can summarize only the retrieved references. Provider failure falls back to cited source text.

## Safety and limits

- Sources are informational, not a substitute for a veterinarian.
- Suspected poisoning, breathing problems, choking, seizures, collapse, and medication or dosage questions bypass generation and return conservative veterinary referral guidance.
- The assistant does not diagnose, prescribe, or give medication doses.
- Unsupported questions return an explicit insufficient-source response.
- Responses include source organization, title, URL, and verification date. The corpus is small and is not a veterinary triage system.
- Calls require `CHAT_SERVICE_TOKEN`; the browser only calls the Next.js proxy and never receives the service credential or provider key.

## Evaluation

`services/assistant/test_app.py` checks Italian toxicity retrieval, English nutrition retrieval, abstention for unrelated questions, urgent-ingestion routing, dosage safety, and citation-bearing fallback output. GitHub Actions compiles and evaluates the service. Compose health-checks the service and makes it a dependency of both UIs.

## Current curated sources

- ASPCA Animal Poison Control, [People Foods to Avoid Feeding Your Pets](https://www.aspca.org/pet-care/aspca-poison-control/people-foods-avoid-feeding-your-pets).
- American Veterinary Medical Association, [Pet First Aid](https://ebusiness.avma.org/files/productdownloads/mcm-client-brochures-pet-first-aid-2023.pdf).
- World Small Animal Veterinary Association, [Global Nutrition Guidelines](https://wsava.org/Global-Guidelines/Global-Nutrition-Guidelines/).
- Cornell Feline Health Center, [Feeding Your Cat](https://www.vet.cornell.edu/departments-centers-and-institutes/cornell-feline-health-center/health-information/feline-health-topics/feeding-your-cat) and [Poisons](https://www.vet.cornell.edu/departments-centers-and-institutes/cornell-feline-health-center/health-information/feline-health-topics/poisons).

The Italian and English entries are concise paraphrases that link to those references. Recheck source content and update `verified_at` when refreshing the corpus.
