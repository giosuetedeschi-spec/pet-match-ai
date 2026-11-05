# Shared RAG assistant (demo)

The Next.js portal and Streamlit MVP call the same private FastAPI service. It supports Italian and English with a curated bilingual corpus, a relevance filter, explicit abstention, and an optional Anthropic model. Without provider credentials, answers quote one retrieved source. The configured model is used only for non-health adoption guidance; nutrition, poisoning, medication, and emergency answers bypass free-form generation and use controlled text or veterinary referral guidance. For generated non-health claims, exact source IDs and a token-support check are still required. That check does not prove semantic entailment.

## Supported scope

- General adoption guidance and choosing a dog for a person's lifestyle.
- Basic dog and cat nutrition, selected emergency/poisoning information, and official dog breed standards.
- Read-only lookup of up to six published, currently available dog/cat profiles. Species, an explicitly named city, and a request for child compatibility become database filters. Child-compatible results require an explicit positive shelter assessment; unknown values are excluded. The shelter must confirm suitability and current availability.
- Multi-turn context is limited to the most recent conversation turns and is held in the client session only; there is no assistant conversation database.

The assistant abstains on unsupported species (including rabbits), unrelated topics, low-relevance retrieval, and live commercial questions it cannot verify. For online food offers, `services/assistant/commerce.py` searches only the public Isola dei Tesori site, follows at most two product links, and accepts only `Product`/`Offer` JSON-LD with a EUR price and explicit `InStock` or `OutOfStock` value. The service timestamps each fetched offer, applies an overall 11-second lookup budget, caps each response at 1 MB, and allows requests and redirects only to `www.isoladeitesori.it`. Common Italian and English price phrasing is removed before search; returned product names must contain every requested product token. Fetch, redirect, or structured-data errors fail closed with no offers.

This is online availability only. The connector does not check a named physical shop, pickup inventory, or other retailers; queries such as “Quale negozio a Torino vende Royal Canin?” abstain. If an online offer is returned, the UI labels its stock scope as online and separately says physical-store availability was not checked. Current online offer lookup is not a brand recommendation: a brand question may receive general WSAVA selection criteria, never a product ranking or endorsement. Queries for unsupported retailers also abstain instead of substituting Isola dei Tesori. Breed coverage is limited to the official standards reference; the assistant must not infer individual temperament from a breed name. More sources must be reviewed before expanding retailer coverage.

Examples: “Quanto costa Royal Canin Mini Adult 2 kg?” searches the public retailer pages and returns only matching product records with their fetch timestamps. “Is Royal Canin available in Turin?” asks about location-specific stock and abstains. If no exact structured offer can be verified, price and availability are not stated.

## Safety, attribution, and service limits

- The assistant does not diagnose, prescribe, or recommend medication or doses. Dosage/medicine questions and detected emergency symptoms bypass generation and return conservative veterinary-referral guidance. Possible ingestion of a lily by a cat, human medicines including paracetamol/acetaminophen, listed toxins, plants/chemicals, or an unknown item are treated prudently as exposure. Ordinary ingestion of normal food alone is not an emergency trigger. Lily guidance is cat-specific; medication ingestion cites the general pet-poison source rather than a cat-only reference.
- Generated claims link to their cited source records. Fallback answers cite only the single source from which their text is taken. The `retrieved` list is diagnostic pipeline output and is not presented as proof for a claim.
- Calls to FastAPI require `CHAT_SERVICE_TOKEN`; the browser only calls the Next.js proxy. The proxy accepts Italian/English text up to 1,200 characters, at most eight short history messages, and limits each client IP to 10 requests per minute in process memory. This is suitable for the demo; a multi-instance deployment needs shared rate-limit storage and trusted proxy IP configuration.
- Health responses never use the model, so a false claim cannot be accepted merely because it shares words with a medical source. Adoption-topic generation still has no semantic entailment checker and remains a demonstration; provider output is not independently validated.
- `.env.example` selects the currently active Anthropic model ID. The provider stays disabled unless an API key is configured. Without a key, no prompt is sent externally and no provider charge is incurred. To enable generation, add your own `ANTHROPIC_API_KEY` to local `.env`, then restart the assistant/UI services. The opt-in live check sends a fixed generic adoption question to Anthropic and may incur API usage charges; it is never run in CI. Anthropic currently lists `claude-haiku-4-5-20251001` as active; check the [model lifecycle page](https://docs.anthropic.com/en/docs/about-claude/model-deprecations) before refreshing the configuration.

  ```powershell
  $env:ANTHROPIC_API_KEY = "<your key>"
  $env:ANTHROPIC_MODEL = "claude-haiku-4-5-20251001"
  $env:RUN_LIVE_LLM_TEST = "1"
  Set-Location services/assistant
  python -m unittest test_live_provider -v
  ```

  For the web and Streamlit demo, set those values in `.env`, rebuild the `assistant` service, and restart the interfaces. Remove the key afterward. The supported model ID and API lifecycle change over time; check the [Anthropic model lifecycle page](https://docs.anthropic.com/en/docs/about-claude/model-deprecations) before refreshing the configuration.

## Corpus and maintenance

Every entry in `services/assistant/knowledge_base.json` records its locale, topic, supported species, source organization and URL, `verified_at`, and a review interval. Italian and English text are concise paraphrases; confirm the original source when updating an entry and re-review on or before its interval. Current source domains:

- ASPCA Animal Poison Control, [People Foods to Avoid Feeding Your Pets](https://www.aspca.org/pet-care/aspca-poison-control/people-foods-avoid-feeding-your-pets).
- American Veterinary Medical Association, [Pet First Aid](https://ebusiness.avma.org/files/productdownloads/mcm-client-brochures-pet-first-aid-2023.pdf) and [Selecting a Pet Dog](https://avma.org/resources/pet-owners/petcare/selecting-pet-dog).
- World Small Animal Veterinary Association, [Global Nutrition Guidelines](https://wsava.org/Global-Guidelines/Global-Nutrition-Guidelines/).
- Cornell Feline Health Center, [Feeding Your Cat](https://www.vet.cornell.edu/departments-centers-and-institutes/cornell-feline-health-center/health-information/feline-health-topics/feeding-your-cat) and [Poisons](https://www.vet.cornell.edu/departments-centers-and-institutes/cornell-feline-health-center/health-information/feline-health-topics/poisons).
- ENCI, [Official breed standards](https://www.enci.it/documenti-e-pubblicazioni/standard-razze-e-commenti).
- ASPCA Animal Poison Control, [Lily toxicity](https://www.aspca.org/pet-care/aspca-poison-control/toxic-and-non-toxic-plants/lily) and [common pet toxins in bags, including human pain relievers](https://www.aspca.org/news/what-pet-toxins-are-hiding-in-your-diaper-bag).

This corpus contains general educational paraphrases, not a comprehensive veterinary reference. Online offers are fetched from a single official retailer at request time; there is no local-store stock feed or broad retailer coverage.

## Evaluation

`services/assistant/test_app.py` covers supported retrieval, unsupported-topic abstention, verified and unavailable commerce, store/brand handling, ordinary-food versus toxin/plant/medicine/unknown-ingestion routing, species-correct citations, controlled health answers despite a simulated contradictory generation, generated adoption-claim checks, provider request parsing, short follow-up context, and filtered catalog responses. `services/assistant/test_commerce.py` covers structured online offers, timestamps, query normalization and product matching, page limits, redirect allowlisting, fail-closed behavior, and local-store abstention. `test_live_provider.py` is opt-in and tests a real provider call only when explicitly enabled. Web query-parser tests check species, city, child filters, and the commerce engine label. Django matching tests cover child incompatibility exclusions and dog/cat-specific household fields. Compose CI checks the assistant service and Next.js proxy, including commercial-query abstention, catalog empty-state/filters, and the 10-request rate limit.

The Streamlit and web interfaces show the engine, retrieved candidates, answer citations, and sample abstention boundaries as an educational pipeline. GitHub Actions evaluates the service and starts the Compose stack.
