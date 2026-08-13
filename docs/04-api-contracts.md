# 04 — API Contracts

Most of the web application's data flow uses React Server Components and server actions — no HTTP API is involved and none should be invented for it. This document specifies the boundaries where a real contract exists:

1. **Public/JSON endpoints** the browser calls directly (search, map, favourites, assistant streaming, uploads).
2. **The ML service contract** between the web app and FastAPI.
3. **The assistant's tool definitions**.
4. **Inbound webhooks**.

Everything is versioned under `/api/v1`.

## 1. Conventions

- **Base URL** — `${APP_URL}/api/v1`
- **Auth** — session cookie. Server-to-server calls (web → ML) use a bearer token from `ML_SERVICE_TOKEN`.
- **Content type** — `application/json; charset=utf-8`, except uploads.
- **Locale** — `Accept-Language` or an explicit `locale` parameter; responses carry localised labels but never localised enum values (enums stay canonical, the UI translates them).
- **Idempotency** — `Idempotency-Key` header honoured on application submission, visit booking and donations.
- **Rate limits** — communicated with `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`.

### Pagination

Cursor-based on every list endpoint.

```jsonc
// request:  ?limit=24&cursor=01HQ8Z...
{
  "data": [ /* … */ ],
  "pagination": { "next_cursor": "01HQ9A...", "has_more": true, "total_estimate": 1284 }
}
```

`total_estimate` is exactly that — an estimate on large result sets, exact under 1,000. The UI never renders "page 43 of 97".

### Error envelope

```jsonc
{
  "error": {
    "code": "validation_failed",       // stable, machine-readable
    "message": "Alcuni campi non sono validi.",   // localised, safe to display
    "correlation_id": "01HQ8ZC3M4N5P6Q7R8S9T0",
    "details": [
      { "field": "microchip_number", "code": "already_exists",
        "message": "Questo microchip è già registrato per un altro animale." }
    ]
  }
}
```

| HTTP | `code` values |
|---|---|
| 400 | `validation_failed`, `malformed_request` |
| 401 | `unauthenticated`, `session_expired` |
| 403 | `forbidden`, `plan_limit_reached`, `shelter_not_active` |
| 404 | `not_found` |
| 409 | `conflict`, `already_exists`, `slot_full`, `invalid_state_transition` |
| 413 | `payload_too_large` |
| 422 | `unprocessable` |
| 429 | `rate_limited` |
| 500 | `internal_error` |
| 503 | `dependency_unavailable` (ML service, Claude, storage) |

Internal error messages, stack traces and SQL never reach a response body. The `correlation_id` is also rendered in the UI error state so a user can quote it.

## 2. Endpoint map

### Public — animals and search

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/animals` | — | Search and filter available animals |
| GET | `/animals/{slug}` | — | Full public animal detail |
| GET | `/animals/{slug}/similar` | — | Related animals |
| GET | `/animals/map` | — | Lightweight marker set for the map viewport |
| GET | `/shelters` | — | Shelter directory |
| GET | `/shelters/{slug}` | — | Shelter detail + available animals |
| GET | `/geo/comuni?q=` | — | Comune / CAP autocomplete |

### Matching

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET | `/match/questions` | — | Quiz definition (questions, options, order) |
| POST | `/match/preview` | — | Score an in-progress or anonymous profile |
| POST | `/match/profile` | Adopter | Create or update the saved profile |
| GET | `/match/profile` | Adopter | Read the saved profile |
| GET | `/match/results` | Adopter | Ranked results for the saved profile |
| DELETE | `/match/profile` | Adopter | Delete profile and cached results |

### Adopter

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET/POST/DELETE | `/favorites` | Adopter | List, add, remove |
| POST | `/applications` | Adopter | Create a draft |
| PATCH | `/applications/{id}` | Adopter | Edit a draft |
| POST | `/applications/{id}/submit` | Adopter | Submit (idempotent) |
| POST | `/applications/{id}/withdraw` | Adopter | Withdraw |
| GET | `/applications` | Adopter | Own applications |
| GET | `/visits/slots?shelter_id=&from=&to=` | Adopter | Bookable slots |
| POST | `/visits` | Adopter | Book (idempotent) |
| PATCH | `/visits/{id}` | Adopter | Reschedule or cancel |

### Shelter

| Method | Path | Auth | Purpose |
|---|---|---|---|
| GET/POST | `/shelter/animals` | Member | List / create |
| GET/PATCH/DELETE | `/shelter/animals/{id}` | Member | Read / update / soft-delete |
| POST | `/shelter/animals/{id}/publish` | Member | Validate and publish |
| PUT | `/shelter/animals/{id}/behavior` | Member | Upsert behaviour profile |
| GET/POST | `/shelter/animals/{id}/medical` | Member | Medical log |
| GET/POST | `/shelter/animals/{id}/vaccinations` | Member | Vaccinations |
| POST | `/shelter/animals/{id}/media` | Member | Request an upload URL |
| PATCH/DELETE | `/shelter/media/{id}` | Member | Reorder, set primary, alt text, delete |
| GET | `/shelter/applications` | Member | Queue |
| PATCH | `/shelter/applications/{id}` | Member | Decide or request info |
| GET/POST/PATCH | `/shelter/slots` | Member | Availability |
| PATCH | `/shelter/visits/{id}` | Member | Complete / no-show / cancel |
| GET | `/shelter/dashboard` | Member | KPIs and charts |
| GET | `/shelter/at-risk` | Member | Triage list with predictions |
| POST | `/shelter/import/animals` | Member | CSV import (validate then commit) |
| GET/POST | `/shelter/members` | Member | List / invite |

### Assistant, admin, system

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/chat` | Optional | Send a message; streams the reply |
| GET | `/chat/{conversation_id}` | Optional | History |
| GET | `/admin/shelters/pending` | Admin | Approval queue |
| POST | `/admin/shelters/{id}/approve` \| `/reject` | Admin | Decide |
| GET | `/admin/metrics` | Admin | Platform metrics |
| POST | `/webhooks/stripe` | Signature | Billing events |
| POST | `/webhooks/whatsapp` | Signature | Delivery receipts |
| GET | `/health` | — | Liveness + dependency status |

## 3. Key payloads

### `GET /animals`

```
GET /api/v1/animals
  ?species=dog
  &size=small,medium
  &age_band=adult
  &good_with_children=yes
  &sterilized=true
  &lat=45.4642&lng=9.1900&radius_km=50
  &sort=distance
  &limit=24
```

```jsonc
{
  "data": [
    {
      "id": "01HQ8ZC3M4N5P6Q7R8S9T0",
      "slug": "luna-canile-speranza-mi",
      "name": "Luna",
      "species": "dog",
      "sex": "female",
      "size": "medium",
      "breed_primary": "Meticcio",
      "is_mixed": true,
      "age_months": 38,
      "age_band": "adult",
      "is_sterilized": true,
      "has_special_needs": false,
      "headline": "Tranquilla, adora le passeggiate lunghe",
      "primary_photo": {
        "url": "https://cdn.example/…/640.webp",
        "srcset": "…/320.webp 320w, …/640.webp 640w, …/1280.webp 1280w",
        "placeholder": "data:image/webp;base64,UklGR…",
        "alt": "Luna, cagnolina meticcia marrone, seduta sull'erba"
      },
      "has_video": false,
      "days_in_care": 214,
      "shelter": {
        "id": "01HQ8ZB…", "slug": "canile-speranza",
        "name": "Canile La Speranza",
        "comune": "Milano", "province": "MI",
        "distance_km": 12.4
      },
      "match": { "score": 91, "summary": "Adatta a un appartamento e al tuo ritmo" }
    }
  ],
  "facets": {
    "species": { "dog": 842, "cat": 611 },
    "size": { "small": 190, "medium": 430, "large": 201, "xlarge": 21 },
    "age_band": { "puppy": 96, "young": 271, "adult": 812, "senior": 274 }
  },
  "pagination": { "next_cursor": "01HQ9A…", "has_more": true, "total_estimate": 1453 }
}
```

`match` is present only when the caller has a completed adopter profile. Facet counts reflect the current filter set minus the facet being counted, so the UI can show "what would happen if I also picked this".

### `GET /animals/{slug}`

```jsonc
{
  "id": "01HQ8ZC3M4N5P6Q7R8S9T0",
  "slug": "luna-canile-speranza-mi",
  "name": "Luna",
  "species": "dog", "sex": "female", "size": "medium",
  "breed_primary": "Meticcio", "breed_secondary": null, "is_mixed": true,
  "coat_color": "marrone", "coat_length": "short",
  "age_months": 38, "birth_date_estimated": true,
  "weight_kg": 18.5,
  "is_sterilized": true,
  "is_vaccinated": true,
  "has_special_needs": false,
  "special_needs_summary": null,
  "adoption_fee_cents": 0,
  "status": "available",
  "days_in_care": 214,
  "headline": "Tranquilla, adora le passeggiate lunghe",
  "story": "Luna è arrivata da noi nell'inverno del 2024…",
  "story_language": "it",
  "media": [
    { "kind": "photo", "url": "…", "srcset": "…", "alt": "…", "is_primary": true },
    { "kind": "video", "url": "…/720.mp4", "poster": "…/poster.jpg", "duration_seconds": 34 }
  ],
  "behavior": {
    "energy_level": 2,
    "good_with_children": "yes",
    "good_with_dogs": "yes",
    "good_with_cats": "unknown",
    "house_trained": "yes",
    "leash_trained": "partially",
    "alone_tolerance_hours": 6,
    "exercise_min_per_day": 60,
    "grooming_needs": 2,
    "training_needs": 2,
    "suitable_for_first_time": "yes",
    "needs_garden": "preferred",
    "temperament_tags": ["affettuosa", "calma", "curiosa"],
    "notes": "Con i gatti non è ancora stata testata.",
    "assessed_at": "2026-05-14",
    "is_stale": false
  },
  "shelter": {
    "id": "01HQ8ZB…", "slug": "canile-speranza", "name": "Canile La Speranza",
    "address_line": "Via dei Prati 12", "comune": "Milano", "province": "MI",
    "postal_code": "20134", "latitude": 45.4812, "longitude": 9.2451,
    "phone": "+39 02 1234567", "distance_km": 12.4,
    "accepts_donations": true
  },
  "match": {
    "score": 91,
    "reasons": [
      { "key": "energy_matches", "label": "Il suo livello di energia si adatta al tuo ritmo" },
      { "key": "apartment_ok",  "label": "Sta bene in appartamento" },
      { "key": "alone_ok",      "label": "Tollera bene le ore in cui saresti fuori" }
    ],
    "considerations": [
      { "key": "cats_untested", "label": "Non è ancora stata testata con i gatti" }
    ],
    "explanation": "Luna sembra pensata per la tua situazione…"
  },
  "can_apply": true
}
```

Note what is **absent**: no medical records, no `microchip_number`, no adoption predictions. Predictions are shelter-facing only, by design (see [01](./01-product-spec.md) §8).

### `POST /match/preview`

```jsonc
// request
{
  "profile": {
    "housing_type": "apartment",
    "housing_size_sqm": 80,
    "has_outdoor_space": false,
    "household_adults": 2,
    "children_ages": [],
    "existing_dogs": 0,
    "existing_cats": 0,
    "hours_alone_per_day": 6,
    "activity_level": 3,
    "experience_level": "first_time",
    "grooming_capacity": 2,
    "training_capacity": 3,
    "preferred_species": "dog",
    "preferred_sizes": ["small", "medium"],
    "preferred_age_bands": ["adult"],
    "preferred_sex": "any",
    "dealbreakers": ["must_be_house_trained"],
    "search_comune_id": 4021,
    "search_radius_km": 50
  },
  "limit": 12,
  "explain": true          // false skips LLM generation and returns reason keys only
}

// response
{
  "results": [
    {
      "animal": { /* the card shape from GET /animals */ },
      "score": 91,
      "breakdown": {
        "space": { "score": 95, "weight": 0.15, "contribution": 14.25 },
        "time_alone": { "score": 88, "weight": 0.15, "contribution": 13.2 },
        "energy": { "score": 100, "weight": 0.20, "contribution": 20.0 },
        "household": { "score": 100, "weight": 0.15, "contribution": 15.0 },
        "experience": { "score": 90, "weight": 0.10, "contribution": 9.0 },
        "care_capacity": { "score": 80, "weight": 0.10, "contribution": 8.0 },
        "preferences": { "score": 92, "weight": 0.10, "contribution": 9.2 },
        "practical": { "score": 85, "weight": 0.05, "contribution": 4.25 }
      },
      "reasons": [ /* … */ ],
      "considerations": [ /* … */ ],
      "explanation": "…"
    }
  ],
  "excluded": {
    "count": 47,
    "by_reason": { "dealbreaker_house_trained": 12, "outside_radius": 31, "species_preference": 4 }
  },
  "engine_version": "match-1.0.0",
  "radius_widened_to_km": null
}
```

The scoring contract is specified in full in [06 — Matching Algorithm](./06-matching-algorithm.md); the weights above must match that document exactly.

### `POST /applications/{id}/submit`

```jsonc
// request
{
  "motivation_text": "Cerchiamo un compagno per le nostre passeggiate…",
  "home_description": "Appartamento 80 m² con balcone, secondo piano con ascensore.",
  "household_summary": "Due adulti, nessun bambino, nessun altro animale.",
  "previous_animals": "Ho avuto un cane fino al 2023, morto per vecchiaia a 15 anni.",
  "availability_note": "Sabato mattina o infrasettimanale dopo le 18.",
  "consent_home_visit": true,
  "accepted_terms": true
}

// 201
{
  "id": "01HQ9B…",
  "reference": "PM-7K4Q-2210",
  "status": "submitted",
  "submitted_at": "2026-08-13T09:12:44.120Z",
  "animal": { "slug": "luna-canile-speranza-mi", "name": "Luna" },
  "shelter": { "name": "Canile La Speranza", "typical_response_days": 4 },
  "next_step": "La struttura esaminerà la tua candidatura."
}

// 409 — animal no longer available
{ "error": { "code": "invalid_state_transition",
             "message": "Luna non è più disponibile per l'adozione.",
             "correlation_id": "…" } }
```

### `POST /visits`

```jsonc
// request  (Idempotency-Key required)
{ "application_id": "01HQ9B…", "slot_id": "01HQ9C…" }

// 201
{
  "id": "01HQ9D…",
  "status": "booked",
  "scheduled_start": "2026-08-22T09:00:00.000Z",
  "scheduled_end": "2026-08-22T09:30:00.000Z",
  "shelter": { "name": "Canile La Speranza", "address_line": "Via dei Prati 12",
               "latitude": 45.4812, "longitude": 9.2451 },
  "calendar_url": "/api/v1/visits/01HQ9D…/calendar.ics",
  "can_cancel_until": "2026-08-21T09:00:00.000Z"
}

// 409
{ "error": { "code": "slot_full", "message": "Questo orario è appena stato prenotato." } }
```

### `GET /shelter/at-risk`

```jsonc
{
  "data": [
    {
      "animal": { "id": "01HQ8Z…", "name": "Rocco", "slug": "rocco-…",
                  "species": "dog", "age_months": 96, "size": "large",
                  "primary_photo": { "url": "…", "alt": "…" } },
      "days_in_care": 418,
      "prediction": {
        "adoption_probability": 0.31,
        "median_days_to_adoption": 265,
        "days_bucket": "gt_90",
        "bucket_probabilities": { "lt_7": 0.04, "7_30": 0.11, "30_90": 0.22, "gt_90": 0.63 },
        "top_factors": [
          { "feature": "age_months", "label": "Età superiore a 8 anni", "direction": "negative", "impact": 0.22 },
          { "feature": "size", "label": "Taglia grande", "direction": "negative", "impact": 0.14 },
          { "feature": "intake_condition", "label": "Arrivato in condizioni non ottimali", "direction": "negative", "impact": 0.09 }
        ],
        "model_version": "adoption_survival-1.0.0",
        "computed_at": "2026-08-13T02:00:00.000Z"
      },
      "suggested_actions": [
        { "key": "add_photos", "label": "Aggiungi altre foto", "impact": "high", "dismissed": false },
        { "key": "add_video", "label": "Carica un breve video", "impact": "high", "dismissed": false },
        { "key": "complete_behavior", "label": "Completa il profilo comportamentale", "impact": "medium", "dismissed": false },
        { "key": "consider_foster", "label": "Valuta un affido temporaneo", "impact": "medium", "dismissed": false }
      ]
    }
  ],
  "disclaimer_key": "predictions.disclaimer.austin_model"
}
```

`disclaimer_key` resolves to a permanent, unmissable caveat: the model was trained on North American shelter data, it estimates rather than decides, and it must never inform any decision about an animal's life. See [05](./05-ml-spec.md) §8.

### Media upload

Two steps, so large files never pass through the application server.

```jsonc
// 1. POST /shelter/animals/{id}/media
{ "kind": "photo", "mime_type": "image/jpeg", "byte_size": 3145728, "filename_hint": "luna-01.jpg" }

// 201
{
  "media_id": "01HQ9E…",
  "upload": { "method": "PUT", "url": "https://storage…?X-Amz-Signature=…", "expires_in": 900,
              "headers": { "Content-Type": "image/jpeg" } },
  "max_bytes": 12582912
}

// 2. client PUTs the file, then:
// POST /shelter/media/01HQ9E…/complete  → { "processing_status": "pending" }
// derivatives are generated by a job; the client polls or receives a socket update
```

Plan limits (`plan_limit_reached`) and unsupported types are rejected at step 1, before a byte is uploaded.

## 4. ML service contract

Base URL `ML_SERVICE_URL`. Bearer token auth. The service is stateless, has no database access, and knows nothing about shelters or users — it receives features and returns numbers.

### `GET /health`

```jsonc
{
  "status": "ok",
  "models": [
    { "name": "adoption_survival", "version": "1.0.0", "trained_at": "2026-07-02T10:00:00Z",
      "algorithm": "random_survival_forest", "role": "primary",
      "metrics": { "concordance": 0.731, "integrated_brier": 0.147,
                   "auc_90d": 0.768, "bucket_calibration_error": 0.031 } }
  ],
  "uptime_seconds": 84213
}
```

Baseline comparators (`adoption_classifier`, `los_regressor`) are evaluation instruments and are not served — they exist in the training pipeline and the model card only.

### `POST /predict/outcome`

One call, one model, both answers — probability and timing are read from the same fitted curve, so they cannot contradict each other ([05](./05-ml-spec.md) §4).

```jsonc
// request — the feature contract. Every field is nullable; the service imputes
// and reports what it imputed, so the caller can show "prediction based on
// incomplete data".
{
  "features": {
    "species": "dog",
    "sex": "female",
    "sterilized_at_intake": true,
    "age_months_at_intake": 34,
    "breed_primary": "Meticcio",
    "is_mixed": true,
    "size": "medium",
    "coat_color": "marrone",
    "coat_length": "short",
    "intake_type": "stray",
    "intake_condition": "normal",
    "intake_month": 2,
    "intake_weekday": 3,
    "intake_season": "winter",
    "has_name": true,
    "prior_intake_count": 0,
    "has_special_needs": false,
    "photo_count": 1,
    "has_video": false,
    "behavior_profile_completeness": 0.6
  },
  "explain": true
}

// 200
{
  "model": { "name": "adoption_survival", "version": "1.0.0",
             "algorithm": "random_survival_forest" },

  // read off the adoption cumulative incidence curve
  "adoption_probability": 0.31,          // curve plateau — eventual adoption
  "confidence_interval": [0.24, 0.39],
  "median_days_to_adoption": 265,        // null when the curve never reaches 0.5
  "prediction_interval": [120, 460],     // conformal, see 12 §4
  "days_bucket": "gt_90",                // the highest-probability bucket
  "bucket_probabilities": { "lt_7": 0.04, "7_30": 0.11, "30_90": 0.22, "gt_90": 0.63 },

  // the curve itself, for the sparkline on the animal record
  "survival_curve": [
    { "day": 7,   "adopted_by": 0.04 },
    { "day": 30,  "adopted_by": 0.15 },
    { "day": 90,  "adopted_by": 0.37 },
    { "day": 180, "adopted_by": 0.54 },
    { "day": 365, "adopted_by": 0.68 }
  ],

  // competing risks — distinct exits, not collapsed into "not adopted"
  "competing_outcomes": {
    "transfer": 0.12, "return_to_owner": 0.04, "death": 0.03
  },

  "top_factors": [
    { "feature": "age_months_at_intake", "direction": "negative", "impact": 0.22 },
    { "feature": "size", "direction": "negative", "impact": 0.14 },
    { "feature": "intake_condition", "direction": "negative", "impact": 0.09 }
  ],
  "imputed_fields": ["coat_length"],
  "computed_at": "2026-08-13T02:00:00Z"
}
```

`bucket_probabilities` are the numbers the UI leads with, and they are now the model's native output rather than a point estimate chopped into bins. `median_days_to_adoption` is deliberately secondary and may be `null` — for an animal whose curve never crosses 0.5 within the observable window, "no median within 2 years" is the honest answer, and inventing a number there would be worse than omitting it.

### `POST /predict/batch`

Accepts up to 500 items, each `{ "ref": "<animal_id>", "features": { … } }`, returns one prediction per ref plus a `failed` array with per-ref reasons. Used by the nightly job. `survival_curve` is omitted in batch responses to keep payloads small; the dashboard fetches it per animal on demand.

### `GET /model-info`

Full model card: training window, row count, feature list, per-class metrics, per-species and per-age-band breakdowns, calibration curve points, and a plain-language limitations block that the shelter UI renders verbatim.

### Failure behaviour

If the ML service is unreachable, times out (2 s), or returns 5xx:
- the web app logs it with a correlation id and does **not** retry inline;
- prediction UI renders a "not available" state rather than a stale number without a date;
- the nightly batch retries with backoff and alerts after three consecutive failures;
- a documented heuristic fallback (age band × size × species × days already waited, from the training set's empirical rates) may be used **only** in local development, and is always labelled as such.

## 5. Assistant

### `POST /chat`

```jsonc
// request
{
  "conversation_id": "01HQ9F…",          // omitted on the first message
  "message": "Cerco un gatto tranquillo vicino a Milano, ho un bambino di 6 anni",
  "locale": "it",
  "persona": "adopter"                    // "staff" requires a shelter membership
}
```

The response is a server-sent event stream: `token` events carrying text deltas, `tool_use` events naming the tool being run (so the UI can show "sto cercando…"), `card` events carrying structured animal results to render, `citation` events with knowledge-base links, and a final `done` event with the conversation id and token usage.

### Tool definitions

**Adopter persona** — read-only, public data only:

| Tool | Parameters | Returns |
|---|---|---|
| `search_animals` | `species?`, `size?[]`, `age_band?[]`, `good_with_children?`, `good_with_dogs?`, `good_with_cats?`, `energy_max?`, `comune?`, `radius_km?`, `limit?` (≤ 6) | Animal cards, published fields only |
| `get_animal` | `slug` | Full public detail (identical to the public endpoint) |
| `search_knowledge_base` | `query`, `category?`, `locale?` | Ranked chunks with document links |
| `get_shelter_info` | `slug` | Public shelter profile, hours, contacts |

**Staff persona** — read-only, hard-scoped to the caller's shelter:

| Tool | Parameters | Returns |
|---|---|---|
| `query_my_animals` | `status?`, `species?`, `min_days_in_care?`, `sort?`, `limit?` | The caller's animals with days in care and predictions |
| `get_my_stats` | `from`, `to`, `metric` | Aggregates for the caller's shelter only |
| `draft_animal_description` | `animal_id`, `locale`, `tone?` | Draft text — returned to the UI for human editing, never written |

The `shelter_id` is injected server-side from the session on every staff tool call. It is not a model-visible parameter, so there is no prompt that can make the assistant read another shelter's data.

### Guardrails

- No tool writes. The assistant cannot create, update, delete, publish, decide an application, or send a message.
- Retrieved documents and shelter-authored text are inserted inside explicit delimiters, and the system prompt states that content within them is reference material and never instructions.
- Medical questions get general information plus an explicit referral to a veterinarian.
- The assistant never states or implies that a specific application will be accepted, never quotes availability it has not just retrieved, and never speaks as the shelter.
- Refusal to answer is preferred over a guess; unanswerable questions route to the shelter's contact details.
- Per-session (30 messages/hour) and per-IP limits; staff persona metered against the plan quota; monthly platform budget with alerting.

## 6. Webhooks

### `POST /webhooks/stripe`

Signature-verified with `STRIPE_WEBHOOK_SECRET`. Events consumed:

| Event | Effect |
|---|---|
| `checkout.session.completed` | Activate subscription or record a donation |
| `customer.subscription.updated` | Sync plan, status, period end |
| `customer.subscription.deleted` | Downgrade to `free` at period end, never mid-period |
| `invoice.payment_failed` | Mark `past_due`, notify the billing contact |
| `payment_intent.succeeded` | Mark donation `succeeded`, issue receipt |
| `charge.refunded` | Mark donation `refunded` |

Handlers are idempotent on the Stripe event id, which is persisted before processing. A duplicate delivery is acknowledged and ignored.

### `POST /webhooks/whatsapp`

Delivery receipts and opt-out messages. `STOP` in any casing revokes the WhatsApp consent, writes a `consents` row with `granted = 0`, and disables the channel for that user across every notification type.

## 7. Health

`GET /health` returns `200` when the app and database are up, with a per-dependency breakdown (`database`, `storage`, `ml_service`, `claude`, `email`, `stripe`) each reporting `ok`, `degraded`, `unavailable` or `not_configured`. Degraded dependencies do not fail the check — the application is designed to work with any of them missing, and `not_configured` is the normal local-development state.
