# Shared RAG assistant (demo)

The Next.js portal and Streamlit MVP call the same private FastAPI service. It supports Italian and English with a curated bilingual corpus, a relevance filter, explicit abstention, and an optional Anthropic model. Without provider credentials, answers quote one retrieved source and say they are general information. If generation is enabled, each short claim must cite an exact retrieved source and pass a token-support check; unsupported generation falls back to the source text. The check is a lightweight demo safeguard, not a guarantee of semantic faithfulness.

## Supported scope

- General adoption guidance and choosing a dog for a person's lifestyle.
- Basic dog and cat nutrition, selected emergency/poisoning information, and official dog breed standards.
- Read-only lookup of up to six published, currently available dog/cat profiles. Only public fields are sent to the assistant; profile links point to the web catalogue. The shelter must confirm suitability and current availability.
- Multi-turn context is limited to the most recent conversation turns and is held in the client session only; there is no assistant conversation database.

The assistant abstains on unsupported species (including rabbits), unrelated topics, low-relevance retrieval, and live commercial questions. It does not know store inventory, local sellers, current prices, or enough evidence to endorse a specific food brand. A brand question may receive general WSAVA selection criteria, never a product ranking or endorsement. More sources must be reviewed and added before expanding these supported areas.

## Safety, attribution, and service limits

- The assistant does not diagnose, prescribe, or recommend medication or doses. Dosage/medicine questions and detected emergency symptoms bypass generation and return conservative veterinary-referral guidance. Ordinary ingestion of normal food is not itself an emergency trigger; ingestion of a known or unknown risky substance is.
- Generated claims link to their cited source records. Fallback answers cite only the single source from which their text is taken. The `retrieved` list is diagnostic pipeline output and is not presented as proof for a claim.
- Calls to FastAPI require `CHAT_SERVICE_TOKEN`; the browser only calls the Next.js proxy. The proxy accepts Italian/English text up to 1,200 characters, at most eight short history messages, and limits each client IP to 10 requests per minute in process memory. This is suitable for the demo; a multi-instance deployment needs shared rate-limit storage and trusted proxy IP configuration.
- The model's limitations are shown in the UI. Provider output is not independently clinically validated, and lexical claim/source overlap does not prove semantic entailment.

## Corpus and maintenance

Every entry in `services/assistant/knowledge_base.json` records its locale, topic, supported species, source organization and URL, `verified_at`, and a review interval. Italian and English text are concise paraphrases; confirm the original source when updating an entry and re-review on or before its interval. Current source domains:

- ASPCA Animal Poison Control, [People Foods to Avoid Feeding Your Pets](https://www.aspca.org/pet-care/aspca-poison-control/people-foods-avoid-feeding-your-pets).
- American Veterinary Medical Association, [Pet First Aid](https://ebusiness.avma.org/files/productdownloads/mcm-client-brochures-pet-first-aid-2023.pdf) and [Selecting a Pet Dog](https://avma.org/resources/pet-owners/petcare/selecting-pet-dog).
- World Small Animal Veterinary Association, [Global Nutrition Guidelines](https://wsava.org/Global-Guidelines/Global-Nutrition-Guidelines/).
- Cornell Feline Health Center, [Feeding Your Cat](https://www.vet.cornell.edu/departments-centers-and-institutes/cornell-feline-health-center/health-information/feline-health-topics/feeding-your-cat) and [Poisons](https://www.vet.cornell.edu/departments-centers-and-institutes/cornell-feline-health-center/health-information/feline-health-topics/poisons).
- ENCI, [Official breed standards](https://www.enci.it/documenti-e-pubblicazioni/standard-razze-e-commenti).

This corpus contains general educational paraphrases, not a comprehensive veterinary reference. It has no continuously refreshed commercial/local data.

## Evaluation

`services/assistant/test_app.py` covers supported retrieval (including breed and nutrition), irrelevant and unsupported-species abstention, store/brand handling, ordinary-food versus risky-ingestion routing, urgent and dosage safety, generated claim support and fallback, exact citation behavior, short follow-up context, and read-only catalog lookup. Django matching tests cover child incompatibility exclusions and dog/cat-specific household fields. Compose CI checks the assistant service and the Next.js proxy, including shopping-query abstention, catalog lookup, and the 10-request rate limit.

The Streamlit and web interfaces show the engine, retrieved candidates, answer citations, and sample abstention boundaries as an educational pipeline. GitHub Actions evaluates the service and starts the Compose stack.
