# 01 — Product Specification

## 1. The problem

Adoption in Italy is mediated by hundreds of small, under-resourced organisations: *canili comunali* (municipal dog shelters), *canili privati* under convention with municipalities, *gattili*, and volunteer associations. Almost none of them have software. The consequences are concrete:

**For shelters.** Animal records live in spreadsheets, paper folders, or a volunteer's memory. Nobody knows which animals have been waiting the longest until someone notices. There is no way to estimate whether a newly arrived animal will be placed in two weeks or two years, so there is no way to prioritise the ones that need extra effort — a better photo, a foster placement, a targeted post. Staff answer the same questions ("is he good with cats?", "what does adoption cost?", "can I adopt if I work full time?") dozens of times a week, by phone and by Facebook comment.

**For adopters.** Listings are scattered across municipal PDF pages, Facebook groups, and a handful of national portals with thin, inconsistent data. Photos are poor. Behavioural information is missing or reduced to "buonissimo con tutti". People choose on appearance, discover the mismatch at home, and a share of those adoptions come back — the outcome everyone was trying to avoid.

**The shared failure.** The information that would produce a good match — how many hours the animal is alone, whether there are children, how much exercise the adopter can actually give — is never collected in a structured way, so it can never be matched against anything.

## 2. What PetMatch AI is

A multi-shelter platform where shelters keep their animal records and adopters find animals, with three pieces of intelligence layered on top:

1. **Adoption forecasting** — for shelter staff. Every animal in care gets an adoption-probability score and an expected length of stay, so the ones at risk of lingering surface automatically instead of being noticed by accident.
2. **Explained matching** — for adopters. A guided lifestyle questionnaire is scored against structured animal attributes to produce a ranked list, where each result says *why* in plain language. The score is a transparent formula, never a black box.
3. **An AI assistant** — for both. A public assistant that answers adoption and care questions from a curated knowledge base and can search live animals; and an internal assistant that lets staff query their own data conversationally and draft animal descriptions.

## 3. Goals and non-goals

### Goals

- **G1** — Reduce average length of stay by making at-risk animals visible early and giving staff a reason to act on them.
- **G2** — Increase the quality of matches, measured by completed adoptions that do not return within 12 months.
- **G3** — Give a shelter with zero technical capacity a usable animal registry in under an hour, with no installation.
- **G4** — Make every ranked match explainable to a non-technical person in one sentence.
- **G5** — Cut the volume of repetitive inbound questions shelters answer manually.

### Non-goals

- We are **not** an adoption decision-maker. The platform never approves or rejects an adopter; it structures information for the humans who do.
- We are **not** a marketplace. No animal is ever sold. Adoption fees, where they exist, are shelter-set contributions and are displayed as such.
- We are **not** a veterinary record system of legal standing. The medical log is an operational aid, not a substitute for official veterinary documentation or the anagrafe canina.
- We are **not** a social network. No public comments, no adopter-to-adopter messaging.

## 4. Personas

### Giulia — shelter operator (primary shelter persona)
Runs a 60-dog *canile convenzionato* in a province capital with two paid staff and a rotating cast of volunteers. Works from a phone as much as a laptop, often standing in a kennel corridor. Spreadsheet-literate, not technical. Her real problems: she cannot tell you today how many dogs have been in care longer than a year without counting by hand; she loses an hour a day to repeat questions; she gets adoption applications as unstructured Facebook messages that she then has to chase for basic information.

**What success looks like for Giulia:** she opens the dashboard in the morning, sees five dogs flagged as likely to linger with a suggested action for each, and works through the applications queue in ten minutes.

### Marco — adopter (primary public persona)
34, lives in an 80 m² flat in a city with a partner, no children yet, works hybrid — the animal would be alone about six hours on three days a week. Wants a dog. Has no idea whether that is responsible, which sizes suit a flat, or what a first-time owner can realistically handle. Currently scrolling Facebook groups and feeling guilty.

**What success looks like for Marco:** ten minutes of honest questions, a shortlist of six real animals within 40 km, each with a sentence explaining the fit and one saying plainly what would be hard, and a way to apply that does not feel like shouting into a void.

### Anna — platform admin (internal)
Runs PetMatch AI. Approves new shelters (verifying they are a real organisation, not a breeder or a private reseller), watches for listings that break the rules, monitors platform health and the AI assistant's cost and behaviour.

### Secondary: Luca — volunteer
Uses the same shelter-staff permissions as Giulia but touches only a few things: uploading photos after a Saturday shoot, updating a behavioural note. Not a separate permission tier — see §7.

## 5. User stories

Format: *As a [role], I want [capability], so that [outcome].* Acceptance criteria are the conditions under which the story is done.

### Epic A — Shelter onboarding and identity

**A1. Register a shelter.** As a shelter operator, I want to register my organisation, so that I can start entering animals.
- Registration captures organisation name, legal name, type (canile comunale / canile privato / gattile / associazione / rifugio), fiscal or VAT identifier, address with comune, contact email and phone, and a public description.
- The account is created in `pending` status and cannot publish animals until approved.
- The registrant becomes the first member of the shelter with the billing-contact flag set.
- Address is geocoded to coordinates at save time; failure to geocode blocks activation, not registration.

**A2. Approve a shelter.** As a platform admin, I want to review and approve or reject shelter registrations, so that only legitimate organisations publish.
- Queue shows pending shelters ordered oldest-first with all submitted details.
- Approve sets status `active` and emails the registrant; reject requires a reason, which is included in the email.
- Both actions are written to the audit log.

**A3. Invite colleagues.** As a shelter operator, I want to invite staff and volunteers by email, so that they can help maintain records.
- Invitation email contains a single-use, time-limited link.
- Accepting creates or links a user account and adds a `shelter_members` row.
- Members can be removed; removal never deletes the content they created.
- The number of members is capped by the shelter's plan (see §10).

**A4. Manage the public shelter profile.** As a shelter operator, I want a public page describing my organisation, so that adopters know who they are dealing with.
- Logo, cover image, description in Italian and English, opening hours, address, map position, contact details, links to social pages, and an optional donation call to action.

### Epic B — Animal records

**B1. Create an animal record.** As shelter staff, I want to add an animal with full details, so that it can be listed and matched.
- Required to save a draft: species (dog or cat), name or temporary code, sex, estimated birth date or age band, intake date.
- Required to publish: at least one photo with alt text, size, sterilisation status, a completed behaviour profile, and a description in at least one language.
- Microchip number is validated for format (15 digits) and uniqueness across the platform, with a clear conflict message if it already exists.
- Draft records are visible only within the owning shelter.

**B2. Record behaviour.** As shelter staff, I want to record a structured behavioural profile, so that matching has something to work with.
- Energy level, sociability with people, compatibility with children / dogs / cats, house-trained, leash-trained, noise tolerance, tolerable hours alone, training needs, grooming needs, daily exercise minutes, free temperament tags, and free-text notes.
- Compatibility fields explicitly support **unknown** — never silently defaulted to "yes".
- Records who assessed and when; profiles older than 12 months are flagged as stale in the UI.

**B3. Keep a medical history.** As shelter staff, I want a dated log of medical events, so that I can answer health questions and hand over a real history at adoption.
- Entries of type exam, treatment, surgery, test, deworming, weight measurement, other — each with a date, title, description, optional vet and clinic, optional cost, optional next-due date.
- Vaccinations are tracked separately with vaccine type, date administered, validity date, batch number.
- Entries with a next-due date generate a reminder for the shelter when it approaches.
- Weight entries render as a chart on the animal record.
- Medical detail is **never** exposed publicly beyond a curated summary the shelter chooses to publish (special needs, sterilised, vaccinated).

**B4. Manage photos and video.** As shelter staff, I want to upload several photos and a short video, so that the animal is presented well.
- Up to 10 photos and 1 video (≤ 60 seconds) per animal, subject to plan limits.
- One photo is the primary; drag to reorder; alt text required per photo in at least one language.
- Server generates derivatives; originals are retained.
- Upload works from a phone camera roll.

**B5. Change status.** As shelter staff, I want to move an animal through its lifecycle, so that the public listing is accurate.
- Statuses: `draft`, `available`, `reserved`, `adopted`, `unavailable` (medical hold, quarantine, behavioural rehab), `transferred`, `deceased`.
- Only `available` and `reserved` appear publicly; `reserved` appears with a badge and cannot receive new applications.
- Marking `adopted` requires an outcome record, and offers to link the application that produced it.
- Status changes are audit-logged.

**B6. Bulk import.** As a shelter operator with existing spreadsheets, I want to import animals from CSV, so that onboarding does not mean re-typing 60 records.
- Downloadable template, column mapping step, validation preview showing per-row errors before anything is written, partial import allowed.
- Imported animals land in `draft`.

### Epic C — Public discovery

**C1. Browse and filter.** As an adopter, I want to filter available animals, so that I see relevant ones.
- Filters: species, sex, size, age band, sterilised, good with children / dogs / cats, energy level, special needs, shelter, and free-text search over name, breed and description.
- Distance filter: a location (comune, CAP, or browser geolocation) plus a radius in km; results show distance.
- Results are paginated, sortable by newest, nearest, longest waiting, and (when a profile exists) best match.
- Filter state lives in the URL so results can be shared.

**C2. Map view.** As an adopter, I want to see animals and shelters on a map, so that I understand what is near me.
- Toggle between grid and map on the same result set; clustered markers; clicking a shelter marker shows its available animals; the map respects active filters.

**C3. Animal profile page.** As an adopter, I want a rich page per animal, so that I can decide.
- Photo gallery and video, name, age, size, breed, sex, sterilisation, the shelter's story text, structured behaviour presented as human-readable statements ("Sta bene con altri cani", "Non ancora testato con i gatti"), published health summary, adoption fee if any, time in care, shelter card with distance and contact, favourite button, apply button, and a "similar animals" strip.
- If the visitor has an adopter profile, the page shows their match score and its explanation inline.
- Server-rendered with per-animal metadata and structured data for search engines; indexable while available, de-indexed with a redirect when adopted.

**C4. Shelter profile page.** As an adopter, I want to see a shelter and everything it currently has available.

**C5. Favourites.** As a registered adopter, I want to save animals, so that I can compare later.
- Favourites survive across devices; the adopter is notified if a favourited animal's status changes.

### Epic D — Matching

**D1. Take the quiz.** As an adopter, I want a guided questionnaire, so that I get relevant suggestions instead of guessing.
- One question per screen with a progress indicator, back navigation, and no dead ends.
- Partial answers persist so the quiz can be resumed.
- Can be completed anonymously; results are shown immediately; saving requires an account.
- Full question list and scoring in [06 — Matching Algorithm](./06-matching-algorithm.md).

**D2. See ranked results.** As an adopter, I want ranked matches with reasons, so that I trust the ranking.
- Each result: score out of 100, a one-paragraph natural-language rationale, up to three positive reason bullets, and — when relevant — an honest "things to consider" note.
- Deal-breakers exclude animals outright rather than merely lowering their score, and the UI says how many were excluded and why.
- If fewer than five animals score above the threshold, the page widens the radius and says so, rather than showing bad matches silently.

**D3. Save the profile and keep matching.** As an adopter, I want my answers saved, so that I hear about new animals that fit.
- The saved profile is editable at any time.
- New or newly published animals are scored against active profiles; matches above the adopter's chosen threshold generate a notification.
- Frequency is capped (default: at most one digest per profile per 48 hours) and unsubscribing is one click.

### Epic E — Applications

**E1. Apply to adopt.** As an adopter, I want to submit a structured application, so that the shelter has what it needs on first contact.
- Application is per-animal and requires an account.
- Pre-filled from the adopter profile where available; the adopter can amend and must confirm.
- Adds: motivation text, home description, who else lives there, previous animals and what happened to them, availability for a visit, consent to a home visit, acceptance of terms.
- Saved as `draft` until submitted; one active application per adopter per animal.
- On submit, both the adopter and the shelter are notified, and the application receives a human-readable reference.

**E2. Review applications.** As shelter staff, I want a queue of applications, so that nothing is lost.
- Queue filterable by status, animal, and date, with a per-application detail view showing everything submitted plus the applicant's profile summary and their other applications on this platform.
- Actions: request more information, approve, reject (reason required, shown to the adopter), mark withdrawn.
- Internal notes on an application are never visible to the adopter and are labelled as such in the UI.

**E3. Track status.** As an adopter, I want to see where my application stands, so that I am not left in silence.
- A status timeline on the adopter dashboard, plus notification on every transition.
- Explicit "the shelter has not yet responded" state with an expectation of typical response time.

**E4. State machine.** Statuses and legal transitions:

```
draft ──submit──▶ submitted ──open──▶ under_review ──┬──▶ info_requested ──reply──▶ under_review
                                                     ├──▶ approved ──book──▶ visit_scheduled ──▶ completed
                                                     └──▶ rejected
any non-terminal ──▶ withdrawn   (adopter-initiated)
any non-terminal ──▶ expired     (system, after 60 days of inactivity)
```

- Terminal: `completed`, `rejected`, `withdrawn`, `expired`.
- Every transition writes an `application_events` row with actor, timestamp and optional note.
- `completed` requires the visit to have happened and creates the animal's outcome record.

### Epic F — Visits

**F1. Publish availability.** As shelter staff, I want to publish visit slots, so that adopters book instead of phoning.
- Slots have start, end, capacity (more than one family can visit in the same window), and an optional location note.
- Recurring weekly patterns can be generated and individual instances cancelled.
- Slots can be blocked for holidays.

**F2. Book a visit.** As an approved adopter, I want to choose a slot, so that I can meet the animal.
- Only approved applications can book; only future slots with remaining capacity are selectable.
- Booking confirms by email and in-app, with a calendar file and the shelter's address and map link.
- Reschedule and cancel are allowed up to a configurable cutoff (default 24 h); later cancellations are still possible but flagged to the shelter.

**F3. Record the outcome.** As shelter staff, I want to mark a visit completed, no-show, or cancelled, so that the record is honest.
- Completing a visit prompts the next step: proceed to adoption, schedule another visit, or close the application.

### Epic G — Intelligence for shelters

**G1. Dashboard.** As a shelter operator, I want an overview, so that I know where I stand.
- KPI tiles: animals in care (by species), currently available, average length of stay, adoptions this month vs last, open applications, occupancy against declared capacity.
- Charts: intakes vs outcomes over time, length-of-stay distribution, outcome type breakdown, applications funnel.
- Date range selector; every tile links to the filtered list behind it.

**G2. At-risk triage.** As a shelter operator, I want the animals likely to wait longest surfaced, so that I can intervene.
- A ranked list of animals in care by predicted difficulty, showing adoption probability, expected days, days already waited, and the top factors driving the prediction.
- Each row carries suggested actions drawn from a fixed catalogue tied to the driving factors — for example: add more photos, add a video, complete the behaviour profile, consider a foster placement, feature on social channels, reconsider the adoption fee.
- Staff can dismiss a suggestion or mark it as done; dismissals are remembered.
- Every prediction carries a plain-language caveat about model uncertainty and origin.

**G3. Predictions on the record.** As shelter staff, I want to see the forecast on an animal's page, so that context travels with the animal.
- Probability, expected days band, contributing factors, model version and computation date.
- Predictions recompute when relevant fields change and on a nightly batch.

### Epic H — AI assistant

**H1. Public assistant.** As an adopter, I want to ask questions in my own words, so that I do not have to read a FAQ page.
- Answers adoption-process and pet-care questions grounded in a curated knowledge base, with links to the source articles.
- Can search live animals and return real cards ("gatti tranquilli vicino a Milano che vanno d'accordo con i bambini").
- Replies in the visitor's interface language.
- Says it does not know rather than inventing, and refers medical questions to a veterinarian.
- Never speaks on a shelter's behalf about a specific application, and never promises availability.
- Rate-limited per session; conversation history is retained for the session and, for logged-in users, on their account.

**H2. Staff assistant.** As shelter staff, I want to ask questions about my own data, so that I do not have to build a report.
- Natural-language querying scoped strictly to the requesting shelter ("quali cani aspettano da più di sei mesi?", "quante adozioni a maggio?").
- Drafts an animal description from the structured record, in both languages, for a human to edit and approve — never auto-published.
- Cannot modify data; it reads and drafts only.

### Epic I — Accounts, notifications, admin

**I1. Accounts.** Email and password registration with verification, password reset, profile management, language preference, notification preferences, and self-service account deletion (see [09](./09-compliance-gdpr.md)).

**I2. Notifications.** In-app centre plus email; WhatsApp for the transactional moments that matter (application submitted, decision made, visit reminder). Per-channel, per-type preferences. Every outbound message is localised.

**I3. Platform admin.** Shelter approval queue, shelter and user search, listing moderation with takedown and reason, platform-wide metrics, AI assistant usage and cost monitoring, audit log viewer, feature flags.

### Epic J — Money (final phase)

**J1. Shelter subscriptions.** Plan selection, Stripe checkout, invoices, plan limits enforced in-product, self-service upgrade, downgrade and cancellation.

**J2. Donations.** One-off and recurring donations from adopters, optionally attributed to a specific shelter, with receipt by email, an optional public thank-you (never itemised, never showing amounts), and an anonymous option.

### Epic K — Welcome Kit (hard-to-place incentives)

Practical goods — bowl, lead, harness, bed, carrier, a first bag of food, a voucher toward the first veterinary check — given to adopters of animals that have been hardest to place. Deferred to Phase 5, and deliberately constrained by the rules below.

**The tension this resolves.** The obvious design is "offer a kit on animals the model flags as at-risk". That would breach the rule that predictions never reach adopters ([INDEX](./INDEX.md) hard rule 1): a kit badge on a listing is a prediction badge in disguise, and it tells every visitor that this animal is the one nobody wants. Eligibility is therefore defined on **objective, already-public facts**, never on model output.

**K1. Eligibility.** As a platform admin, I want eligibility to be rule-based, so that no prediction leaks to the public.
- An animal qualifies when it meets one or more objective criteria, all of which are already visible on its public profile: **in care longer than 180 days**, **age 8 years or older**, or **flagged as having special needs**.
- Model output is **never** an input to eligibility. This is asserted by a test.
- Criteria and thresholds are configurable per programme, not hardcoded.
- A shelter can opt an individual animal out (some shelters will consider it undignified, and they get to decide).

**K2. Framing.** As an adopter, I want the kit presented as support, not as a discount.
- The badge reads *"Kit di benvenuto incluso"* — never "hard to place", "difficult", "long-term resident", "urgent", or anything implying the animal is a problem.
- Copy frames it as help with the practical start: *"Chi adotta un animale adulto o con esigenze particolari riceve tutto l'occorrente per i primi giorni."*
- The kit is **never** described as compensation, and the animal is never described as a burden.
- A dedicated page explains the programme, who funds it, and why it exists — visible before adoption, not a surprise at handover.

**K3. Fulfilment.** As shelter staff, I want to record that a kit was given, so that the programme can be audited and measured.
- The kit is granted **on completed adoption**, not on application — it must never be an incentive to apply, only support for someone who has already decided.
- Handed over physically by the shelter at collection, with the grant recorded against the adoption.
- Where a partner ships directly, the adopter's address is shared only with explicit consent, for that single purpose.
- Stock or budget per programme is tracked; when a programme is exhausted, badges disappear rather than promising what cannot be delivered.

**K4. Funding.** As a platform admin, I want programmes funded by partners or the donation fund, not from operating margin.
- A programme records its funder (pet-food or accessory brand, local business, or the unattributed donation fund), its budget, and its period.
- Partner attribution is a discreet line on the programme page, never a logo on an animal's profile.
- No partner ever influences which animals qualify, or ranking of any kind.

**K5. Measurement.** As a platform admin, I want to know whether this works, so that we can stop if it does not.
- Tracked per eligible animal: time-to-adoption with and without an active kit programme, application volume, and — the metric that decides it — **12-month return rate for kit adoptions versus non-kit adoptions of comparable animals**.
- The programme is treated as an experiment with a stated kill condition: if kit adoptions return at a materially higher rate, the programme ends. See open question 7 in the [INDEX](./INDEX.md).

**Risks, recorded rather than assumed away.**
- *Adverse selection* — goods may attract adopters motivated by the goods. Mitigated by granting at completion rather than application, by keeping value modest (~€40–70 of practical items), and by never offering cash or fee reductions.
- *Dignity* — the badge risks marking an animal as unwanted. Mitigated by objective public criteria, careful copy, and shelter opt-out.
- *Perverse incentive on shelters* — a shelter could hold an animal to 180 days to unlock a kit. Mitigated because eligibility criteria are also independently visible and length of stay is a metric shelters are measured on improving, not extending.

## 6. Screen inventory

### Public

| Screen | Route (Italian locale) | Notes |
|---|---|---|
| Home | `/it` | Hero, quiz entry point, featured animals, how it works, shelters strip, trust signals |
| Browse / search | `/it/animali` | Filters, grid/map toggle, sort, pagination |
| Map view | `/it/animali/mappa` | Same filters, map-first |
| Animal profile | `/it/animali/[slug]` | Gallery, behaviour, health summary, shelter card, apply |
| Quiz | `/it/match` | Multi-step, one question per screen |
| Match results | `/it/match/risultati` | Ranked cards with scores and explanations |
| Shelter directory | `/it/strutture` | Searchable list and map |
| Shelter profile | `/it/strutture/[slug]` | About, available animals, contact, donate |
| Application form | `/it/animali/[slug]/candidatura` | Auth required, multi-step |
| Adopter dashboard | `/it/area-personale` | Applications, visits, favourites, profile, notifications |
| Favourites | `/it/area-personale/preferiti` | |
| Adopter profile editor | `/it/area-personale/profilo-adottante` | Re-take or amend quiz answers |
| Notifications | `/it/area-personale/notifiche` | |
| Donation | `/it/sostieni` | One-off or recurring, optional shelter attribution |
| Welcome Kit | `/it/kit-di-benvenuto` | What the programme is, who qualifies, who funds it (Epic K) |
| Assistant | Persistent widget + `/it/assistente` | Full-page conversation view |
| Auth | `/it/accedi`, `/it/registrati`, `/it/recupera-password` | |
| Content | `/it/come-funziona`, `/it/guide/[slug]`, `/it/chi-siamo`, `/it/per-le-strutture` | Care guides double as SEO surface |
| Legal | `/it/privacy`, `/it/cookie`, `/it/termini` | |
| System | `404`, `500`, maintenance | |

### Shelter (authenticated, `/it/gestione/...`)

| Screen | Notes |
|---|---|
| Dashboard | KPI tiles, charts, at-risk triage list, alerts |
| Animals list | Table with filters, bulk actions, status chips, prediction column |
| Animal editor | Tabbed: identity, behaviour, media, medical, publication |
| Medical log | Timeline, add entry, vaccinations, weight chart, due reminders |
| Applications queue | Filterable list, per-application detail with decision actions |
| Visit calendar | Week and month views, slot creation, bookings, no-show marking |
| Availability settings | Recurring patterns, blackout dates, booking cutoff |
| Staff | Member list, invitations, removal |
| Shelter settings | Public profile, address and map position, capacity, contact, languages |
| Assistant (staff mode) | Scoped conversational access to the shelter's own data |
| Billing | Current plan, usage against limits, invoices, upgrade |
| Import | CSV upload, mapping, validation preview |

### Platform admin (`/admin/...`)

| Screen | Notes |
|---|---|
| Shelter approvals | Pending queue, detail, approve/reject with reason |
| Shelters | All shelters, status, plan, activity |
| Users | Search, role, status, suspend |
| Moderation | Reported or flagged listings, takedown with reason |
| Platform metrics | Adoptions, applications, active shelters, funnel, growth |
| AI monitoring | Conversation volume, token cost, error and refusal rates, flagged exchanges |
| Welcome Kit programmes | Create programmes, set criteria and budget, funders, grants issued, effectiveness vs return rate |
| Audit log | Filterable by actor, entity, action, date |
| Feature flags | Per-environment toggles |

## 7. Roles and permissions

Three roles. There is deliberately **no** volunteer tier: within a shelter every member has identical permissions, because splitting them adds permission surface that small organisations will not maintain correctly. The `is_billing_contact` flag on a membership designates who receives billing communication; it grants no extra powers over animals or applications.

| Capability | Adopter | Shelter member | Platform admin |
|---|---|---|---|
| Browse, match, favourite | ✅ | ✅ | ✅ |
| Apply to adopt | ✅ | ✅ | ✅ |
| Create / edit animals | — | Own shelter only | Read-only across all |
| View applications | Own only | Own shelter only | Read-only across all |
| Decide applications | — | Own shelter only | — |
| Manage slots and visits | — | Own shelter only | Read-only |
| View medical records | — | Own shelter only | Only on abuse investigation, audit-logged |
| Staff assistant | — | Own shelter only | — |
| Approve shelters | — | — | ✅ |
| Moderate listings | — | — | ✅ |
| Impersonate users | — | — | ❌ (never) |

Every cross-tenant read by a platform admin is written to the audit log.

## 8. Cross-cutting requirements

- **Bilingual everywhere.** Every user-facing string, email, WhatsApp template, notification and assistant reply exists in Italian and English. Shelter-authored content (animal stories, shelter descriptions, alt text) has per-language columns; when a translation is missing the UI falls back to the available language and labels it.
- **Mobile-first.** Shelter staff work from phones. Every shelter screen must be usable on a 390 px viewport, including the applications queue and the animal editor.
- **Accessibility.** WCAG 2.1 AA. Alt text on animal media is required, not optional — it is also how blind adopters and search engines read the listing.
- **Performance budget.** Public pages render meaningful content in under 2.5 s on a 4G connection; search results respond in under 500 ms at 10,000 animals; images are served in modern formats at the size actually displayed.
- **Works without third-party credentials.** In development the app runs with no Stripe, no email provider, no WhatsApp and no Claude key: payments are stubbed, emails are written to a local dev mailbox, WhatsApp logs to console, the assistant returns a fixed canned response, and the ML service falls back to a documented heuristic. A missing integration degrades a feature; it never breaks the app.
- **Honesty about AI.** Anywhere a prediction or an AI-generated text appears, it is labelled, dated, and accompanied by its limitations. Predictions are never shown to adopters — they exist to help shelters allocate effort, and showing an adopter that an animal is "unlikely to be adopted" would be both cruel and self-fulfilling.

## 9. Out of scope

Not in this product, and not to be smuggled in during the build:

- Species other than dogs and cats
- Lost-and-found / missing animal reporting
- A structured fostering programme (foster placements are recorded as a status only)
- Veterinary invoicing, clinical decision support, or legally binding health records
- Native mobile applications (the web app is responsive; a PWA is a later consideration)
- Adopter-to-adopter social features, public comments, ratings or reviews of shelters
- Direct integration with regional anagrafe canina systems (the microchip number is stored and displayed; no API integration exists to build against)
- Animal transport logistics
- Multi-currency (EUR only)
- White-label deployments on custom domains

## 10. Plan limits

Enforced in-product from phase 5; the schema and UI account for them from phase 1 so nothing needs retrofitting.

| | Free | Base | Pro |
|---|---|---|---|
| Animals in care | 15 | 60 | Unlimited |
| Members | 2 | 6 | Unlimited |
| Photos per animal | 5 | 10 | 10 |
| Video per animal | — | 1 | 1 |
| ML predictions | — | ✅ | ✅ |
| Analytics dashboard | Basic tiles | Full | Full + export |
| Staff assistant | — | Limited monthly quota | Higher quota |
| Visit scheduling | ✅ | ✅ | ✅ |
| CSV import | — | ✅ | ✅ |
| Support | Email, best effort | Email | Priority + onboarding call |

Price points and rationale live in [10 — Marketing Plan](./10-marketing-plan.md). Exceeding a limit never deletes or hides existing data: it blocks the creation of new records and says which plan lifts the limit.
