# 06 — Matching Algorithm

The match score is a **transparent weighted formula**, not a learned model. Three reasons this is the right call:

1. **There is no training data.** Nobody has a labelled dataset of successful adopter–animal pairs, least of all us on day one. A model trained on invented labels would be theatre.
2. **It has to explain itself.** An adopter deciding on a living animal deserves "92% because your flat suits her size and she tolerates the hours you're out" — not a number from a box.
3. **Shelter staff must be able to argue with it.** When Giulia says the algorithm is wrong about senior dogs and first-time owners, we can open this document, look at the weight, and change it. That conversation is impossible with a black box.

The engine lives in `apps/web/lib/matching/` as pure functions: `(AdopterProfile, AnimalWithBehavior) → MatchResult`. No I/O, exhaustively unit-testable, versioned (`engine_version`) so a score can always be traced to the rules that produced it.

## 1. The questionnaire

One question per screen, progress bar, back navigation, resumable. 14 questions, target completion time under four minutes. Every question offers "non lo so" or "preferisco non rispondere" where an honest answer might not exist — a forced answer is a wrong answer, and a wrong answer poisons the match.

| # | Question (IT) | Field | Options |
|---|---|---|---|
| 1 | Che tipo di animale stai cercando? | `preferred_species` | Cane · Gatto · Sono aperto/a a entrambi |
| 2 | Dove vivi? | `housing_type` | Appartamento · Casa senza giardino · Casa con giardino · Cascina/campagna |
| 3 | Quanto è grande, all'incirca? | `housing_size_sqm` | <50 · 50–80 · 80–120 · >120 m² |
| 4 | Hai uno spazio esterno tuo? | `has_outdoor_space`, `outdoor_space_sqm` | No · Balcone/terrazzo · Giardino piccolo · Giardino grande |
| 5 | Chi vive con te? | `household_adults`, `children_ages` | Adulti (numero) + bambini con fasce d'età (0–5, 6–11, 12–17) |
| 6 | Hai già animali in casa? | `existing_dogs`, `existing_cats` | Cani (n) · Gatti (n) · Nessuno |
| 7 | Quante ore al giorno l'animale resterebbe solo? | `hours_alone_per_day` | 0–2 · 3–4 · 5–6 · 7–8 · più di 8 |
| 8 | Quanto sei attivo/a? | `activity_level` | 1 (poco) … 5 (molto) with plain descriptions per level |
| 9 | Hai già avuto animali? | `experience_level` | È la prima volta · Qualche esperienza · Molta esperienza |
| 10 | Quanto tempo puoi dedicare alla cura del pelo? | `grooming_capacity` | 1 (il minimo) … 5 (anche ogni giorno) |
| 11 | Quanto tempo puoi dedicare all'educazione? | `training_capacity` | 1 … 5 |
| 12 | Hai preferenze su taglia, età o sesso? | `preferred_sizes`, `preferred_age_bands`, `preferred_sex` | Multi-select, all optional |
| 13 | C'è qualcosa che per te è escluso? | `dealbreakers` | Multi-select — see §3 |
| 14 | Dove cerchi? | `search_comune_id`, `search_radius_km` | Comune/CAP + radius (10 · 25 · 50 · 100 · 200 km) |

Question 5's children question is asked with care: the ages matter for compatibility, and the UI explains why it is asking rather than simply demanding household composition.

## 2. Scoring dimensions

Eight dimensions, weights summing to 1.00. Each dimension scores 0–100; the final score is the weighted sum, rounded.

| Dimension | Weight | What it compares |
|---|---|---|
| Energy & activity | **0.20** | `activity_level` ↔ `energy_level`, `exercise_min_per_day` |
| Space | **0.15** | `housing_type`, `housing_size_sqm`, outdoor space ↔ `size`, `needs_garden` |
| Time alone | **0.15** | `hours_alone_per_day` ↔ `alone_tolerance_hours` |
| Household | **0.15** | children ages, existing animals ↔ `good_with_children/dogs/cats` |
| Experience | **0.10** | `experience_level` ↔ `training_needs`, `suitable_for_first_time` |
| Care capacity | **0.10** | `grooming_capacity`, `training_capacity` ↔ `grooming_needs`, `training_needs` |
| Stated preferences | **0.10** | size, age band, sex |
| Practical | **0.05** | distance, adoption fee against budget, special needs |

Energy carries the largest weight because energy mismatch is the most common cause of a returned adoption: an under-exercised high-drive dog in a sedentary household becomes a behavioural problem within weeks, and that is the outcome the whole product exists to prevent.

### Handling `unknown`

Any behaviour field may be `unknown`. Unknown never scores as a pass and never scores as a fail: the dimension scores **65** (a neutral-with-a-shrug value), the animal is flagged with a `considerations` entry ("Non è ancora stato testato con i gatti"), and the shelter's dashboard counts it toward that animal's profile-completeness advisory. This is the honest treatment — assuming "yes" is how people end up returning an animal after a week.

## 3. Deal-breakers — exclusion, not penalty

Deal-breakers remove an animal from the results entirely. They are never a score reduction, because a 40-point penalty still leaves a beautiful animal at rank 8, and someone will click it.

| Deal-breaker | Excludes animals where |
|---|---|
| `must_be_house_trained` | `house_trained` is `no` |
| `no_special_needs` | `has_special_needs` is true |
| `no_dogs_over_25kg` | `size` is `large` or `xlarge` |
| `must_be_good_with_children` | `good_with_children` is `no` (`older_only` is kept if the youngest child is 12+) |
| `must_be_good_with_cats` | `good_with_cats` is `no` |
| `must_be_good_with_dogs` | `good_with_dogs` is `no` |
| `no_puppies` | `age_band` is `puppy` |
| `must_be_sterilized` | `is_sterilized` is false |

Two exclusions are always applied regardless of stated deal-breakers, because they are safety rules rather than preferences:

- Children under 6 in the household exclude animals with `good_with_children = 'no'`.
- An existing cat excludes animals with `good_with_cats = 'no'`; an existing dog excludes `good_with_dogs = 'no'`.

The results page always reports how many animals were excluded and why, grouped by reason, with a control to relax a deal-breaker. Silent filtering is a dark pattern; the adopter should know their own filter cost them 12 animals.

## 4. Dimension scoring

Notation: `p` = adopter profile, `a` = animal (with behaviour profile). All functions return 0–100.

### Energy & activity — 0.20

```
energyGap = |p.activity_level − a.energy_level|          // both 1–5

base = { 0: 100, 1: 82, 2: 55, 3: 28, 4: 8 }[energyGap]

// asymmetric correction: an under-exercised high-energy animal is a
// much worse failure than an over-served calm one
if a.energy_level > p.activity_level:  base −= 10 × (a.energy_level − p.activity_level − 1)   // ≥0

// exercise-time reality check
if a.exercise_min_per_day is known:
    required = a.exercise_min_per_day
    offered  = { 1: 20, 2: 40, 3: 60, 4: 90, 5: 120 }[p.activity_level]
    if offered < required:  base −= min(25, (required − offered) / 4)

score = clamp(base, 0, 100)
```

### Space — 0.15

Matrix of housing type against animal size, then modifiers.

| | small | medium | large | xlarge |
|---|---|---|---|---|
| Apartment | 100 | 85 | 55 | 30 |
| House, no garden | 100 | 95 | 75 | 55 |
| House with garden | 95 | 100 | 100 | 95 |
| Farm/country | 90 | 100 | 100 | 100 |

```
score = matrix[p.housing_type][a.size]

if a.needs_garden == 'yes'  and not p.has_outdoor_space:  score −= 35
if a.needs_garden == 'preferred' and not p.has_outdoor_space:  score −= 12
if p.housing_size_sqm < 50 and a.size in ('large','xlarge'):   score −= 15
if a.species == 'cat':  score = max(score, 85)   // cats are far less space-constrained
score = clamp(score, 0, 100)
```

### Time alone — 0.15

```
if a.alone_tolerance_hours unknown:
    score = 65
else:
    surplus = a.alone_tolerance_hours − p.hours_alone_per_day
    score = surplus ≥ 2  → 100
            surplus ≥ 0  → 90
            surplus ≥ −1 → 65
            surplus ≥ −2 → 40
            surplus ≥ −4 → 15
            else         → 0

// puppies and kittens cannot be left long regardless of what the profile says
if a.age_band in ('puppy') and p.hours_alone_per_day > 4:  score = min(score, 30)
```

### Household — 0.15

Starts at 100; each incompatibility deducts.

```
score = 100
youngest = min(p.children_ages) if any children else null

if youngest is not null:
    if a.good_with_children == 'no':          → EXCLUDED (safety rule)
    if a.good_with_children == 'older_only':  score −= (youngest < 12 ? 45 : 5)
    if a.good_with_children == 'unknown':     score −= 25 + consideration
    if youngest < 6 and a.size in ('large','xlarge') and a.energy_level ≥ 4: score −= 15

if p.existing_dogs > 0:
    a.good_with_dogs == 'no'        → EXCLUDED (safety rule)
    a.good_with_dogs == 'selective' → score −= 20 + consideration
    a.good_with_dogs == 'unknown'   → score −= 25 + consideration

if p.existing_cats > 0:
    a.good_with_cats == 'no'        → EXCLUDED (safety rule)
    a.good_with_cats == 'selective' → score −= 20 + consideration
    a.good_with_cats == 'unknown'   → score −= 25 + consideration

if p.household_adults == 1 and a.energy_level ≥ 4 and a.training_needs ≥ 4:  score −= 10
score = clamp(score, 0, 100)
```

### Experience — 0.10

```
experienceValue = { first_time: 1, some: 2, experienced: 3 }[p.experience_level]
demand = a.training_needs                                     // 1–5
demandTier = demand ≤ 2 ? 1 : demand ≤ 3 ? 2 : 3

score = experienceValue ≥ demandTier ? 100
      : experienceValue == demandTier − 1 ? 60
      : 25

if a.suitable_for_first_time == 'yes' and p.experience_level == 'first_time':  score = min(100, score + 20)
if a.suitable_for_first_time == 'no'  and p.experience_level == 'first_time':  score = min(score, 30)
if a.age_band == 'puppy' and p.experience_level == 'first_time':               score −= 10
```

### Care capacity — 0.10

```
groomScore = p.grooming_capacity ≥ a.grooming_needs ? 100
           : 100 − 30 × (a.grooming_needs − p.grooming_capacity)

trainScore = p.training_capacity ≥ a.training_needs ? 100
           : 100 − 30 × (a.training_needs − p.training_capacity)

score = clamp(0.5 × groomScore + 0.5 × trainScore, 0, 100)
```

### Stated preferences — 0.10

```
sizeScore = p.preferred_sizes empty ? 100
          : a.size in p.preferred_sizes ? 100
          : adjacent size band ? 60 : 20

ageScore  = p.preferred_age_bands empty ? 100
          : a.age_band in p.preferred_age_bands ? 100
          : adjacent band ? 65 : 30

sexScore  = p.preferred_sex == 'any' ? 100 : a.sex == p.preferred_sex ? 100 : 70

score = 0.4 × sizeScore + 0.4 × ageScore + 0.2 × sexScore
```

Preferences are weighted lower than compatibility on purpose: someone who arrived certain they wanted a small young female should still see the calm four-year-old medium male who fits their life. Preference is deliberately soft, which is the whole argument for a matching product over a filter.

### Practical — 0.05

```
distScore = ratio = distance_km / p.search_radius_km
            ratio ≤ 0.33 → 100 · ≤ 0.66 → 85 · ≤ 1.0 → 70 · else → 40

feeScore  = no fee or no budget → 100
          : fee ≤ 20% of monthly budget → 100 · ≤ 50% → 80 · else → 50

needsScore = a.has_special_needs
             ? (p.experience_level == 'experienced' ? 85 : 55)
             : 100

score = 0.5 × distScore + 0.2 × feeScore + 0.3 × needsScore
```

### Final

```
raw = Σ (dimension_score × weight)
final = round(clamp(raw, 0, 100))
```

Bands used in the UI: **90–100** eccellente · **75–89** ottimo · **60–74** buono · **45–59** possibile · **<45** not shown by default.

## 5. Worked examples

### Marco — flat, no garden, out six hours, moderately active, first-time owner

Profile: `apartment`, 80 m², no outdoor space, 2 adults, no children, no pets, 6 h alone, activity 3, `first_time`, grooming 2, training 3, prefers `dog`, sizes `[small, medium]`, ages `[adult]`, deal-breaker `must_be_house_trained`, Milano, 50 km.

**Animal A — Luna**, medium meticcio, 38 months, energy 2, 60 min/day exercise, alone tolerance 6 h, good with children yes, dogs yes, cats unknown, house-trained yes, grooming 2, training 2, first-time yes, garden preferred, 12.4 km away, no fee.

| Dimension | Working | Score | × weight |
|---|---|---|---|
| Energy | gap 1 → 82; animal calmer than adopter so no penalty; offered 60 ≥ required 60 | 82 | 16.4 |
| Space | apartment × medium = 85; `needs_garden = preferred` without outdoor space −12 | 73 | 10.95 |
| Time alone | tolerance 6 − 6 h = surplus 0 → 90 | 90 | 13.5 |
| Household | no children, no pets, nothing deducted | 100 | 15.0 |
| Experience | first_time (1) vs demand tier 1 → 100; `suitable_for_first_time = yes` → capped 100 | 100 | 10.0 |
| Care | grooming 2 ≥ 2 → 100; training 3 ≥ 2 → 100 | 100 | 10.0 |
| Preferences | size medium ✓ 100, age adult ✓ 100, sex any 100 | 100 | 10.0 |
| Practical | 12.4/50 = 0.25 → 100; no fee 100; no special needs 100 | 100 | 5.0 |
| | | **Total** | **90.85 → 91** |

Reasons surfaced: `energy_matches`, `alone_ok`, `first_time_friendly`. Consideration: `cats_untested`, `prefers_garden`.

**Animal B — Thor**, large mixed breed, 18 months, energy 5, 120 min/day, alone tolerance 3 h, good with children unknown, house-trained partially, training needs 4, grooming 3, first-time no, needs garden yes, 8 km away.

Not excluded (`must_be_house_trained` excludes only `no`, and Thor is `partially`).

| Dimension | Working | Score | × weight |
|---|---|---|---|
| Energy | gap 2 → 55; animal higher by 2 → −10; offered 60 < required 120 → −25 (capped) | 20 | 4.0 |
| Space | apartment × large = 55; `needs_garden = yes` without space −35 | 20 | 3.0 |
| Time alone | 3 − 6 = −3 → 15 | 15 | 2.25 |
| Household | no children, no pets | 100 | 15.0 |
| Experience | first_time (1) vs tier 3 → 25; `suitable_for_first_time = no` → capped 30 → 25 | 25 | 2.5 |
| Care | grooming 2 vs 3 → 70; training 3 vs 4 → 70 | 70 | 7.0 |
| Preferences | size large ✗ adjacent → 60; age young adjacent → 65; sex 100 | 70 | 7.0 |
| Practical | 8/50 → 100; no fee; no special needs | 100 | 5.0 |
| | | **Total** | **45.75 → 46** |

46 lands in "possibile" and is not shown by default. Correct: Thor in Marco's flat is precisely the adoption that comes back in six weeks — and the dimension breakdown says exactly why, so if Marco insists on seeing him, the page can be honest instead of merely discouraging.

## 6. Explanations

Two layers, and the split matters.

**Layer 1 — deterministic reason keys.** The engine emits `reasons` (up to three highest positive contributions above 85) and `considerations` (any dimension below 55, plus every `unknown` field encountered). Both are i18n keys with pre-written Italian and English labels. **This layer always works** — no API key, no latency, no cost, no possibility of an invented claim.

**Layer 2 — the written paragraph.** Claude turns the reason keys into one warm paragraph. It receives only the structured facts, never free-rein access to the animal record:

```
System: Sei l'assistente di PetMatch AI. Scrivi UN paragrafo (max 60 parole)
che spiega perché questo animale è adatto a questa persona.
Usa SOLO i fatti forniti. Non inventare caratteristiche, storie o promesse.
Non garantire l'esito dell'adozione. Tono caldo, concreto, mai sdolcinato.
Se ci sono "considerazioni", nominane al massimo una, con onestà e senza allarmismo.
Rispondi in {locale}.

User: {"animal":{"name":"Luna","species":"cane","age_months":38,"size":"media"},
       "score":91,
       "reasons":["energy_matches","alone_ok","first_time_friendly"],
       "considerations":["cats_untested"],
       "profile_summary":{"housing":"appartamento","hours_alone":6,"activity":3,
                          "experience":"prima volta"}}
```

Generated paragraphs are cached in `match_results.explanation_it` / `explanation_en` and regenerated only when the score or reasons change. If Claude is unavailable, the UI renders the reason bullets and loses nothing structural.

**Rules for the generated text:** no health claims, no guarantee of adoption approval, no invented biography, never a negative characterisation of the animal, never a comparison to another animal. The `considerations` bullets always render as structured text regardless of what the paragraph says, so an honest caveat can never be smoothed away by prose.

## 7. Re-matching and notifications

```
animal published / behaviour updated
   └─▶ job: score against all active profiles with notify_new_matches = 1
          └─▶ upsert match_results
                 └─▶ score ≥ profile.min_notify_score (default 70)?
                        └─▶ queue for the next digest
```

- Digests are batched: at most one per profile per 48 hours, containing up to five new animals, sent at a civilised local hour.
- `notified_at` on `match_results` prevents the same animal appearing twice.
- Every digest carries a one-click unsubscribe that sets `notify_new_matches = 0` without requiring a login.
- Profiles inactive for 12 months are deactivated automatically and the adopter told why.
- Scoring is cheap (pure arithmetic over indexed rows) but explanation generation is not, so paragraphs are generated only for the animals that actually enter a digest.

## 8. Tuning and governance

Weights and matrices live in one versioned constants file, not scattered through the code:

```ts
export const MATCH_ENGINE_VERSION = 'match-1.0.0'
export const DIMENSION_WEIGHTS = {
  energy: 0.20, space: 0.15, timeAlone: 0.15, household: 0.15,
  experience: 0.10, careCapacity: 0.10, preferences: 0.10, practical: 0.05,
} as const   // must sum to 1.00 — asserted by a test
```

- Any change bumps `MATCH_ENGINE_VERSION` and invalidates cached results.
- A test asserts the weights sum to 1.00; another asserts every dimension returns within 0–100 across a fuzzed input space.
- The worked examples in §5 are encoded as regression tests, so a weight change that silently breaks them fails CI.
- Both worked examples and the full weight table are reproduced in the shelter-facing documentation, because shelters must be able to see and challenge the rules.

**The honest measure.** The only real validation is longitudinal: do high-scoring matches that become adoptions return less often than low-scoring ones? That requires 12 months of outcomes. Until then the weights are informed judgement drawn from shelter practice, and this document says so rather than implying a rigour we do not yet have. Once the data exists, §5's numbers get revisited — and the "learned matching" idea rejected at the outset becomes worth reopening, with real labels behind it.
