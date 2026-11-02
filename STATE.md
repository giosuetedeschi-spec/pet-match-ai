# PetMatch AI — Operational State

Updated: 2026-11-03
Branch: `chore/clean-modules-types-docs`; audit pushed as `bc1775d` (implementation `adef1ff`)
Working tree: separate local `manage.py` demo-login comment remains uncommitted
Merge status: not merged.

## Assistant and compatibility audit follow-up (2026-11-03)

- RAG now rejects low-relevance and out-of-scope prompts (including unsupported species and live shop/price claims), uses the previous user turn for short follow-ups, and routes adoption searches to a read-only public catalog lookup. It adds dog-selection and official breed-standard references with per-entry topic/species/source/review metadata.
- Emergency routing distinguishes ordinary food from toxic/unknown ingestion and directs cat-lily, dog-paracetamol, and unknown-ingestion cases to veterinary help with appropriate sources. Health answers bypass generation and use controlled source text or referral guidance, avoiding reliance on the lexical overlap checker for medical meaning. Adoption-topic model claims retain source-ID and lexical checks, which do not establish entailment. The web proxy rate-limits to 10 requests per minute per client IP.
- The web and Streamlit assistants parse explicit species, city, and child-compatibility filters. Child-compatible results require an explicit positive assessment; unknown compatibility is omitted. City parsing handles multiword locations and the English article before a species. Live-provider generation has a gated test but was not invoked; the default has no API key and makes no external call.
- Commercial inventory/pricing remains out of scope and abstains; breed information remains limited to official standards. Web and Django/Streamlit public matching remain separate rule engines, and the synthetic Kaggle return-risk model is not a validated compatibility model; no common head-to-head or real-outcome evaluation exists.
- The Django compatibility quiz now records existing dogs and cats separately, excludes known conflicts with children/dogs/cats, and exposes cautions for unknown compatibility. Streamlit and web assistant UIs explain the pipeline, citations, catalogue limits, and abstention examples.
- Verification: 20 assistant tests, 12 Django matching/API tests, 21 web tests, migration consistency, Streamlit AppTest (4 tabs), TypeScript typecheck, production Next build, Compose config, and `git diff --check` passed. GitHub Actions run `41544976767` passed all jobs; Compose verified the assistant proxy, catalog filters, and rate limit. The local AppTest assertions passed but Windows emitted a tempfile cleanup `WinError 5`; local Docker Compose remains unavailable because the Docker Desktop Linux engine pipe is missing.
- Existing local `manage.py` change is a separate demo-login comment and must remain unstaged/uncommitted.

CI on the branch passed on Ubuntu 24.04 (GitHub Actions run `38040076466`). It now runs on branch pushes, checks Django matching, typechecks and tests the web app during its image build, and runs ML service contract tests. The full Compose smoke test passed.

## Completed unit

PR #23 added the first public Next.js catalogue backed by published Prisma animal records.

- `/it/animali` shows available animals from active shelters.
- Search supports text, species, size, and pagination.
- The home page links to the Next.js catalogue and the Streamlit MVP.
- The operational roadmap records the current status in `ROADMAP-OPERATIVA.md`.

Commit `26d8cc9` also updated the project documentation, cleaned existing modules, added the Bun lockfile, and repaired the generated Prisma client setup. TypeScript typecheck and the Next.js production build passed; `python manage.py check` passed. A local web smoke check returned 200 for `/`; `/api/health` returned 503 because Docker Desktop and the database were unavailable.

## Current scope and constraints

- Django + Streamlit remains the MVP priority; Next.js + Prisma is a parallel release.
- Next.js shelter animal drafting, validated publication, and photo handling are implemented locally.
- Next.js Prisma uses MySQL, so the new flow was validated against the Compose MySQL service; SQLite cannot run this schema directly. Django MVP media continues to use its local volume.
- FastAPI now serves two authenticated, trained demo models: Austin adoption outcome and conditional stay duration, plus synthetic Kaggle dog-pair return risk. Both are experimental and staff-only; the old Cox artifact remains excluded for target leakage.
- Product requirements and intended architecture are in `docs/`; implementation status is in `ROADMAP-OPERATIVA.md`.

## Audit implementation (2026-11-02)

- Corrected Austin `Sex upon Intake` encoding so “Spayed Female” is not classified as male; retrained and advanced the model version to `austin-adoption-outcome-0.1.1` (ROC-AUC 0.6489; conditional-stay MAE 20.44 days).
- ML prediction payload now provides bucket probabilities, field-level logistic signals, and input completeness. Next.js triage persists and displays those fields plus estimated stay; model limitations remain visible.
- Added a shared authenticated bilingual RAG assistant for Next.js and Streamlit, with a curated citation-bearing corpus, abstention for unsupported prompts, and conservative veterinary guidance for emergency/dosage queries. A language model remains optional; retrieval fallback needs no provider credentials.
- Public matching remains deterministic. The Next.js matcher is authoritative for the portal; Django MVP scoring is separate. Compose uses distinct databases with no synchronization. Removed the localhost Streamlit link from the web home page.
- Added assistant evaluation to CI; improved Streamlit filter layout and theme; added assistant source and safety documentation.
- Verification: assistant evaluation (6 tests), ML tests (4), Django matching tests (3), TypeScript typecheck, production Next build, Streamlit rendering, and `docker compose config` passed. GitHub Actions run `41538497791` passed all jobs, including Compose startup, migrations, assistant retrieval and the Next.js proxy. Local Compose startup could not be run because the Docker Desktop Linux engine named pipe was unavailable.

## MVP adopter compatibility and ML access (2026-10-13)

- Streamlit's public Compatibilità tab keeps the anonymous deterministic ranking and discloses internal ML use without exposing predictions to adopters.
- The authenticated Rifugi area now offers an Austin-trained adoption-outcome classifier and conditional length-of-stay estimate, plus a Kaggle-trained synthetic dog-pair return-risk model. The latter is clearly labelled synthetic and weak (ROC-AUC 0.6172); Austin adoption ROC-AUC is 0.6489 and conditional stay MAE is 20.44 days after correcting female sex encoding and retraining.
- Docker builds the ML image from root context and trains both models from the versioned Austin and Kaggle CSV files in `training-data/`. Source links and upstream license labels, including Kaggle's `Other` label, are documented in `docs/14-mvp-ml-demo.md`.
- Local seed login: `rifugio_esperanza` / `DemoRifugio123!`, limited to `DEBUG=True`; verified with an in-memory SQLite seed and JWT `/users/me/` request. Three ML service unit tests, direct inferences, Python compilation, `manage.py check`, and Compose config passed. Docker live validation is blocked by denied access to the Docker Desktop named pipe.

## Shelter authoring unit (2026-10-09)

- Shelter staff can create and edit drafts, complete the animal and behavior profile, upload photos, and publish when required fields and one processed, accessible photo are ready. Access is restricted to shelter memberships. Onboarding and admin review are now implemented below.
- Photos are validated and normalized with Sharp, metadata is stripped, and WebP sizes are generated. Staff can edit alt text, choose a cover, reorder, and remove photos from the listing; removal is logical and retains the stored bytes. Compose stores them in a persistent local volume; production can use a private S3-compatible bucket.
- The MySQL migration applied successfully. Docker web service is healthy; `/api/health` returned 200, the shelter page redirects unauthenticated users (307), and the shelter API returns 401 without a session. Parser checks accepted a valid draft, rejected an invalid date and microchip, and publication validation accepted a complete profile.
- TypeScript typecheck, six shelter/photo unit tests, and production build passed. Tests cover draft and publish validation, invalid inputs, image derivatives, EXIF orientation and metadata stripping, and unsupported image data. Graphify index was updated. SQLite was not used for this Next.js flow because its Prisma datasource is MySQL.

## Current matching checkpoint

The Next.js matching scope now includes the resumable quiz, saved anonymous/account profiles, score breakdowns, favorites, browse integration, animal details, cache invalidation, optional Claude explanations with deterministic fallback, verified account carry-over, notifications, unsubscribe, and a scheduled digest worker.

Verification on 2026-10-08: Prisma schema validation, TypeScript typecheck, production build, Compose config, 10 automated scoring/digest tests, local page smoke checks, and all three required GitHub CI checks passed. The test suite covers both documented examples (91 and 46), weight total, exclusions, unknown data, the 48-hour policy, and 10,000 animals (<300 ms). GitHub CI started the full Compose stack and verified Next.js-to-MySQL connectivity. A three-person usability run and end-to-end email delivery/unsubscribe test remain outstanding.

## Next planned unit

Usability run with three people and end-to-end email delivery/unsubscribe validation remain. The MVP ML demo now has a reproducible training path; local Docker verification remains.

## Shelter onboarding, ML integration, and translation (2026-10-09)

- Shelter registration validates legal/contact/location data, creates the user, pending shelter, and first membership atomically, then uses the existing email verification. Admins review verified contacts in a protected queue, approve, or reject with a reason. A CLI promotes only an existing verified account to `platform_admin`.
- FastAPI provides health, model-info, single and batch inference behind a bearer token. The old Cox artifact remains excluded for leakage; shelter-only MVP demo models are documented in `docs/14-mvp-ml-demo.md`.
- Self-hosted LibreTranslate/Argos supplies automatic Italian/English text translation at display time. Original text remains in the database and is restored when switching back. Translation failure preserves the source content.
- TypeScript typecheck, the six existing shelter/photo tests, Python compile, Compose config, Next.js production build, Prisma client generation in Docker, and the MySQL migration passed. Live smoke checks returned 200 for web health and registration, 403/401 for unauthenticated admin/shelter APIs, 400 for invalid shelter registration, and a successful Italian-to-English translation. ML health and authorized prediction worked; model-info correctly returned 401 without a token. No test shelter account was created.
- The local Prisma CLI could not download its pinned engine through the sandbox proxy, but Docker build generated the client and the migration container applied the migration successfully.
