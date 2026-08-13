# INDEX — read this first

**Purpose of this file:** the documentation set is ~42,000 words. This index exists so you do not have to read it. It carries the product in one paragraph, a routing table from question to document, every normative constant in one place, and the hard rules that must never be broken. Read the full document only when you are about to build the thing it describes.

---

## The product in one paragraph

**PetMatch AI** is a multi-shelter animal adoption platform for the Italian market, serving adopters and shelters equally. Shelters get an animal registry (identity, behaviour, dated medical history), an application queue, visit scheduling, and ML forecasting that surfaces which animals will struggle to be placed. Adopters get a bilingual public catalogue with distance search and a map, a 14-question lifestyle quiz that produces ranked and *explained* matches, an AI assistant, and a structured application-to-visit journey. Dogs and cats only. Italian and English from day one. Free for adopters forever; freemium for shelters. Next.js + Prisma + MySQL, with a separate Python FastAPI service holding the models.

---

## Where to look

| If you need to know… | Go to | Section |
|---|---|---|
| What a screen must do | [01](./01-product-spec.md) | §5 user stories, §6 screen inventory |
| Who can do what | [01](./01-product-spec.md) §7, [02](./02-architecture.md) §4 | permission matrix + enforcement |
| The application lifecycle | [01](./01-product-spec.md) | §5 E4 state machine |
| What we are deliberately *not* building | [01](./01-product-spec.md) | §9 |
| Why the stack is what it is | [02](./02-architecture.md) | §2, incl. rejected alternatives |
| Where files live in the repo | [02](./02-architecture.md) | §3 |
| How tenancy is enforced | [02](./02-architecture.md) | §4–5 |
| i18n mechanics | [02](./02-architecture.md) | §6 |
| Photo/video handling | [02](./02-architecture.md) | §7 |
| Distance search SQL | [02](./02-architecture.md) | §8 |
| Env vars and dev fallbacks | [02](./02-architecture.md) | §10 |
| Any table, column, index or enum | [03](./03-database-schema.md) | §2–14 |
| Dev seed data | [03](./03-database-schema.md) | §15 |
| Retention per data type | [03](./03-database-schema.md) | §16 |
| An endpoint's shape | [04](./04-api-contracts.md) | §2 map, §3 payloads |
| Error codes | [04](./04-api-contracts.md) | §1 |
| ML request/response | [04](./04-api-contracts.md) | §4 |
| Assistant tools and guardrails | [04](./04-api-contracts.md) | §5 |
| Dataset quirks and cleaning | [05](./05-ml-spec.md) | §1 |
| Which features the model uses | [05](./05-ml-spec.md) | §3 |
| How models are evaluated | [05](./05-ml-spec.md) | §5 |
| **Model limitations (normative)** | [05](./05-ml-spec.md) | **§8** |
| Retraining plan | [05](./05-ml-spec.md) | §9 |
| How to actually train (Colab) | [11](./11-training-workflow.md) | §2 notebook sequence |
| Reproducibility requirements | [11](./11-training-workflow.md) | §4 |
| **Which model to build, and why** | [12](./12-modelling-approaches.md) | **§3 survival recommendation, §7 summary** |
| Why not fine-tune an LLM | [12](./12-modelling-approaches.md) | §5 |
| Adapting the model to Italian data | [12](./12-modelling-approaches.md) | §6 |
| Modelling ideas already rejected | [12](./12-modelling-approaches.md) | §8 |
| The quiz questions | [06](./06-matching-algorithm.md) | §1 |
| Scoring formulas | [06](./06-matching-algorithm.md) | §4 |
| Worked examples (= regression tests) | [06](./06-matching-algorithm.md) | §5 |
| Explanation prompt | [06](./06-matching-algorithm.md) | §6 |
| Colours, type, spacing | [07](./07-design-system.md) | §2–4 |
| Component list | [07](./07-design-system.md) | §5 |
| Screen wireframes | [07](./07-design-system.md) | §6 |
| Accessibility bar | [07](./07-design-system.md) | §8 |
| What we never say about animals | [07](./07-design-system.md) | §9 |
| Build order and exit criteria | [08](./08-roadmap.md) | phases 1–5 |
| Testing strategy | [08](./08-roadmap.md) | §testing |
| Lawful bases, consent, erasure | [09](./09-compliance-gdpr.md) | §3, §5, §7 |
| Microchip / anagrafe rules | [09](./09-compliance-gdpr.md) | §10 |
| Positioning and competitors | [10](./10-marketing-plan.md) | §2–5 |
| Pricing | [10](./10-marketing-plan.md) | §15 |
| Metrics to instrument | [10](./10-marketing-plan.md) | §13 |
| Welcome Kit incentive programme | [01](./01-product-spec.md) §5 Epic K, [10](./10-marketing-plan.md) §16b | deferred to Phase 5 |

---

## Normative constants

Change these in the document that owns them, never in a copy. The owning document is authoritative; this index is a convenience mirror and must be updated alongside.

### Matching weights — owned by [06](./06-matching-algorithm.md) §2

```
energy 0.20 · space 0.15 · timeAlone 0.15 · household 0.15
experience 0.10 · careCapacity 0.10 · preferences 0.10 · practical 0.05   (Σ = 1.00)
```

Unknown behaviour field → dimension scores **65** + a visible consideration.
Score bands: `90–100` eccellente · `75–89` ottimo · `60–74` buono · `45–59` possibile · `<45` hidden by default.
Default notify threshold: **70**. Digest cap: **1 per profile per 48 h**, max 5 animals.

### Plans — owned by [01](./01-product-spec.md) §10, priced in [10](./10-marketing-plan.md) §15

| | Free | Base | Pro |
|---|---|---|---|
| Price | €0 | €24/mo · €240/yr | €69/mo · €690/yr |
| Animals | 15 | 60 | ∞ |
| Members | 2 | 6 | ∞ |
| Photos/animal | 5 | 10 | 10 |
| Video | — | ✅ | ✅ |
| ML forecasting | — | ✅ | ✅ |
| Staff assistant | — | 100/mo | 500/mo |

### Enums — owned by [03](./03-database-schema.md)

```
role              adopter | shelter_staff | platform_admin
locale            it | en
species           dog | cat
animal.status     draft | available | reserved | adopted | unavailable | transferred | deceased
                  (public: available, reserved only)
application.status draft | submitted | under_review | info_requested | approved
                  | visit_scheduled | completed | rejected | withdrawn | expired
visit.status      booked | completed | cancelled | no_show
shelter.status    pending | active | suspended | archived
shelter.type      canile_comunale | canile_privato | gattile | associazione | rifugio
intake_type       stray | owner_surrender | transfer | born_in_care | return | confiscation
outcome_type      adoption | transfer | return_to_owner | died | euthanasia | escaped
days_bucket       lt_7 | 7_30 | 30_90 | gt_90
compatibility     yes | selective | no | unknown   (children: yes | older_only | no | unknown)
```

### Conventions — owned by [03](./03-database-schema.md) preamble

```
IDs        CHAR(26) ULID on entities; BIGINT AUTO_INCREMENT on append-only logs
Time       DATETIME(3) UTC stored; Europe/Rome displayed; DATE for calendar-only values
Money      INT UNSIGNED cents, EUR only
Charset    utf8mb4 / utf8mb4_0900_ai_ci
Soft delete  users, shelters, animals, animal_media only
```

### Design — owned by [07](./07-design-system.md)

```
accent #B4531F (terracotta) · forest #2F5D4A · bg #FBF8F3 · text #1F1B16 · focus #1F6FEB
Display/headings  Fraunces (variable serif)
Body/UI           Inter (variable), tabular-nums for data
Spacing base 4px · radii 6/10/16/24/full · 3 elevation levels, warm-tinted
```

### ML — owned by [05](./05-ml-spec.md)

```
PRIMARY       adoption_survival — competing-risks survival (RSF / gradient-boosted survival)
              one curve → adoption probability, median days, bucket probabilities,
              competing outcomes.  Censored stays ARE training data.
Comparators   adoption_classifier · los_regressor — evaluation only, never served
Training data Austin Animal Center, Kaggle, ~80k records, Oct 2013 – early 2018
Split         TEMPORAL. train <2017-01-01 · val 2017-H1 · test 2017-07-01+
Baselines     constant · Kaplan-Meier by species×age×size · Cox PH  (must beat all three)
Primary metric concordance index — ranking is the only claim the product makes
Endpoint      POST /predict/outcome (one call, both answers) · /predict/batch
Batch         nightly 02:00; on publish; on relevant field change
Timeout       2s, no inline retry, degrade to a labelled "not available" state
Environment   Colab for exploration, repo scripts for artifacts (doc 11). No GPU, ever.
```

---

## Hard rules

Violating any of these is a defect, not a trade-off. They are the decisions the product's integrity rests on.

**Product**
1. **No ML prediction ever reaches a public surface.** Predictions are shelter-facing only — telling an adopter an animal is unlikely to be adopted is cruel and self-fulfilling. Asserted by a test over the public serialisers.
2. **No adopter personal data is ever used to train a model.** The feature set contains no adopter-derived fields at all.
3. **No automated decision with legal or significant effect.** Match scores suggest; humans decide. A future "auto-reject below score X" would breach GDPR Art. 22 and must never be built.
4. **No pay-to-feature.** Ranking is never influenced by a shelter's plan. No promoted listings.
5. **Adopters are never charged.** Not for browsing, matching, applying, or adopting.
6. **Animals are never framed as goods.** No *merce*, *prodotto*, *stock*, *prezzo*, or *cliente* for an adopter. See [07](./07-design-system.md) §9.
7. **Deal-breakers exclude, never penalise** — and the count and reasons are always reported to the user.
8. **Safety exclusions always apply**, regardless of what the adopter stated: young children vs `good_with_children = no`; existing pets vs the corresponding `no`.
9. **`unknown` is never assumed to be `yes`.** It scores 65 and produces a visible consideration.
10. **Predictions always ship with a suggested action.** Surfacing a problem without an intervention is just a bad mood.

**Security and data**
11. **`shelter_id` is never trusted from the client.** It is resolved from session memberships; any client value is checked against them.
12. **The assistant has no write tools.** It reads and drafts. This removes the entire "convince the model to change a record" attack class.
13. **The staff assistant's `shelter_id` is server-injected**, not a model-visible parameter.
14. **Medical records, internal notes, microchip numbers and adopter contact details never appear in a public or cross-tenant serialiser.** Enforced by explicit `select` lists.
15. **Consent is append-only.** A revocation is a new row, never an update.
16. **EXIF is stripped on upload, GPS included.** Volunteers photograph animals on personal phones.
17. **Platform admins get read-only cross-tenant access, always audit-logged, and can never impersonate.**

**Engineering**
18. **The app runs with zero third-party credentials.** `docker compose up` yields a working, seeded site. A missing integration degrades one feature; it never breaks the app.
19. **One feature transform, shared by training and serving.** A test asserts identical output through both paths.
20. **Alt text is required to publish an animal.** It is how blind adopters and search engines read the listing.
21. **AI-generated or predicted values always carry a visible disclosure.** Every time, no exceptions.

---

## The Austin caveat

Stated here because it is the single most important thing to carry into any work on the ML features, and it must never be quietly dropped.

The models are trained on **Austin Animal Center data — Texas, 2013 to early 2018.** Italy in 2026 differs in adoption culture, breed mix (Austin's population is heavily pit-bull-type; Italy's is overwhelmingly *meticci*), legal framework (Italy's no-kill law and municipal *canile* system have no US equivalent), typical length of stay, and seasonality.

**Therefore:**
- **Absolute numbers will be wrong.** "265 days" is not a forecast anyone should plan around.
- **Only relative ranking is claimed** — *which of my animals will struggle most*. That is the entire product claim, and the UI leads with bucket probabilities rather than day counts for exactly this reason.
- **The length-of-stay model is optimistically biased** by right-censoring: animals still in care at export have no outcome and were excluded from training, and those are disproportionately the long stays.
- **The model reproduces the unfairness in its training data.** Black dogs, seniors and bully breeds waited longer in Austin, so the model says they will here. Used correctly that is the feature — those animals need more help. Used incorrectly it becomes self-fulfilling, which is why rule 1 exists.
- **Prohibited uses**, written into the shelter terms of service, not merely recommended: never for euthanasia, intake refusal, transfer-out, adopter rejection, or pricing an animal's life.
- A model older than 12 months without revalidation is marked stale in the UI.

This caveat appears verbatim in the shelter UI beneath the triage list, permanently and non-dismissibly. Full treatment in [05](./05-ml-spec.md) §8.

---

## Open questions

Carried from the documents, unresolved, listed so nobody assumes they were settled.

| # | Question | Owner doc | Resolves when |
|---|---|---|---|
| 1 | Do the matching weights actually predict adoption success? | [06](./06-matching-algorithm.md) §8 | 12 months of return-rate data by score band |
| 2 | Does the transferred model perform well enough per segment to be shown at all? | [05](./05-ml-spec.md) §5 | Phase 3 evaluation; under-performing segments get suppressed |
| 2b | Does the survival model earn its complexity against the comparators? | [12](./12-modelling-approaches.md) §3 | Phase 3c head-to-head. If it loses, [05](./05-ml-spec.md) §4 reverts to two models |
| 2c | Can per-prediction attribution populate `top_factors` on a survival model? | [05](./05-ml-spec.md) §7 | Phase 3b — validate early, it is an API requirement with named fallbacks |
| 3 | Will shelters act on triage suggestions or dismiss them? | [10](./10-marketing-plan.md) §11 | Phase 3 + 3 months of `at_risk_action_taken` |
| 4 | Will shelters pay anything at all? | [10](./10-marketing-plan.md) appendix | Pilot conversations, months 0–2 |
| 5 | Do adopters finish 14 questions? | [10](./10-marketing-plan.md) §10 | Phase 2 + `quiz_abandoned(index)` |
| 6 | Is the addressable market ~3,000 organisations or ~800? | [10](./10-marketing-plan.md) §4 | Registry research before committing a second year |
| 7 | Does the Welcome Kit programme improve placement without attracting adverse selection? | [01](./01-product-spec.md) Epic K | Phase 5 + 6 months of return rates by kit status |
| 8 | Are we a payment intermediary under Italian rules when forwarding donations? | [10](./10-marketing-plan.md) §16 | Legal review before Phase 5 |
| 9 | Which name ships publicly? | [10](./10-marketing-plan.md) §18–19 | Month 6–9, before public launch |

---

## Glossary

| Term | Meaning |
|---|---|
| *canile* / *gattile* | Municipal or private dog shelter / cat shelter |
| *canile comunale* | Municipally run shelter; procurement is public tendering |
| *canile convenzionato* | Private shelter operating under municipal contract |
| *anagrafe canina* | Regional legal registry of microchipped dogs |
| *comune* | Italian municipality; ~7,900 of them, our unit of geography |
| CAP | Italian postal code |
| *meticcio* | Mixed-breed — the overwhelming majority of Italian shelter dogs |
| *contributo di adozione* | Adoption contribution — never *prezzo* |
| Stay | One intake + its matching outcome; the unit of ML analysis |
| At-risk | An animal the model predicts will wait a long time |
| Welcome Kit | Practical goods given to adopters of hard-to-place animals (Epic K) |
