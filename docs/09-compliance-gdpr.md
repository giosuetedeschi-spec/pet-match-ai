# 09 — Compliance & GDPR

> This document describes the design decisions taken to be compliant. It is engineering documentation, not legal advice. Before public launch, the privacy policy, terms of service and the shelter data-processing agreement must be reviewed by a lawyer qualified in Italian and EU data protection law. Two items in particular need professional input: the controller/processor characterisation in §2 and the WhatsApp consent mechanics in §5.

## 1. Why this is a first-class concern

PetMatch AI processes the personal data of private individuals in the EU: names, email addresses, phone numbers, home descriptions, household composition **including the ages of children**, and lifestyle information. Some of that is data people would not casually hand over, and the household composition of a family with young children is genuinely sensitive in the ordinary sense of the word even where it is not "special category" data under Article 9.

Retrofitting compliance is expensive and produces bad results. Consent capture, retention rules and erasure paths are built in Phase 1, before there is any real data to migrate.

## 2. Roles under the GDPR

| Processing | Controller | Notes |
|---|---|---|
| Adopter accounts, profiles, matching, assistant conversations | **PetMatch AI** | We determine purposes and means |
| Adoption applications, once submitted to a shelter | **Shelter** (controller), PetMatch AI (processor) | The shelter decides how to evaluate; we provide the tooling |
| Animal records | **Shelter** | Animal data is not personal data, but the record can contain staff names and vet details |
| Shelter staff accounts | **PetMatch AI** | Account administration |
| Platform analytics | **PetMatch AI** | |

The dual role on applications is the awkward part and needs explicit contractual treatment: a **data processing agreement** is part of shelter onboarding, presented and accepted at registration, covering purpose limitation, our sub-processors, security measures, breach notification timelines, and what the shelter may and may not do with applicant data (in particular: not exporting applicant contact details for its own marketing).

## 3. Lawful bases

| Processing activity | Lawful basis | Notes |
|---|---|---|
| Account creation and authentication | Contract (Art. 6(1)(b)) | Necessary to provide the service requested |
| Adopter profile and matching | Contract | The user asked to be matched |
| Submitting and processing an application | Contract | Pre-contractual steps at the data subject's request |
| Visit scheduling | Contract | |
| Transactional notifications (application status, visit reminders) | Contract | Not marketing; no consent needed, but preferences are still offered |
| WhatsApp as a channel | **Consent** (Art. 6(1)(a)) | Separate, explicit, opt-in, revocable — see §5 |
| Marketing email and new-match digests | **Consent** | Separate from transactional; one-click unsubscribe |
| Analytics cookies | **Consent** | Opt-in, rejectable with equal ease |
| Strictly necessary cookies (session, CSRF, consent state) | No consent required | Documented in the cookie policy |
| Security logging, abuse prevention | Legitimate interest (Art. 6(1)(f)) | Balancing test documented; IPs hashed |
| Fraud/misuse detection on shelter accounts | Legitimate interest | |
| Retaining consent records | Legal obligation (Art. 7(1) accountability) | Survives account deletion |
| Retaining donation records | Legal obligation | Italian accounting law |
| Model training | **Not applicable to personal data** | Models are trained on the public Austin animal dataset and, later, on animal outcome data. **No adopter personal data is ever used for training.** |

That last line is a design commitment, not a current-state description. It is written into the terms and enforced by the fact that the ML feature set (see [05](./05-ml-spec.md) §3) contains no adopter-derived fields at all.

## 4. Data inventory

| Category | Fields | Where | Retention |
|---|---|---|---|
| Account | email, name, phone, password hash, locale | `users` | While active |
| Session | token hash, hashed IP, user agent | `sessions` | Until expiry |
| Adopter lifestyle | housing, household adults, **children's ages**, existing animals, hours alone, activity, experience, budget, allergies | `adopter_profiles` | While active; deleted on request |
| Application content | motivation, home description, household summary, previous animals | `applications` | 24 months after terminal status |
| Application snapshot | copy of the profile at submission | `applications.profile_snapshot` | With the application |
| Visits | schedule, attendance | `visits` | 24 months |
| Match results | scores, reasons, generated text | `match_results` | 90 days after last profile update |
| Conversations | message content, tool payloads | `conversations`, `messages` | 12 months; 30 days if anonymous |
| Notifications | type, payload, delivery status | `notifications`, `notification_deliveries` | 6 months |
| Consents | type, granted, version, hashed IP/UA | `consents` | 5 years after revocation |
| Audit | actor, action, entity, before/after | `audit_log` | 24 months |
| Donations | name, email, amount, Stripe references | `donations` | 10 years (accounting) |
| Shelter staff | name, email, phone, membership | `users`, `shelter_members` | While the membership lasts |

Deliberately **not** collected: date of birth, fiscal code (*codice fiscale*) for adopters, identity documents, income, precise home address before approval, payment card data (Stripe holds it; we never touch it), and precise geolocation (a comune-level location is sufficient for search, and browser geolocation is used transiently and never stored without consent).

Children's ages are collected as **age bands** at the point of the questionnaire, stored as integers only where the adopter provided them, used solely for compatibility scoring, and never displayed to a shelter except within an application the adopter chose to submit.

## 5. Consent

Consent is captured through the `consents` table, **append-only** — a withdrawal is a new row with `granted = 0`. Each row records the policy version, timestamp, and hashed IP and user agent, because Article 7(1) requires being able to *demonstrate* consent, which an updated boolean cannot do.

| Consent point | Where | Granularity |
|---|---|---|
| Terms and privacy | Registration | Separate checkboxes, neither pre-ticked, both linked in full |
| Cookies | First visit banner | Per category: necessary (no choice), analytics, marketing |
| Marketing email | Registration and settings | Opt-in, unticked by default |
| New-match digests | Quiz completion and profile settings | Opt-in, separate from marketing |
| WhatsApp | Notification settings | Explicit opt-in, off by default, per-type |
| Home visit | Application form | Explicit, application-specific |

**Banner design is a compliance requirement, not an aesthetic one.** "Accetta tutti" and "Rifiuta tutti" have identical visual weight — same size, same contrast, same position. No dark patterns, no "legitimate interest" pre-toggled sub-settings, no cookie wall. Analytics does not run until the choice is made, and refusal is remembered so the banner does not reappear on every visit.

**WhatsApp** is the strictest case. Beyond GDPR consent, the WhatsApp Business Platform requires opt-in obtained through a channel the user recognises, restricts business-initiated messages to approved templates, and requires honouring opt-out. Our implementation: off by default, explicit opt-in with the number confirmed, templates approved in advance and stored with their identifiers, `STOP` in any casing handled through the inbound webhook writing a revocation row and disabling the channel across every notification type.

## 6. Data subject rights

All rights are exercisable from `/it/area-personale/privacy` without contacting support, plus an email route for people without an account. Responses within 30 days as required, with the automated paths resolving in minutes.

| Right | Implementation |
|---|---|
| **Access** (Art. 15) | Self-service export: a JSON archive of the account, profile, applications, visits, favourites, conversations, notifications and consent history, generated as a job and delivered through a signed, expiring link |
| **Rectification** (Art. 16) | All profile and application fields editable; submitted applications editable through the "request info" flow, so the shelter sees the correction rather than a silent change |
| **Erasure** (Art. 17) | Self-service deletion — see §7 |
| **Restriction** (Art. 18) | Profile deactivation stops all matching and notifications while retaining the account |
| **Portability** (Art. 20) | The same export, in machine-readable JSON with a documented schema |
| **Objection** (Art. 21) | One-click opt-out of every optional processing activity |
| **No automated decision-making** (Art. 22) | **No decision with legal or similarly significant effect is automated.** Match scores are suggestions to a human; ML predictions concern animals, not people; adoption decisions are made by shelter staff. This is stated plainly in the privacy policy and is a hard product constraint — a future "auto-reject applications below X" feature would break it and must never be built. |

## 7. Erasure procedure

Deletion is not `DELETE FROM users`. Applications and their events are shelter records with their own retention basis, and outcome history is the platform's institutional memory. The procedure is therefore **anonymisation of the person, preservation of the record**:

```
1. Verify identity (re-authenticate) and confirm intent with a clear statement of consequences.
2. Immediate:
   - all sessions destroyed
   - users.status = 'deleted', deleted_at set
   - email → deleted-{ulid}@anonymized.invalid, name → "Utente eliminato",
     phone → NULL, password_hash → NULL
   - adopter_profiles row deleted
   - match_results deleted
   - favorites deleted
   - conversations and messages deleted
   - notifications and deliveries deleted
   - pending applications withdrawn, with the shelter notified
3. Preserved with the person anonymised:
   - applications and application_events: free-text fields cleared,
     the record and its status history retained for the shelter's 24-month period
   - visits: attendance history retained, applicant anonymised
   - outcomes: adopter_user_id nulled, the adoption event itself retained
   - audit_log: actor pseudonymised, entries retained
4. Retained under legal obligation, stated explicitly to the user before they confirm:
   - consents (5 years) — proof of what was agreed and when
   - donations (10 years) — accounting
5. A completion record is written and confirmation emailed to the address on file
   before it is anonymised.
```

The confirmation screen lists exactly what will be deleted and what will be kept and why, before the user confirms. Nobody should discover after the fact that something survived.

Cascade behaviour in the schema is chosen to match this procedure — which is why `applications` has no `ON DELETE CASCADE` from `users`, and `adopter_profiles` does.

## 8. Security measures

| Measure | Implementation |
|---|---|
| Passwords | Argon2id, per-user salt, never logged, never emailed |
| Transport | TLS everywhere, HSTS, secure cookies |
| Sessions | Database-backed, httpOnly, SameSite=Lax, immediate revocation on suspension |
| Access control | Two enforcement layers (route + query), cross-tenant reads audit-logged |
| At rest | Provider-level disk encryption; medical attachments private with signed short-lived URLs |
| Logging | No personal data, no message content, no medical text; IPs stored only as salted hashes |
| Rate limiting | Authentication, application submission, assistant, uploads |
| Injection | Parameterised queries throughout; Zod validation on every input |
| Uploads | Type and size validation, **EXIF stripped including GPS**, never-trusted filenames, generated storage keys |
| Dependencies | Automated vulnerability scanning in CI |
| Secrets | Environment only; CI secret scanning |
| Backups | Daily, encrypted, retention 30 days, restore rehearsed before launch and quarterly after |
| Breach response | Documented procedure; 72-hour notification to the Garante; affected users notified where the risk is high |

Stripping GPS from photo EXIF deserves emphasis: shelter volunteers photograph animals on personal phones, and an un-stripped photo publishes the coordinates of wherever it was taken.

## 9. Sub-processors

Disclosed in the privacy policy with purpose, location and transfer safeguard. Users are notified before a new one is added.

| Sub-processor | Purpose | Data | Location |
|---|---|---|---|
| Hosting provider | Application and database | All | EU (requirement — the provider chosen must offer EU regions) |
| Object storage | Media | Animal media, medical attachments | EU |
| Anthropic (Claude) | AI assistant, match explanations | Conversation content, structured animal/profile facts | US — SCCs; no assistant data used for training under the API terms |
| Email provider | Transactional email | Email address, message content | EU preferred |
| Meta (WhatsApp Business) | WhatsApp notifications | Phone number, template variables | US — SCCs; consent-gated |
| Stripe | Payments | Billing details, donation data | US/EU — SCCs; card data never touches our systems |
| Error reporting | Diagnostics | Hashed identifiers, no personal data | EU, with scrubbing configured |

**What the assistant sends to Claude** is worth stating explicitly in the privacy policy in plain language: the user's message, conversation history, retrieved knowledge-base excerpts, and structured facts about animals. For match explanations: the animal's public attributes and a *summary* of the adopter profile (housing type, hours alone, activity level, experience) — never name, email, phone, address, or children's ages.

## 10. Italian specifics

### Microchip and anagrafe canina

Italian law requires dogs to be microchipped and registered in the regional *anagrafe canina*; registration transfers to the new owner on adoption, within a deadline that varies by region.

Our handling:
- `animals.microchip_number` — 15 digits, format-validated, unique platform-wide
- `animals.microchip_registered_on` and `animals.anagrafe_region` — the registry the chip is filed with
- The number is **never published**: it appears only to the owning shelter's members, because a public microchip number is an identity-theft vector for animals
- On adoption, the shelter is prompted with a reminder that ownership transfer must be recorded in the regional anagrafe, with a link to the relevant regional service
- **No API integration.** There is no national interoperable interface to build against; regional systems are heterogeneous. Claiming integration we cannot deliver would be worse than the manual reminder.
- Cats are handled identically where a regional feline registry exists, and the field is optional otherwise

### Adoption eligibility

Surfaced in the application form as informational requirements, since they are set by law and by each shelter rather than by us:
- Adopters must be adults; the form states this and the terms require it
- Some shelters require residence in a given region or comune, or forbid adoption by non-residents — a shelter-configurable note shown on the application form
- Adoption is free of charge in municipal shelters; where a contribution is requested it is displayed as *contributo*, never *prezzo*, and never processed as a platform payment

### Consumer and e-commerce law

The platform never sells animals, so distance-selling rules do not apply to adoptions. They **do** apply to shelter subscriptions: pre-contractual information, the right of withdrawal for the subscription, and clear pricing including VAT are handled in the billing flow.

### Language

Privacy policy, cookie policy and terms exist in Italian as the authoritative version, with an English translation clearly marked as a courtesy translation.

## 11. Compliance checklist by phase

**Phase 1** — cookie banner with equal-weight options · privacy and cookie policies published · consent records on registration · account deletion working end to end · EXIF stripping · IP hashing in logs · data processing agreement in shelter onboarding

**Phase 2** — separate consent for match digests · one-click unsubscribe without login · adopter profile deletion cascading to match results

**Phase 3** — confirmation in the privacy policy that no adopter data reaches model training · animal predictions documented as animal data

**Phase 4** — WhatsApp opt-in and `STOP` handling · application retention job · applicant-data boundaries enforced in the shelter UI · the data processing agreement covering application data specifically

**Phase 5** — sub-processor list complete and published · Stripe data flows documented · assistant conversation retention job · breach response procedure written and rehearsed · full legal review before public launch
