# 10 — Marketing Plan

> **Do not act on this document yet.**
> It exists so that the product is built with distribution in mind — the events we instrument, the pages we make indexable, the plan limits we design. Execution begins only when Phase 1–4 are shipped and a pilot shelter is using the product for real. Launching a marketplace with an empty catalogue is the one mistake that cannot be undone: adopters who arrive to find nothing do not come back.
>
> **Verification flag.** Market-size figures, competitor capabilities and price benchmarks in this document are estimates and reasoned inference, not researched fact. Every figure marked ⚠️ must be verified against primary sources before it informs a decision or appears in any external material.

---

## Part I — Positioning

### 1. The strategic problem

This is a two-sided marketplace, which means the classic cold-start problem: adopters will not come without animals, and shelters will not join without adopters. Most such platforms die in that gap.

**The wedge that avoids it:** PetMatch AI is useful to a shelter on day one, with zero adopters on the platform.

A shelter that signs up gets a working animal registry, a medical log, a public page it can link from Facebook, and — from Base upward — forecasting that tells it which animals need help. That is worth having even if we send it no traffic at all. Adopter-side demand is a compounding benefit layered on top, not the entry condition.

This inverts the usual sequencing. **We are a shelter tool that becomes a marketplace**, not a marketplace that needs shelters. It also dictates the launch geography: go deep in one region until the catalogue there is genuinely dense, then open adopter acquisition in that region only.

### 2. Positioning statement

> For small and medium Italian shelters and animal associations that manage adoptions with spreadsheets, paper and Facebook, **PetMatch AI** is an adoption platform that keeps the animal registry, forecasts which animals will struggle to be placed, and matches adopters to animals on lifestyle rather than looks.
>
> Unlike national listing portals — which publish animals and stop — PetMatch AI gives the shelter the operational tools, and gives the adopter an explained match instead of a photo grid.

### 3. Messaging pillars

**To shelters:**

| Pillar | The line | The proof |
|---|---|---|
| Order out of chaos | "I tuoi animali, finalmente in un posto solo." | Registry, medical log, CSV import, mobile-first |
| See the problem early | "Sai quali animali rischiano di restare, prima che restino." | Forecasting and triage with suggested actions |
| Fewer repeated questions | "L'assistente risponde alle domande di sempre." | AI assistant on the public listings |
| Better applications | "Candidature complete, non messaggi su Facebook." | Structured applications and review queue |
| No risk | "Gratis per iniziare. Nessuna installazione." | Free tier, browser only, export your data whenever |

**To adopters:**

| Pillar | The line | The proof |
|---|---|---|
| The right animal, not the cutest photo | "Non il più bello. Quello giusto per te." | 14-question quiz, 8-dimension scoring |
| Explained, always | "Ti diciamo sempre perché." | Reason bullets and honest considerations on every match |
| Honesty about what is unknown | "Se non lo sappiamo, te lo diciamo." | `unknown` shown as unknown, never smoothed |
| Real shelters, real animals | "Solo strutture verificate." | Admin approval before publication |

**Brand line:** *Ogni animale ha già una famiglia. Deve solo incontrarla.*

### 4. Ideal customer profiles

**Primary ICP — the shelter that pays.** ⚠️ Sizing to verify.

| Attribute | Profile |
|---|---|
| Type | Canile privato under municipal convention, gattile, or a volunteer association with a physical facility |
| Size | 25–150 animals in care |
| Staff | 1–5 paid, plus volunteers |
| Current tooling | Excel, WhatsApp groups, a Facebook page, possibly a neglected website |
| Budget | Small but real; already pays for food, vets, insurance, sometimes a website |
| Decision maker | The president or operations lead — one person, reachable, decides in a single conversation |
| Trigger | A volunteer leaves and takes the knowledge with them; a municipal reporting obligation; an animal that has waited two years |
| Anti-profile | Municipal shelters where procurement is public tendering (long, formal, not a self-serve motion); breeders and resellers (never accepted) |

Italy has on the order of ⚠️ 1,000+ registered canili/rifugi and several thousand active associations. If the addressable set is ~3,000 organisations and 15% eventually adopt a tool like this, the ceiling is ~450 paying accounts — a real business at our price points, not a venture-scale one. That shapes everything: this is a capital-efficient, high-margin, slow-compounding product, and the plan below is written for that shape rather than for a growth-at-all-costs one.

**Secondary ICP — the adopter.** 25–45, urban or peri-urban, moderate-to-high digital comfort, first or second animal, researching for weeks before acting, anxious about doing it right. Reached through search (they are actively looking) and social proof (they are being reassured), not through paid interruption.

**Tertiary — institutions.** Comuni, ASL veterinary services, regional animal-welfare offices, and the national associations (ENPA, LAV, OIPA, LNDC). Slow, but a single association endorsement can carry dozens of local branches. Worth cultivating from month one, worth expecting nothing from until month twelve.

### 5. Competitive landscape

⚠️ **Every row needs verification before external use.** These are categories with representative examples, characterised by what such services typically do, not by audited feature comparisons.

| Category | Examples | What they do well | The gap |
|---|---|---|---|
| National association portals | ENPA, LAV, OIPA, LNDC listings | Trust, brand recognition, reach, genuine authority | Listing only — no shelter-side tooling, no matching, uneven data quality, generally limited to affiliated branches |
| Municipal and institutional pages | Comune websites, regional anagrafe portals | Official, authoritative | Often PDF-era, rarely updated, no adopter experience at all |
| Social media | Facebook groups and pages, Instagram | Where adoption *actually* happens today; enormous reach, zero cost, immediate | Ephemeral, unsearchable, no structure, no record, no follow-up; reach is at the platform's mercy |
| General classifieds | Subito.it, Kijiji and similar | Traffic, familiarity | Not adoption-oriented; animals adjacent to commerce, which is precisely the framing we reject |
| Shelter management software | International vendors (Shelterluv, PetPoint, ShelterBuddy and similar) | Mature, deep operational features | US/UK-centric, English-first, priced for larger organisations, no Italian localisation or anagrafe awareness, no consumer-facing marketplace |
| International adoption marketplaces | Petfinder, Adopt-a-Pet | Enormous catalogues, strong SEO, category-defining | Not present in the Italian market |

**Where the gap actually is:** nobody serves the Italian small shelter with *both* an operational tool and a consumer-facing matching experience, in Italian, at a price a volunteer association can approve without a board meeting. The international SaaS vendors have the tooling but not the market; the national portals have the market but not the tooling; Facebook has the audience but no structure.

**Our defensibility is honest and limited.** The software is copyable. What compounds is: (1) shelter switching cost once records live with us, (2) SEO accumulated across thousands of indexed animal pages, (3) the local outcome dataset that makes the model progressively better than any cold-start competitor, and (4) association relationships. Points 2 and 3 take a year to matter, which is another argument for the slow, deep, one-region start.

**The real competitor is not any of these. It is inertia** — the spreadsheet plus the Facebook page, which is free, familiar, and works well enough. Every message should be aimed at that, not at other software.

---

## Part II — Go to market

### 6. Sequencing

```
Month 0–2   PILOT       3–5 shelters, one region. No marketing. Product truth.
Month 3–5   REGION      30–40 shelters in one region. Adopter demand switched on locally.
Month 6–9   ADJACENT    Expand to 2–3 neighbouring regions. Paid tiers introduced.
Month 10–12 NATIONAL    Open registration nationally. Associations. PR.
```

**Region choice.** Lombardia is the default: highest density of shelters and adopters, largest media market, shortest travel for in-person onboarding. ⚠️ Verify against actual shelter density data; Veneto and Emilia-Romagna are plausible alternatives with strong associative networks and possibly less competition for attention.

### 7. Shelter acquisition

This is a **high-touch, low-volume sales motion**, and pretending otherwise wastes a year. At ~450 addressable accounts, personal contact with every one of them is feasible. There is no growth hack here; there is a list and a phone.

**The playbook:**

1. **Build the list.** Regional shelter registries, association directories, comune pages. Name, organisation, phone, email, approximate size, current web presence. This is manual work and it is the foundation of everything.
2. **Warm before cold.** Volunteer at two shelters. Show up. The first five customers should come from people who have met you, because the first five determine whether the product is actually right.
3. **Do the work for them.** The offer is not "sign up" — it is *"send me your spreadsheet and I'll have your animals online by Friday."* Free onboarding, done by us, is the single highest-leverage acquisition tactic available and it is unscalable on purpose.
4. **Lead with the artefact.** Before any pitch, produce the shelter's public page populated with their real animals and send it. A working page beats any deck.
5. **One conversation, one decision.** Twenty minutes, screen shared, their animals on screen. The free tier means there is no procurement, no budget approval, no committee.
6. **Association endorsement, patiently.** Approach regional branches of ENPA/LAV/OIPA/LNDC once 20+ shelters are live and can vouch. An endorsement without proof is a cold ask; with proof it is a formality.
7. **Veterinary clinics and comuni** as referral surfaces — clinics see adopters at the moment of intent; comuni have an obligation to promote adoption and no tooling to do it.

**The outreach message** (email or WhatsApp — WhatsApp is how Italian associations actually communicate; ⚠️ respect the opt-in rules that apply to us as much as to our users):

> Buongiorno [Nome],
>
> ho visto i cani in adozione sulla pagina di [Struttura] — Rocco è lì da parecchio, se ho capito bene.
>
> Sto costruendo uno strumento gratuito per le strutture come la vostra: anagrafica animali, cartella sanitaria, e una pagina pubblica dove chi cerca può filtrare per taglia, età e compatibilità.
>
> Ho già caricato i vostri animali dalla pagina Facebook per farvi vedere com'è: [link]. Se non vi interessa, cancello tutto oggi stesso e non vi disturbo più.
>
> Se invece vi va, vi metto online il resto io, gratis, entro questa settimana.

Short, specific, shows work already done, offers a clean exit. The specificity — naming a real animal that has been waiting — is what separates it from the software pitches these organisations delete daily.

**Onboarding.** Success is the shelter's animals live and someone logging in twice a week. Concretely: we import the data, we take or edit the photos where needed, we run a 30-minute walkthrough, we check in at day 7 and day 30. Anything less and the account goes dormant, and a dormant account is worse than no account — it is a reference we cannot use.

### 8. Adopter acquisition

Switched on **per region, only once that region has 20+ shelters and 200+ available animals.** Before then, adopter traffic is wasted and actively harmful to reputation.

**SEO is the primary channel, and it is a product decision as much as a marketing one.** Adopters search with high intent — *"cani in adozione Milano"*, *"adottare gatto Roma"*, *"cane taglia piccola adozione appartamento"* — and that intent converts. It also compounds: every animal page is an indexed asset, and a shelter with 60 animals is 60 pages we did not have to write.

| Surface | Approach |
|---|---|
| Animal pages | Server-rendered, structured data, rich metadata, real content. Thousands of long-tail pages. On adoption, the page becomes an "adopted" story with a redirect rather than a 404 — the link equity stays, and the story is good content |
| City × species pages | *"Cani in adozione a Milano"* — programmatic but genuinely useful: live counts, real animals, local shelters, local context. Not thin doorway pages |
| Shelter pages | Each shelter's page targets its own name and locality; shelters link to it themselves, which is how the backlinks arrive |
| Care guides | The knowledge base doubles as the SEO content hub and the assistant's grounding — one body of work, two jobs. *"Quanto costa mantenere un cane"*, *"adottare un cane in appartamento"*, *"cosa serve per adottare un gatto"* |
| Comparison and decision content | *"Cane o gatto: cosa è giusto per te"* — top of funnel, natural entry to the quiz |

Realistic expectation: ⚠️ meaningful organic traffic takes 6–9 months. Plan the year assuming SEO contributes nothing until month six and everything by month eighteen.

**Social.** Instagram and TikTok, format-native and animal-led. The content that works is not promotional: long-stay animals, adoption day videos, before/after shelter arrivals, "why this dog has waited 400 days" explainers. A weekly rhythm — Monday a long-stay animal, Wednesday a care tip from the guides, Friday an adoption story, plus reactive posting when something lands. Shelters supply the raw material; we edit, publish, and hand back the assets for them to reuse. That last part is why shelters cooperate.

**PR angles**, in order of strength:
1. *"Un algoritmo per i cani che nessuno adotta"* — the forecasting story. Technology in service of the animals nobody chooses is a story that writes itself.
2. The data story — with enough platform data, "how long animals actually wait in Italy, by region and by size" is original research nobody else can publish. This is the strongest asset and arrives in year two.
3. The founder story — a solo build, told concretely, works well in Italian tech and startup press.
4. Local first: provincial newspapers and regional radio cover the local canile eagerly and reach exactly the people who adopt. Cheaper, faster, and better-converting than national coverage.

**Creators.** Micro-influencers in the Italian animal space (10–100k) with genuine shelter involvement, compensated with donations to their chosen shelter rather than fees. Aligned incentives, better content, lower cost, no disclosure awkwardness beyond the standard.

**Paid.** Minimal and late. Small Google Search budget on high-intent adoption terms in active regions once conversion is measured — never before, because paying to send traffic to an unmeasured funnel is how budgets disappear. No paid social for adopter acquisition; the organic content performs and the audience is not in a buying mindset.

### 9. Twelve-month plan

⚠️ Budgets are order-of-magnitude planning figures for a solo founder, in EUR, excluding the founder's own time.

| Phase | Months | Focus | Targets | Budget |
|---|---|---|---|---|
| **Pilot** | 0–2 | 3–5 shelters, weekly contact, product truth over growth | 5 shelters · 150 animals · 0 marketing spend | ~€200 (hosting, domain, travel) |
| **Region** | 3–5 | 30–40 shelters in one region; adopter demand switched on locally; SEO foundation; social rhythm begins | 35 shelters · 900 animals · 2,000 monthly visits · first 20 adoptions | ~€1,500 (travel, content, tools) |
| **Adjacent** | 6–9 | 2–3 neighbouring regions; **paid tiers introduced**; first association conversations; local PR | 90 shelters · 2,500 animals · 12,000 monthly visits · 15 paying · 120 adoptions | ~€4,000 (incl. first small paid tests) |
| **National** | 10–12 | Open registration; association partnerships; national PR; donations live | 180 shelters · 5,000 animals · 35,000 monthly visits · 45 paying · 350 adoptions | ~€7,000 |

**Introducing paid tiers is the moment of maximum risk.** The first 40 shelters must be grandfathered on generous terms permanently. They took the risk when the product was unproven, they are the reference customers, and charging them retroactively would cost more in reputation than it could ever earn in revenue.

---

## Part III — Metrics

### 10. The adopter funnel

Targets are hypotheses to be replaced with measurement, not forecasts. ⚠️

| Stage | Event | Target rate | Notes |
|---|---|---|---|
| Visit | `page_view` | — | |
| Engaged | 2+ pages or 30 s | 45% | Below this, the landing page is wrong |
| Quiz started | `quiz_started` | 20% of engaged | Primary home CTA |
| Quiz completed | `quiz_completed` | 65% of started | 14 questions is a real ask; per-question drop-off tells us which to cut |
| Results viewed | `match_results_viewed` | 95% of completed | |
| Animal viewed | `animal_viewed` | 80% of results | |
| Favourited or registered | `favorite_added` / `signup` | 35% | The retention hook |
| Application started | `application_started` | 12% of quiz completions | The step where the decision becomes real |
| Application submitted | `application_submitted` | 70% of started | Below this, the form is too long |
| Shelter responded | `application_reviewed` | 85% within 7 days | **The number that kills the product if it slips.** An adopter met by silence is lost permanently and tells people |
| Visit booked | `visit_booked` | 55% of approved | |
| Adoption completed | `adoption_completed` | 60% of visits | |

**North star: completed adoptions per month.** Not users, not traffic, not shelters. It is the only metric that means the product did its job, and it forces attention on shelter responsiveness — the part of the funnel we do not control and therefore must design around.

**The quality metric that matters more, and arrives later: 12-month return rate**, split by match score band. If high-scoring matches do not return less than low-scoring ones, the matching engine is decoration and [06](./06-matching-algorithm.md) §8 says so plainly. This requires a year of data and a follow-up survey at 1, 6 and 12 months — deferred to post-launch in [08](./08-roadmap.md), and it should not be deferred forever.

### 11. Shelter metrics

| Metric | Definition | Target |
|---|---|---|
| Activation | Published 5+ animals within 14 days of approval | 70% |
| Weekly active shelters | Logged in and took an action | 60% of registered |
| Time to first published animal | Approval → first publication | < 3 days median |
| Records maintained | Animals with a complete behaviour profile | 80% |
| Response time | Application submitted → first shelter action | < 4 days median |
| Free→paid conversion | Of shelters active 3+ months | 25% ⚠️ |
| Monthly logo churn | Paying shelters lost | < 2% |
| Advisory action rate | Suggested actions acted on rather than dismissed | 30% — the honest test of whether the ML feature is useful or ignored |

That last metric deserves emphasis. If shelters dismiss every suggested action, the forecasting feature is expensive decoration and should be cut, however technically satisfying it is. Instrument it from day one so the answer is available before the sunk cost gets emotional.

### 12. Growth loops

Four loops, in descending order of confidence:

**1. SEO content loop (strongest, slowest).**
More shelters → more animal pages → more indexed long-tail pages → more organic traffic → more adoptions → more shelter credibility → more shelters. Compounds indefinitely and cannot be bought. Requires: indexable animal pages, adopted-animal pages retained as stories, city×species pages, the guides hub.

**2. Shelter-referred adopters.**
Shelters link their PetMatch page from Facebook, Instagram and their own site because it is better than what they had. Their existing audience becomes our traffic and our SEO backlinks. Requires: a genuinely shareable shelter page, embeddable widgets, ready-made social assets we generate for them.

**3. Adoption story loop.**
Completed adoption → we ask for a photo and two lines → published as a story → shared by the adopter and the shelter → seen by their networks → new visitors. Requires: an adoption-story flow at completion, consent handled properly, low-friction submission.

**4. Adopter-referred shelters (weakest, real).**
An adopter who has a good experience mentions it to the shelter they volunteer at or the one they adopted from previously. Requires nothing but a good experience and a visible "sei una struttura?" entry point.

**Explicitly not a loop: paid acquisition.** It is a tap, not a loop. Useful for smoothing, never for growth.

### 13. Instrumentation

Analytics is consent-gated (see [09](./09-compliance-gdpr.md) §5). Prefer a privacy-respecting, EU-hosted, cookieless analytics tool for aggregate traffic — it needs no consent banner interaction to function and covers most of what matters — with product events in our own database, where they are ours and are joinable to outcomes.

Events to instrument from Phase 1 onward, so the funnel exists before it is needed:

```
page_view · search_performed(filters, result_count) · filter_applied(name, value)
map_opened · animal_viewed(id, source) · favorite_added/removed
quiz_started · quiz_question_answered(index) · quiz_abandoned(index) · quiz_completed(duration)
match_results_viewed(count, avg_score) · match_explanation_expanded
signup_started/completed(source) · application_started/submitted/withdrawn
visit_booked/cancelled/completed · adoption_completed
assistant_opened · assistant_message_sent · assistant_animal_card_clicked
shelter_signup · shelter_approved · animal_published · at_risk_action_taken/dismissed
plan_limit_reached(limit_type) · upgrade_started/completed · donation_started/completed
```

`quiz_abandoned(index)` and `plan_limit_reached(limit_type)` earn their place specifically: the first tells us which question is costing us adopters, the second tells us whether the free tier's ceilings are set anywhere near right.

---

## Part IV — Pricing and revenue

### 14. Principles

1. **Free forever for adopters.** Never negotiable. A fee on adopters would be morally wrong and commercially fatal.
2. **The free shelter tier is permanent and genuinely useful**, not a crippled trial. A small association with 12 animals should be able to use PetMatch AI indefinitely for nothing. They are the catalogue that makes the marketplace work, and their goodwill is the distribution channel.
3. **Charge for scale and intelligence, never for the basics.** Records, publication, applications and visit scheduling are free at every tier. Paid tiers unlock volume, forecasting, analytics and the staff assistant.
4. **Price where a small association can say yes without a board meeting.** ⚠️ In practice that ceiling is around €30/month for Base; above it the sale slows dramatically.
5. **Never gate an animal's visibility.** No pay-to-feature, no promoted listings, no algorithmic advantage for paying shelters. The moment adopters suspect the ranking is bought, the matching promise is worthless — and it would be, in fact, corrupt.

### 15. Tiers

| | **Free** | **Base** | **Pro** |
|---|---|---|---|
| Price | €0 | **€24/mo** or €240/yr | **€69/mo** or €690/yr |
| Animals in care | 15 | 60 | Unlimited |
| Members | 2 | 6 | Unlimited |
| Photos / animal | 5 | 10 | 10 |
| Video | — | ✅ | ✅ |
| Public page & catalogue | ✅ | ✅ | ✅ |
| Applications & visits | ✅ | ✅ | ✅ |
| Medical log | ✅ | ✅ | ✅ |
| ML forecasting & triage | — | ✅ | ✅ |
| Analytics | Basic tiles | Full | Full + export |
| Staff assistant | — | 100 queries/mo | 500 queries/mo |
| CSV import | — | ✅ | ✅ |
| Support | Email, best effort | Email, 2 days | Priority + onboarding call |

⚠️ Price points to validate in pilot conversations before being published anywhere.

Annual billing at ten months for twelve — the discount is worth it for cash flow and because annual commitment correlates with the shelter actually embedding the tool in its routine.

**Rationale for the €24 point.** It is a rounding error against a shelter's food and veterinary costs, sits under the threshold that triggers formal approval in most small associations, and is defensible against the single question that decides the sale: *"is this worth less than one bag of food a month?"* The Pro jump to €69 is deliberately large and targets shelters with 100+ animals and paid staff, where the analytics and unlimited members genuinely change how work is done.

**Never charged for:** publishing an animal, receiving an application, an adoption completed, or a donation received (see below).

### 16. Donations

Adopters and visitors can donate, one-off or recurring, optionally attributed to a specific shelter.

**Platform fee: 0%.** ⚠️ Confirm this is sustainable once Stripe's processing fees (roughly 1.5% + €0.25 on European cards) are accounted for — the platform absorbs them rather than deducting from the shelter. Taking a cut of money donated to a shelter would be a reputational cost far exceeding the revenue, and "il 100% arriva alla struttura" is a genuinely differentiating claim worth paying for.

Donations are therefore **not a revenue line.** They are a retention and acquisition feature: shelters that receive donations through us stay, and tell others. Unattributed donations go to a shelter-support fund used to cover the subscriptions of shelters that cannot afford them — which is both the right thing and a good story.

⚠️ Legal check required before launch: whether collecting and forwarding donations makes us a payment intermediary under Italian rules, and what tax-receipt obligations follow. This may require the shelter to be the merchant of record with Stripe Connect rather than us collecting and forwarding.

### 17. Twelve-month revenue scenarios

⚠️ Illustrative. Assumes paid tiers introduced at month 6, the first 40 shelters grandfathered free permanently, and no external funding.

| | Conservative | Base | Optimistic |
|---|---|---|---|
| Shelters registered by M12 | 90 | 180 | 320 |
| Paying by M12 | 18 | 45 | 95 |
| Base / Pro split | 15 / 3 | 36 / 9 | 74 / 21 |
| MRR at M12 | ~€567 | ~€1,485 | ~€3,225 |
| ARR run-rate at M12 | ~€6,800 | ~€17,800 | ~€38,700 |
| Cumulative revenue, M6–M12 | ~€2,300 | ~€6,100 | ~€13,400 |
| Adoptions facilitated | 180 | 350 | 700 |

**Costs, monthly at base scale:** hosting and database ~€40 · object storage and bandwidth ~€25 · Claude API ~€60 (dominated by the staff assistant; controlled by quotas) · email ~€15 · WhatsApp ~€20 · monitoring and tooling ~€30 · domain and miscellaneous ~€10 → **~€200/month**, plus one-off legal review (⚠️ €1,500–3,000) and the marketing budget in §9.

**The honest read.** Base case reaches roughly break-even on direct costs around month nine and produces a run-rate under €20k by month twelve. **This does not pay a salary in year one.** It is a business that becomes interesting in year two or three, at 300–500 paying shelters — or one that justifies itself on impact rather than revenue and is funded accordingly (grants, institutional partnerships, a sponsoring foundation). Deciding which of those it is, honestly, before the money runs low, matters more than any tactic in this document.

**Unit economics:** CAC is dominated by founder time — 3–5 hours per shelter through onboarding, which is €0 cash and expensive in the only resource that is actually scarce. At €24/month with sub-2% monthly churn, LTV is roughly €900–1,400 per Base shelter. The economics work; the constraint is founder hours, and it will stay that way until onboarding is genuinely self-serve. **Making onboarding self-serve is therefore a growth lever disguised as a product task**, and it deserves a place on the roadmap the moment the first thirty shelters are live.

---

## Part V — Naming

### 18. Should it stay "PetMatch AI"?

**Arguments to keep it:** descriptive, immediately understood, works in both languages, contains the core promise (*match*), already in the code and these documents.

**Arguments against:** "Pet" is English and slightly commercial in Italian ears — it is the vocabulary of pet *shops*, and we are explicitly not that. "AI" is a suffix that is ageing fast; it describes the mechanism rather than the value, and in two years it will read the way "2.0" reads now. It is also unlikely to be distinctive enough for trademark purposes. ⚠️ Domain, EUIPO trademark and social handle availability all need checking for any candidate, including the incumbent.

**Recommendation: build as PetMatch AI, decide before the public launch (month 6–9), not before the pilot.** The name matters when there is an audience; changing it while five shelters know you is free, and delaying the decision costs nothing but a find-and-replace.

### 19. Alternatives

| Name | Reading | Why it might work | Risk |
|---|---|---|---|
| **Cuccia** | *kennel, the animal's own bed* | Warm, unmistakably Italian, means "home" more than "shelter". Short, memorable, ownable | Dog-leaning; less natural for cats |
| **Zampe** | *paws* | Simple, affectionate, species-neutral, easy to say and spell | Common word — trademark and domain likely difficult |
| **Adottami** | *adopt me* | Maximum clarity, states the action, excellent for SEO | Very likely taken; imperative tone; says nothing about matching |
| **Casa Giusta** | *the right home* | Captures the actual promise better than any other candidate; works for both species; warm without being cute | Two words; needs a strong mark to hold together |
| **Insieme** | *together* | Emotional, memorable, generic enough to extend | Too generic to own; heavily used |
| **Trovamici** | *find friends* | Playful, Italian, coinable, species-neutral | Reads young; may undercut the serious posture |

**If forced to choose today: "Casa Giusta"** — it names the outcome rather than the mechanism, it is honest about what the product does (finds the *right* home, not the *fastest* one), it survives the AI hype cycle entirely, and it sits comfortably next to a serious tool for shelters. "Cuccia" is the strongest single word and the better brand mark if the cat problem can be designed around.

Whatever is chosen, the descriptor stays functional and boring: *"la piattaforma per l'adozione responsabile"*. The name carries the feeling; the descriptor carries the meaning.

---

## Appendix — Assumptions to validate before acting

Ordered by how badly a wrong answer would hurt.

1. ⚠️ **Will shelters pay anything at all?** Everything downstream assumes yes. Test in pilot conversations, months 0–2, by asking directly rather than inferring from enthusiasm.
2. ⚠️ **Does forecasting change behaviour, or is it just interesting?** Measured by the advisory action rate in §11. If shelters dismiss every suggestion, cut the feature.
3. ⚠️ **Do adopters finish a 14-question quiz?** Measured by `quiz_abandoned(index)`. If completion is under 50%, the questionnaire needs cutting — and [06](./06-matching-algorithm.md) needs revisiting, since fewer questions means fewer scoring dimensions.
4. ⚠️ **Is the addressable market ~3,000 organisations or ~800?** Determines whether this is a business or a project. Verify against registry data before committing a second year.
5. ⚠️ **Do shelters actually respond to applications within days?** The one funnel step we do not control, and the one most likely to break the adopter experience.
6. ⚠️ **Does matching reduce returns?** The product's central claim, unanswerable for 12 months, and the thing that determines whether any of this was worth building rather than merely shippable.
