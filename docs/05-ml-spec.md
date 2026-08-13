# 05 — Machine Learning Specification

Two models, both trained offline on the Austin Animal Center dataset, both serving shelter staff only:

| Model | Question | Type | Target |
|---|---|---|---|
| `adoption_classifier` | Will this animal be adopted? | Binary classification | `outcome_type == 'Adoption'` |
| `los_regressor` | How long will it take? | Regression + bucketed classification | Days from intake to outcome |

Neither model is ever shown to an adopter. They exist so that a shelter with limited hours can direct those hours at the animals that need them.

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

### Classification — `adopted`

```
adopted = 1  if outcome_type in ('Adoption', 'Rto-Adopt')
adopted = 0  if outcome_type in ('Transfer', 'Return to Owner', 'Euthanasia', 'Died')
excluded     if outcome_type in ('Disposal', 'Missing') or outcome is null
```

Base rate in Austin is roughly 40–45% adoption across dogs and cats — imbalanced but not severely.

**`Return to Owner` is a negative, and that is a modelling choice with consequences.** From the shelter's operational view, a stray reclaimed by its owner was never an adoption candidate. But it is a *good* outcome, and a model trained this way will mark reclaim-likely animals as "hard to adopt". The at-risk list therefore excludes animals in the reclaim hold period, and the model card states this explicitly.

### Regression — `days_to_outcome`

`(outcome_date − intake_date).days`, clipped at the 99th percentile to stop a handful of multi-year stays from dominating the loss. Heavily right-skewed, so `log1p` transformation is fitted and predictions are inverse-transformed.

A bucketed classifier is trained on the same features against `lt_7 / 7_30 / 30_90 / gt_90`. The bucket probabilities are what the UI actually shows, because "63% chance of more than 90 days" is honest in a way that "265 days" is not.

## 5. Splitting and evaluation

**Temporal split, never random.** A random split leaks the future into the past: seasonal patterns, policy changes and population shifts all make an animal's neighbours in time far more informative than they would be at prediction time. Random cross-validation on this dataset produces flattering numbers that will not survive contact with a real shelter.

```
train:  intakes before 2017-01-01
val:    2017-01-01 … 2017-06-30
test:   2017-07-01 onwards
```

Hyperparameters are chosen on validation; test is touched once, at the end, per model version.

### Metrics

**Classification** — ROC-AUC, PR-AUC, Brier score, and a **calibration curve**. Calibration matters more than discrimination here: the number is displayed to a human as a probability, so "0.7 means roughly seven in ten" has to be true. If calibration is poor, isotonic regression is fitted on the validation fold.

**Regression** — MAE and RMSE in days, plus MAE within each true bucket (an overall MAE of 27 days hides a model that is excellent on quick adoptions and useless on long stays). Bucket classifier: macro F1 and a confusion matrix.

**Breakdowns, always.** Every metric is reported separately by species, age band, and size. A model that is strong on kittens and worthless on senior large dogs is exactly the model that fails the animals the feature exists to help. If a segment's performance is materially worse than the aggregate, the UI suppresses predictions for that segment rather than showing an unreliable number.

### Baselines

Nothing ships without beating these:

1. **Constant** — always predict the base rate / median days.
2. **Age-band × species lookup** — empirical rates from the training set.
3. **Logistic / linear regression** — the interpretable comparator named in the brief.

Then Random Forest (the specified model), and gradient boosting as a stretch comparison. The simplest model within one standard error of the best wins — if logistic regression is within noise of the forest, we ship logistic regression and say so.

## 6. Training

```
services/ml/training/
├── etl/            01_load … 05_split
├── features.py     the single transform used by BOTH training and serving
├── train.py        --model {adoption,los} --algo {rf,logreg,gbm}
├── evaluate.py     metrics, breakdowns, calibration plot, model card
└── artifacts/      {model}-{version}/
                    ├── model.joblib
                    ├── preprocessor.joblib
                    ├── metadata.json
                    ├── model_card.md
                    └── metrics.json
```

`features.py` is imported by both the training scripts and the FastAPI service. Training/serving skew — the classic failure where a feature is computed one way offline and another way online — is prevented structurally, not by discipline, and a test asserts that the same input row produces identical features through both paths.

Random Forest starting grid: `n_estimators` 300–800, `max_depth` {None, 10, 20, 30}, `min_samples_leaf` {1, 5, 20}, `max_features` {sqrt, 0.3}, `class_weight` {None, balanced}. Randomised search over the validation fold, fixed `random_state`, everything logged.

Reproducibility: a training run records the dataset checksum, the code commit, the full parameter grid, the chosen parameters, and the environment lockfile in `metadata.json`. A version that cannot be reproduced is not released.

## 7. Serving

The FastAPI service loads artifacts at startup and holds them in memory. Contract in [04 — API Contracts](./04-api-contracts.md) §4.

**Explanations.** `top_factors` comes from per-prediction feature attribution — permutation importance at the model level and SHAP values per prediction where the runtime cost allows, falling back to the forest's own feature importances. Each factor is mapped to a human sentence through a fixed dictionary (`age_months_at_intake` + negative direction → "Età superiore a 8 anni"). The model never writes the sentence; it selects one.

**When predictions run:**
- on publication of an animal;
- when a field feeding a feature changes;
- nightly at 02:00 for every animal in care, so days-in-care stays current;
- on demand from the shelter dashboard, rate-limited.

Results are written to `predictions` (append-only), so we keep the history and can later ask whether the model was right.

## 8. Limitations — to be stated in the product, not buried here

This section is normative. Its content appears in the shelter UI, not only in this document.

1. **Different country, different everything.** Austin, Texas 2013–2018 is not Italy 2026. Adoption culture, breed mix (Austin's population is heavily pit-bull-type; Italy's is overwhelmingly *meticci*), legal framework (Italy's no-kill law and municipal *canile* system have no US equivalent), average length of stay, and seasonality all differ. Absolute numbers will be wrong. **Relative ranking — which of my animals will struggle most — is what the model is for, and it is the only claim we make.**

2. **Right-censoring biases the length-of-stay model optimistic.** Animals still in care at the export date have no outcome and are excluded from training, and those are disproportionately the long stays. Real waits are likely longer than predicted, particularly at the top of the distribution.

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

- [ ] ETL runs from raw CSVs to processed parquet with a row-count report at every step
- [ ] `features.py` is shared by training and serving, with a test asserting identical output through both paths
- [ ] Both models beat all three baselines on the temporal test split
- [ ] Classification calibration error under 0.05, or isotonic calibration applied
- [ ] Metrics reported by species, age band and size — and segments below the reliability bar are suppressed in the UI
- [ ] A model card is generated automatically and rendered verbatim in the shelter UI
- [ ] The FastAPI service serves both models with the documented contract and a working `/health`
- [ ] The web application degrades gracefully when the service is unavailable
- [ ] The limitations in §8 appear in the product, not just in this file
- [ ] Predictions are stored append-only, so realised accuracy can be measured later
