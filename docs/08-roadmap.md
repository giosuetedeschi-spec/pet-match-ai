# 08 — Build Roadmap

Five phases. **Every phase ends with an application you can run, use, and judge.** No phase leaves the product in a state where the only way to evaluate progress is to read code.

Effort figures assume one developer working with AI assistance and are calibrated in working days, not calendar days. They are estimates, not commitments — the exit criteria are what actually define "done".

```
Phase 1  Foundation ────▶ a real, bilingual, public catalogue managed by real shelters
Phase 2  Matching   ────▶ the quiz, the scoring engine, explained results
Phase 3  Intelligence ──▶ the ML pipeline, predictions, shelter analytics
Phase 4  Journey    ────▶ applications, visits, notifications
Phase 5  Assistant & money ▶ the chatbot, Stripe, admin console
```

Sequencing rationale: the catalogue is the substrate everything else operates on, so it comes first. Matching precedes ML because it needs no training pipeline and delivers the product's headline promise on the smallest foundation. ML precedes the application journey because the training work is the highest-uncertainty item and should not be discovered to be hard in the final week. The assistant is last because it is the most dependent on real content and the easiest to descope under pressure.

---

## Phase 1 — Foundation

**~15–20 days.** The goal: a shelter can register, be approved, enter its animals, and have them appear on a fast, bilingual public site that anyone can search.

**Scope**
- Docker Compose environment: MySQL, MinIO, ML placeholder, mail catcher, web app
- Prisma schema for identity, shelters, animals, media, behaviour, medical, intakes, outcomes, comuni, consents, audit, jobs
- Seed script producing the development dataset from [03](./03-database-schema.md) §15
- Auth: registration, email verification, login, password reset, sessions, the three roles, route and query guards
- Shelter registration → admin approval → activation
- Shelter members: invite, accept, remove
- Animal CRUD: identity, behaviour profile, medical log, vaccinations, publication validation, status transitions
- Media pipeline: signed upload, derivatives, ordering, primary photo, alt text, video with poster
- Public catalogue: browse, filters, facets, distance search, map view, animal profile, shelter directory and profile
- i18n end to end: routing, catalogues, per-language content columns, fallback labelling
- Design system: tokens, typography, restyled primitives, the components Phase 1 screens need
- GDPR baseline: cookie banner, privacy and cookie policies, consent records, account deletion
- SEO: metadata, structured data on animal pages, sitemap, robots, canonicals, hreflang

**Exit criteria**
- [ ] `docker compose up` on a clean machine yields a seeded, working site with no external credentials
- [ ] A shelter can be registered, approved, and publish an animal with photos in under 15 minutes without documentation
- [ ] Publication is blocked with clear per-field errors when required fields are missing
- [ ] Distance search returns correct results, verified against hand-computed distances for five known comune pairs
- [ ] Every public page renders in both locales with no missing-key warnings; CI fails on a missing key
- [ ] A shelter member cannot read or write another shelter's data — proven by tests, not inspection
- [ ] Lighthouse: performance ≥ 90 and accessibility ≥ 95 on home, browse and animal profile
- [ ] axe reports zero critical issues on every Phase 1 screen
- [ ] The animal editor is fully usable at 390 px width

**Risks**
- Media pipeline complexity (HEIC, video transcoding) — mitigate by shipping photos first and video behind a flag.
- Comuni dataset quality — validate coverage and coordinates during seeding, not at first use.

---

## Phase 2 — Matching

**~10–12 days.** The goal: an adopter answers 14 questions and receives ranked, explained matches — and can save the profile to keep receiving them.

**Scope**
- Scoring engine as pure functions, exactly per [06](./06-matching-algorithm.md)
- Quiz: 14 steps, progress, back navigation, resume, anonymous completion
- Results page: ranked cards, score badges, reason bullets, considerations, exclusion reporting, radius widening
- Match breakdown view
- Adopter profiles: save, edit, delete; anonymous-to-account carry-over
- Favourites
- Match caching and invalidation on relevant changes
- Claude-written explanations with the deterministic bullets as the always-present fallback
- Re-matching job and digest notifications (in-app + email)
- Match integration into browse (`sort=match`) and the animal profile panel

**Exit criteria**
- [ ] The weights sum to 1.00, asserted by a test
- [ ] Both worked examples in [06](./06-matching-algorithm.md) §5 are encoded as tests and produce 91 and 46
- [ ] Deal-breakers exclude rather than penalise, and the count and reasons are reported to the user
- [ ] Safety exclusions (young children, existing pets) apply regardless of stated deal-breakers
- [ ] `unknown` behaviour fields score 65 and always produce a visible consideration
- [ ] Results render fully with `ANTHROPIC_API_KEY` unset
- [ ] Quiz completion is under four minutes in a timed run with three people who have not seen it
- [ ] Scoring 10,000 animals against one profile completes in under 300 ms
- [ ] A digest is sent at most once per 48 hours per profile, and one-click unsubscribe works without login

**Risks**
- Weights are judgement, not evidence (acknowledged in [06](./06-matching-algorithm.md) §8) — mitigate by having two shelter operators review the worked examples before the phase closes.

---

## Phase 3 — Intelligence

**~12–15 days.** The goal: shelter staff open the dashboard and immediately see which animals need help and why.

**Scope**
- Colab exploration per [11](./11-training-workflow.md), graduating to repository scripts by the end of the phase
- ETL from the Kaggle CSVs to processed parquet with a row-count report, retaining right-censored stays
- `features.py` shared by notebooks, training and serving
- **3a** — comparators (classifier, regressor) plus the three baselines, temporal split, per-segment metrics, calibration; unblocks the API and dashboard
- **3b** — **the primary model**: competing-risks survival, same features and split, censored stays included; validate per-prediction attribution here
- **3c** — head-to-head on concordance and bucket calibration; survival ships unless it loses, and the numbers are recorded either way
- Auto-generated model card
- FastAPI service with the contract in [04](./04-api-contracts.md) §4, plus `/health` and `/model-info`
- Typed ML client in the web app, with timeout, degradation and no inline retry
- Nightly batch prediction job; on-publish and on-change triggers
- Shelter dashboard: KPI tiles, charts, date ranges
- At-risk triage list with factors, rule-based advisories, dismissible suggested actions
- Prediction display on the animal record, with caveats
- Admin: model status, prediction volume, realised-accuracy scaffolding

**Exit criteria**
- [ ] ETL is reproducible from raw CSVs with a documented row count at every step, including the censored count
- [ ] A test asserts identical features from the training path and the serving path for the same input
- [ ] The survival model beats all three baselines on concordance on the temporal test split
- [ ] Censored stays reach the survival model as censored observations — asserted by a test
- [ ] The head-to-head against the comparators is recorded with its numbers, whichever way it goes
- [ ] Per-prediction attribution populates `top_factors` for every row in the triage list
- [ ] Every released artifact carries the full reproducibility record from [11](./11-training-workflow.md) §4
- [ ] Training runs from a single command in the repository, not only from a notebook
- [ ] Calibration error under 0.05 or isotonic calibration applied
- [ ] Metrics reported by species, age band and size; under-performing segments suppressed in the UI
- [ ] The model card renders verbatim in the shelter UI
- [ ] With the ML service stopped, the dashboard degrades to a labelled "not available" state and nothing 500s
- [ ] Nightly batch handles 10,000 animals within its window
- [ ] No prediction is reachable from any public page — asserted by a test over the public serialisers
- [ ] The limitations from [05](./05-ml-spec.md) §8 are visible in-product

**Risks**
- Model quality may disappoint on transfer. Mitigation: the bucketed classifier and relative ranking are the primary UI, absolute day counts secondary; if a segment is unreliable it is suppressed, and that is a legitimate outcome rather than a failure.

---

## Phase 4 — Journey

**~12–15 days.** The goal: an adopter applies, the shelter decides, a visit is booked, and both sides know what is happening at every step.

**Scope**
- Application draft, edit, submit (idempotent), withdraw; profile snapshot at submission
- Full state machine with `application_events` on every transition
- Shelter queue: filters, detail view, request info, approve, reject with reason, internal notes
- Adopter tracking: timeline, status, expectations
- Availability slots: creation, recurrence, blackout dates, capacity
- Booking with race-safe capacity, reschedule, cancel, calendar file, reminders
- Visit outcomes: completed, no-show, cancelled; conversion to adoption with an outcome record
- Notification infrastructure: preferences, in-app centre, email templates, WhatsApp templates and opt-in, delivery tracking and retry
- Automatic expiry of stale applications

**Exit criteria**
- [ ] Every transition in [01](./01-product-spec.md) §E4 is implemented and every illegal transition rejected with `invalid_state_transition`
- [ ] Two concurrent bookings for the last place in a slot produce exactly one success and one `slot_full` — verified by a concurrency test
- [ ] Duplicate submits with the same idempotency key create one application
- [ ] Adopter-facing responses never leak internal notes — asserted by a test
- [ ] Every notification renders correctly in both locales across all three channels
- [ ] WhatsApp requires explicit opt-in with a consent record, and `STOP` revokes it end to end
- [ ] Marking an adoption creates the outcome record and de-publishes the listing with a redirect
- [ ] End-to-end test: browse → match → apply → approve → book → complete → adopted

**Risks**
- WhatsApp Business approval is an external dependency with real lead time. Mitigation: the channel is an adapter behind the notification interface; if approval is not granted, phase 4 ships with in-app and email and the channel is enabled later without code changes.

---

## Phase 5 — Assistant and money

**~12–15 days.** The goal: questions get answered without a human, and the platform can sustain itself.

**Scope**
- Knowledge base: ~25 articles per locale, authored and reviewed; the same rows render the public guides
- Chunking, embedding, in-process retrieval with a swappable interface
- Adopter assistant: streaming chat, tools, citations, inline animal cards, rate limits, refusal behaviour
- Staff assistant: shelter-scoped querying, description drafting for human approval
- Cost tracking per conversation, plan quotas, platform budget alerts
- Admin AI monitoring: volume, cost, errors, flagged exchanges
- Stripe: shelter subscriptions, checkout, portal, webhooks, plan enforcement, invoices
- Donations: one-off and recurring, shelter attribution, receipts, anonymity
- Welcome Kit programmes (Epic K): rule-based eligibility on objective public criteria, badge and programme page, grant on completed adoption, shelter opt-out, admin programme management, effectiveness tracking
- Platform admin console completion: moderation, metrics, audit viewer, feature flags
- Launch readiness: error reporting, uptime monitoring, backup and restore rehearsal, legal pages finalised

**Exit criteria**
- [ ] The assistant answers the 20 most common shelter questions correctly, with citations, in both languages
- [ ] The staff assistant cannot read another shelter's data under any prompt — verified by an adversarial test set including direct injection attempts
- [ ] Drafted descriptions are never written to an animal record without an explicit human action
- [ ] Every assistant reply carries the AI disclosure
- [ ] With no Anthropic key, the widget shows the static fallback and nothing errors
- [ ] Stripe webhooks are idempotent on event id; a replayed event changes nothing
- [ ] Exceeding a plan limit blocks new creation with a clear message and never hides or deletes existing data
- [ ] A downgrade never deletes data
- [ ] A donation produces a receipt and, when attributed, is visible to the shelter without exposing the donor when anonymous
- [ ] Welcome Kit eligibility references only objective public criteria — a test asserts no code path reads `predictions` when computing it
- [ ] A kit grant can only be marked granted once its application reaches `completed`
- [ ] Kit badge copy contains none of the prohibited framings, and a shelter opt-out removes the badge immediately
- [ ] A restore-from-backup rehearsal succeeds on a clean environment

**Risks**
- Assistant cost. Mitigation: prompt caching, strict rate limits, per-plan quotas, budget alerts, and a hard cut-off that degrades to the static fallback rather than producing an unbounded bill.
- Prompt injection through shelter-authored content. Mitigation: no write tools at all, delimited untrusted content, adversarial tests in CI.

---

## Testing strategy

| Layer | Tool | Covers |
|---|---|---|
| Unit | Vitest | Scoring engine (exhaustive), feature transforms, validators, permission matrix, state machine, distance maths |
| Unit (Python) | pytest | ETL steps, feature engineering, model loading, prediction shapes |
| Integration | Vitest + real MySQL in CI | API routes, tenancy isolation, transactions, idempotency, concurrency |
| End-to-end | Playwright | Three critical journeys (below), in both locales |
| Accessibility | axe-core in Playwright | Every key screen, every phase |
| Visual | Playwright snapshots | Key components, light and dark |
| Contract | Generated from the FastAPI OpenAPI schema | Web ↔ ML compatibility |
| Adversarial | Custom suite | Assistant injection, cross-tenant access, authorisation bypass |
| Load | k6, before launch | Search at 10k animals, batch prediction, concurrent booking |

**The three critical journeys**, tested end to end from Phase 4 onward and run on every commit:
1. Adopter: browse → quiz → results → animal → apply → track
2. Shelter: register → approve → create animal → publish → appears publicly with correct data
3. Full loop: apply → shelter reviews → approves → adopter books → visit completed → adopted → listing de-published

**Coverage targets:** 90%+ on the matching engine and permission layer (these are correctness-critical and cheap to test), 70%+ overall. Coverage is a floor for the parts that matter, not a number to chase everywhere.

## Definition of done

A phase is done when all of the following hold, not when the features appear to work:

- [ ] Exit criteria met and demonstrated on a clean environment
- [ ] Tests written and passing at the layers above; CI green
- [ ] Both locales complete, no missing keys
- [ ] axe clean on new screens; keyboard pass done manually
- [ ] Mobile verified at 390 px on every new screen
- [ ] Errors handled with the standard envelope and a user-facing recovery path
- [ ] Loading and empty states present on every new surface
- [ ] Degradation verified with each external dependency disabled in turn
- [ ] Documentation in `docs/` updated where the build diverged from the plan — **divergence is expected; silent divergence is not**
- [ ] Seed data extended to exercise the new features
- [ ] No secrets in the repository; no personal data in logs

## Cross-phase engineering standards

- **Branching.** Feature branches, PR to main, CI must pass. No direct pushes to main.
- **Migrations.** Forward-only, reviewed, never edited after merge, always tested against seeded data.
- **Commits.** Conventional commits, scoped by area.
- **Dependencies.** Added deliberately; each new one justified in the PR description.
- **Secrets.** Environment only, never committed; a secret scanner runs in CI.
- **Performance budget.** Enforced in CI on the public routes — a regression fails the build rather than being noticed in production.

## Post-launch, deliberately deferred

Not scheduled, and not to be pulled forward without an explicit decision: PWA and offline shelter access, a structured fostering programme, adoption follow-up surveys at 1/6/12 months (the real measure of match quality), a public API for partners, regional anagrafe integration if one ever becomes available, additional locales, native applications, and revisiting learned matching once 12 months of real outcome data exists — see [06](./06-matching-algorithm.md) §8.
