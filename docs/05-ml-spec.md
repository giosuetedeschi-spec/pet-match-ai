# 05 — Machine Learning Specification

Trained offline on the Austin Animal Center dataset, serving shelter staff only.

**The primary model is a competing-risks survival model.** An animal enters care and exits by one of several routes — adoption, transfer, return to owner, death — or is still there when we look. That is a time-to-event problem, and modelling it as one answers both product questions from a single fitted curve instead of from two models that can disagree. The reasoning, and the alternatives considered, are in [12 — Modelling Approaches](./12-modelling-approaches.md) §3.

| Model | Question | Type | Role |
|---|---|---|---|
| `adoption_survival` | How likely is adoption, and how soon? | Competing-risks survival | **Primary** |
| `adoption_classifier` | Will this animal be adopted? | Binary classification | Baseline comparator |
| `los_regressor` | How many days until an outcome? | Regression | Baseline comparator |

The two comparators are still built, because a primary model that cannot beat a simpler one is not worth its complexity — but they are evaluation instruments, not what the product serves.

Nothing here is ever shown to an adopter. It exists so that a shelter with limited hours can direct those hours at the animals that need them.

## 1. The dataset

[Austin Animal Center Shelter Intakes and Outcomes](https://www.kaggle.com/datasets/aaronschlegel/austin-animal-center-shelter-intakes-and-outcomes) — the largest no-kill municipal shelter in the United States, roughly October 2013 through early 2018, on the order of 80,000 intake records and a comparable number of outcomes, plus a pre-joined intakes-and-outcomes file.

**Intake fields:** `animal_id`, `name`, `datetime`, `found_location`, `intake_type`, `intake_condition`, `animal_type`, `sex_upon_intake`, `age_upon_intake`, `breed`, `color`.

**Outcome fields:** `animal_id`, `name`, `datetime`, `date_of_birth`, `outcome_type`, `outcome_subtype`, `animal_type`, `sex_upon_outcome`, `age_upon_outcome`, `breed`, `color`.

### Known quirks, and what we do about each

| Quirk | Reality | Handling |
|---|---|---|
| `animal_id` is not unique | The same animal returns — repeated strays, failed adoptions. Some ids appear five or more times. | Join intake to outcome **chronologically per animal**: each intake pairs with the first outcome after it. Never join on id alone; a naive merge produces a cartesian mess and silently inflates the dataset. |
| `age_upon_intake` is free text | `"2 years"`, `"3 months"`, `"4 weeks"`, `"1 day"`, occasional negatives | Parsed to days with a unit map; negatives and values above 25 years are nulled, not clipped. |
| `sex_upon_intake` encodes two things | `"Neutered Male"`, `"Spayed Female"`, `"Intact Male"`, `"Intact Female"`, `"Unknown"` | Split into `sex` and `sterilized_at_intake`; `"Unknown"` propagates as null on both, never as male. |
| `breed` is free text | ~2,000 distinct values, `"Mix"` suffixes, slash-separated crosses | Normalised, split on `/`, `is_mixed` flag, mapped to a size class and a coarse breed group; anything unmapped goes to `Other` rather than being dropped. |
| `color` is free text | `"Black/White"`, `"Brown Tabby"` | Primary colour + pattern extracted; long tail bucketed. |
| Austin-specific outcome types | `Rto-Adopt`, `Disposal`, `Missing`, `Public Assist` intake type, `Wildlife` | `Rto-Adopt` counts as adoption; `Disposal`/`Missing` rows are excluded from the classification target; `Wildlife` intakes are dropped entirely. |
| Non-target species | Birds, livestock, "Other" | Dropped. We serve dogs and cats. |
| Missing outcomes | Animals still in care at the export date | Right-censored. Excluded from the regression training set, and the exclusion is documented as a source of optimistic bias (see §8). |
| Duplicate rows | Present in small numbers | Deduplicated on `(animal_id, datetime, intake_type)`. |
| Timezone/format drift | Mixed formats across the export | Parsed with explicit formats; unparseable rows are counted and reported, never silently dropped. |

Every cleaning step writes a row count to the ETL report, so the pipeline can be audited: *N raw → N after species filter → N after join → N usable*.

## 2. ETL pipeline

```
data/raw/aac_intakes.csv, aac_outcomes.csv
   └─▶ 01_load.py       normalise column names, parse dates
   └─▶ 02_clean.py      species filter, age parsing, sex split, dedupe
   └─▶ 03_join.py       chronological intake↔outcome pairing → "stay" records
   └─▶ 04_features.py   feature engineering (§3)
   └─▶ 05_split.py      temporal split (§5)
   └─▶ data/processed/{train,val,test}.parquet + etl_report.json
```

The unit of analysis is a **stay**: one intake, its matching outcome, and everything derivable from the pair. An animal with three intakes contributes three stays.

## 3. Features

Only features the platform can actually supply for a live animal. A feature that exists in Austin's data but has no equivalent in a shelter's record is worthless in production, however predictive it looks in training.

| Feature | Type | Derivation | Available live? |
|---|---|---|---|
| `species` | categorical | `animal_type` | ✅ `animals.species` |
| `sex` | categorical | from `sex_upon_intake` | ✅ |
| `sterilized_at_intake` | boolean | from `sex_upon_intake` | ✅ |
| `age_months_at_intake` | numeric | parsed `age_upon_intake` | ✅ from `birth_date` + `intake_date` |
| `age_band` | categorical | puppy/kitten <6m, young 6–24m, adult 2–8y, senior >8y | ✅ derived |
| `is_mixed` | boolean | `"Mix"` or `/` in breed | ✅ |
| `breed_group` | categorical | mapped group (~20 levels) | ✅ from `breed_primary` |
| `size` | categorical | breed→size map; cats always small | ✅ explicit field |
| `coat_color_group` | categorical | primary colour bucketed (~12) | ✅ |
| `coat_pattern` | categorical | tabby, brindle, solid, bicolour… | ✅ derived |
| `intake_type` | categorical | direct | ✅ `intakes.intake_type` |
| `intake_condition` | categorical | direct | ✅ `intakes.intake_condition` |
| `intake_month` | cyclical | sin/cos encoded | ✅ |
| `intake_weekday` | cyclical | sin/cos encoded | ✅ |
| `intake_season` | categorical | meteorological | ✅ |
| `has_name` | boolean | name present and not a code | ✅ |
| `prior_intake_count` | numeric | count of earlier stays for the animal | ✅ from `intakes` |
| `is_black` | boolean | tests the "black dog syndrome" hypothesis explicitly | ✅ |

Three features exist **only** in production, because they describe how well the animal is presented rather than what it is:

| Feature | Why it is not in training | Handling |
|---|---|---|
| `photo_count` | Austin's export has no media | Excluded from the trained model; surfaced separately as a **rule-based** advisory in the triage list ("only one photo") and clearly not attributed to the model |
| `has_video` | idem | idem |
| `behavior_profile_completeness` | idem | idem |

This distinction is load-bearing. The advisory that says "add more photos" is a house rule from shelter practice, not a model output, and the UI labels the two differently. Inventing training values for them would be fabrication.

Preprocessing: one-hot for low-cardinality categoricals, ordinal for age bands, median imputation for numeric with an accompanying `*_was_missing` indicator, and a "missing" level for categoricals — because missingness is itself informative (an animal with no recorded breed usually arrived in a hurry).

## 4. Targets

### Primary — survival with competing risks

Each stay contributes three values rather than one label:

```
duration     days from intake to exit, or to the export date if still in care
event_type   adoption | transfer | return_to_owner | death | censored
is_censored  true when the animal was still in care at the export date
```

Event types map from Austin's outcome vocabulary:

```
adoption        Adoption, Rto-Adopt
transfer        Transfer
return_to_owner Return to Owner
death           Euthanasia, Died
censored        no outcome row at export       ← TRAINING DATA, not discarded
excluded        Disposal, Missing              ← genuinely uninformative
```

**Censored stays are training data.** An animal still waiting at day 400 tells us "not adopted within 400 days", which is strong signal about exactly the population the product exists to find. The previous formulation dropped these rows, which biased the estimates optimistic precisely where accuracy mattered most; see §8, limitation 2.

**Competing risks are modelled separately, not collapsed.** Earlier drafts treated transfer, reclaim and death as one "not adopted" negative class. That distorted reclaim-likely strays into "hard to adopt" animals, which is both wrong and operationally misleading. Cause-specific hazards are fitted per event type, and the adoption-specific cumulative incidence is what the product uses.

### What it produces

One fitted curve per animal — the cumulative incidence of adoption over time — from which every number the product needs is read directly:

```
P(adopted by 7 days)    →  bucket probability  lt_7
P(adopted by 30 days)   →  bucket probability  7_30
P(adopted by 90 days)   →  bucket probability  30_90
1 − P(adopted by 90d)   →  bucket probability  gt_90
curve plateau           →  overall adoption probability
curve crosses 0.5       →  median days to adoption
```

This matters for honesty, not just tidiness. The curve states something about a *population* — "at 90 days, 63% of animals like this one are still waiting" — which is what the model actually knows. A point estimate of 265 days implies a precision about *this individual animal* that no model trained on Austin data possesses. The UI leads with bucket probabilities for exactly this reason, and now they are the model's native output rather than a point estimate chopped into bins after the fact.

### Baseline comparators

Still built, still evaluated, because the primary model has to earn its complexity:

- **`adoption_classifier`** — binary on `event_type == 'adoption'` among uncensored stays. Base rate in Austin is roughly 40–45% across dogs and cats.
- **`los_regressor`** — `days_to_outcome` on uncensored stays, clipped at the 99th percentile, `log1p`-transformed.

If the survival model does not beat these on ranking quality (§5), it does not ship, and this section gets rewritten back. That comparison is a Phase 3 exit criterion in [08](./08-roadmap.md), not an optional extra.

## 5. Splitting and evaluation

**Temporal split, never random.** A random split leaks the future into the past: seasonal patterns, policy changes and population shifts all make an animal's neighbours in time far more informative than they would be at prediction time. Random cross-validation on this dataset produces flattering numbers that will not survive contact with a real shelter.

```
train:  intakes before 2017-01-01
val:    2017-01-01 … 2017-06-30
test:   2017-07-01 onwards
```

Hyperparameters are chosen on validation; test is touched once, at the end, per model version.

### Metrics

**Primary model — survival.**
- **Concordance index** (Harrell's, and Uno's for censoring-adjusted comparison) — does the model rank animals correctly by risk? This is the primary metric because relative ranking is the only claim the product makes.
- **Integrated Brier Score** — calibration across the whole time range rather than at one horizon.
- **Time-dependent AUC** at 30, 90 and 180 days — the horizons shelters actually plan around.
- **Bucket calibration** — predicted versus observed adoption rates in each of the four buckets. These are the numbers on screen, so they are the ones that must be true.

**Comparators.** Classification: ROC-AUC, PR-AUC, Brier, calibration curve. Regression: MAE and RMSE in days, plus MAE within each true bucket (an overall MAE of 27 days hides a model that is excellent on quick adoptions and useless on long stays).

**The head-to-head** is survival concordance against classifier ROC-AUC on the same temporal test split and the same animals, plus bucket calibration against bucket calibration. Both are ranking measures on the same population, which makes the comparison fair.

Calibration matters more than discrimination throughout: a number displayed to a human as a probability has to mean what it says. Where calibration is poor, isotonic regression is fitted on the validation fold — never on test.

**Breakdowns, always.** Every metric is reported separately by species, age band, and size. A model that is strong on kittens and worthless on senior large dogs is exactly the model that fails the animals the feature exists to help. If a segment's performance is materially worse than the aggregate, the UI suppresses predictions for that segment rather than showing an unreliable number.

### Baselines

Nothing ships without beating these:

1. **Constant** — always predict the base rate / median days.
2. **Kaplan–Meier stratified by species × age band × size** — the empirical lookup, done correctly with censoring accounted for.
3. **Cox proportional hazards** — the interpretable survival comparator, the analogue of the logistic regression named in the brief. Check the proportional-hazards assumption before trusting it.

### Algorithms

| Candidate | Library | Notes |
|---|---|---|
| **Random Survival Forest** | `scikit-survival` | The forest the brief names, in its time-to-event form. Non-parametric, captures interactions, no proportional-hazards assumption. ⚠️ Benchmark training time on 80k rows before committing — RSF is materially heavier than a plain forest and may need subsampling |
| **Gradient-boosted survival** | `scikit-survival`, or XGBoost `survival:aft` | Usually the strongest on tabular data; AFT gives an interpretable time scale |
| **Cox PH** | `lifelines` / `scikit-survival` | Interpretable baseline |

The simplest model within one standard error of the best wins. If Cox is within noise of the survival forest, we ship Cox and say so.

## 6. Training

Exploration starts in Google Colab and graduates to repository scripts; the notebook sequence, reproducibility checklist and graduation rules are in [11 — Training Workflow](./11-training-workflow.md).

```
services/ml/training/
├── etl/            01_load … 05_split
├── features.py     the single transform used by BOTH training and serving
├── train.py        --model {survival,adoption,los} --algo {rsf,gbs,cox,rf,logreg}
├── evaluate.py     metrics, breakdowns, calibration plot, model card
└── artifacts/      {model}-{version}/
                    ├── model.joblib
                    ├── preprocessor.joblib
                    ├── metadata.json
                    ├── model_card.md
                    └── metrics.json
```

`features.py` is imported by both the training scripts and the FastAPI service. Training/serving skew — the classic failure where a feature is computed one way offline and another way online — is prevented structurally, not by discipline, and a test asserts that the same input row produces identical features through both paths.

Random Survival Forest starting grid: `n_estimators` 200–600, `max_depth` {None, 10, 20}, `min_samples_leaf` {5, 15, 50}, `max_features` {sqrt, 0.3}. Larger leaves than a classification forest, because each leaf must estimate a survival curve rather than a class proportion, and thin leaves give noisy curves. Comparator forest grid: `n_estimators` 300–800, `max_depth` {None, 10, 20, 30}, `min_samples_leaf` {1, 5, 20}, `class_weight` {None, balanced}. Randomised search over the validation fold, fixed `random_state`, everything logged.

Reproducibility: a training run records the dataset checksum, the code commit, the full parameter grid, the chosen parameters, and the environment lockfile in `metadata.json`. A version that cannot be reproduced is not released.

## 7. Serving

The FastAPI service loads artifacts at startup and holds them in memory. Contract in [04 — API Contracts](./04-api-contracts.md) §4.

**Explanations.** `top_factors` comes from per-prediction feature attribution — SHAP values per prediction where the runtime cost allows, permutation importance at the model level otherwise, falling back to the forest's own importances. Each factor is mapped to a human sentence through a fixed dictionary (`age_months_at_intake` + negative direction → "Età superiore a 8 anni"). The model never writes the sentence; it selects one.

⚠️ **Attribution over a survival model needs validating early in Phase 3.** SHAP is less turnkey for survival forests than for classifiers, and `top_factors` is a hard API requirement ([04](./04-api-contracts.md) §4), not a nice-to-have — the triage list is useless without a reason attached to each row. If per-prediction attribution proves impractical, the acceptable fallbacks in order are: attribution against the risk score at a fixed horizon (90 days), then model-level permutation importance combined with the animal's own feature values. Discovering this in the final week of the phase is the failure mode to avoid.

**When predictions run:**
- on publication of an animal;
- when a field feeding a feature changes;
- nightly at 02:00 for every animal in care, so days-in-care stays current;
- on demand from the shelter dashboard, rate-limited.

Results are written to `predictions` (append-only), so we keep the history and can later ask whether the model was right.

## 8. Limitations — to be stated in the product, not buried here

This section is normative. Its content appears in the shelter UI, not only in this document.

1. **Different country, different everything.** Austin, Texas 2013–2018 is not Italy 2026. Adoption culture, breed mix (Austin's population is heavily pit-bull-type; Italy's is overwhelmingly *meticci*), legal framework (Italy's no-kill law and municipal *canile* system have no US equivalent), average length of stay, and seasonality all differ. Absolute numbers will be wrong. **Relative ranking — which of my animals will struggle most — is what the model is for, and it is the only claim we make.**

2. **Right-censoring is handled, not ignored — but only for the primary model.** Animals still in care at the export date are used as censored observations by the survival model, which is the main reason it is primary. The baseline comparators still drop them and remain optimistically biased as a result; that is one of the things the head-to-head is measuring. Note the residual limitation: censoring is handled correctly under the assumption that it is *uninformative* — that being still-in-care at the export date says nothing beyond the elapsed time. Since the export date is arbitrary rather than related to any animal's circumstances, that assumption is reasonable here, but it is an assumption.

3. **The model learns what happened, including the unfair parts.** If black dogs, senior animals, and bully breeds waited longer in Austin, the model reproduces that. Used correctly this is the point — those animals need more help, and surfacing them is the feature. Used incorrectly it becomes self-fulfilling. Hence: predictions are shelter-facing only, always paired with a suggested action, and never visible to adopters.

4. **Presentation quality is not modelled.** Photo count, video, and description quality plausibly dominate real adoption speed and are absent from the training data. Advisories about them are rules, not predictions, and are labelled separately.

5. **Prohibited uses.** These predictions must never inform euthanasia, intake refusal, transfer-out decisions, adopter rejection, or any pricing of an animal's life. This is written into the terms of service for shelter accounts, not merely recommended.

6. **Expiry.** A model older than 12 months without revalidation is marked stale in the UI, and the dashboard says so.

## 9. Retraining and the feedback loop

Austin data is the cold start. Every completed stay on the platform produces a real, local, Italian training row through the `intakes` and `outcomes` tables — which were deliberately shaped to mirror the training schema.

```
Phase A (launch)      Austin only.                      Model version 1.x
Phase B (~500 local outcomes)  Austin + local, sample-weighted toward local.  2.x
Phase C (~3,000 local outcomes) Local only; Austin retained as a validation
                       curiosity and to answer "did the transfer help?"       3.x
```

Retraining is quarterly and manual — reviewed by a human against the model card, promoted deliberately, never automatic. An automated retrain on a platform this size would be a way to silently ship a worse model.

**Monitoring in production:**
- feature drift, comparing live feature distributions to the training distribution;
- prediction drift, week over week;
- **realised accuracy** — for every animal that reaches an outcome, compare against what was predicted at intake and record the error. This is the only measurement that tells the truth, and it is reported on the admin dashboard.

**Shelter feedback.** Each prediction carries a "does this look right?" control. Disagreements are stored with the prediction and reviewed before each retraining round. Where staff consistently disagree with a segment of predictions, that segment is a candidate for suppression.

## 10. Definition of done for the ML phase

- [ ] ETL runs from raw CSVs to processed parquet with a row-count report at every step, including the censored count
- [ ] `features.py` is shared by notebooks, training and serving, with a test asserting identical output through all paths
- [ ] Censored stays reach the survival model as censored observations — asserted by a test, since silently dropping them is the exact failure this formulation exists to prevent
- [ ] The survival model beats all three baselines on concordance on the temporal test split
- [ ] The head-to-head against the classifier and regressor is recorded with its numbers, whichever way it goes
- [ ] Bucket calibration error under 0.05, or isotonic calibration applied
- [ ] Per-prediction attribution works well enough to populate `top_factors` for every row in the triage list
- [ ] Metrics reported by species, age band and size — and segments below the reliability bar are suppressed in the UI
- [ ] A model card is generated automatically and rendered verbatim in the shelter UI
- [ ] The FastAPI service serves both models with the documented contract and a working `/health`
- [ ] The web application degrades gracefully when the service is unavailable
- [ ] The limitations in §8 appear in the product, not just in this file
- [ ] Predictions are stored append-only, so realised accuracy can be measured later
