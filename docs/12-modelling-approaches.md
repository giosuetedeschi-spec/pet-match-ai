# 12 — Modelling Approaches

What to train, why, and what was considered and rejected. The environment and mechanics are in [11 — Training Workflow](./11-training-workflow.md); the current specification is [05 — ML Specification](./05-ml-spec.md).

**Status: decided.** Competing-risks survival analysis is the primary model. [05](./05-ml-spec.md) has been updated to match; the classifier and regressor remain as baseline comparators. §3 records the reasoning.

---

## 1. First, a disambiguation

"Training a model" and "fine-tuning a model" are different activities aimed at different problems, and this product has three surfaces that get confused with each other:

| Surface | What it does | What it needs | Is it "trained"? |
|---|---|---|---|
| **Adoption forecasting** | Predicts probability and duration from ~18 structured fields | Supervised learning on tabular data | **Yes** — this is the only trained model in the product |
| **Adopter–animal matching** | Ranks animals for a person | A transparent weighted formula | **No** — deliberately not learned ([06](./06-matching-algorithm.md) §intro) |
| **AI assistant & explanations** | Answers questions, writes a paragraph | A general LLM with retrieval and structured facts | **No** — prompting + RAG, not fine-tuning |

So when the question is "should we train or fine-tune?", the honest answer is that they are not alternatives here. Fine-tuning is a technique for adapting a large pre-trained neural network — nearly always a language or vision model. The forecasting problem is 80,000 rows of tabular data with categorical and numeric columns. Those are different worlds, and §5 explains why bringing an LLM to the tabular problem makes it strictly worse.

The interesting question is not "train or fine-tune" but **"what is the right formulation of the forecasting problem?"** — and answering it changed the specification. §3.

---

## 2. The problem with the two-model formulation

Earlier drafts of [05](./05-ml-spec.md) specified two independent models:

1. `adoption_classifier` — binary: was the animal adopted?
2. `los_regressor` — regression: how many days until the outcome?

This works, it is simple, and it remains a reasonable baseline — which is why both models are still built as comparators. But it has three real weaknesses, two of which doc 05 already admitted:

**Weakness 1 — it throws away the most informative data.** Animals still in care at the export date have no outcome, so they are excluded from regression training ([05](./05-ml-spec.md) §8, limitation 2). Those are disproportionately the *long stays* — precisely the animals the entire feature exists to identify. We are excluding our best examples of the phenomenon we are trying to predict, and the documented consequence is a model biased optimistic exactly where accuracy matters most.

**Weakness 2 — it collapses distinct outcomes into "not adopted".** Transfer, return-to-owner, euthanasia and death are treated as a single negative class. [05](./05-ml-spec.md) §4 already flags the resulting distortion: a stray likely to be reclaimed gets marked "hard to adopt", which is wrong and operationally misleading.

**Weakness 3 — the two models can disagree.** Nothing constrains the classifier's 80% adoption probability to be coherent with the regressor's 300-day estimate. A shelter seeing both will notice.

All three have the same root cause: **the problem is a time-to-event problem, and it is being modelled as two static ones.**

---

## 3. Decision — competing-risks survival analysis (primary)

### The idea

An animal enters care and eventually exits by one of several routes: adoption, transfer, return to owner, death, or it is still there when we look. That is the textbook shape of a **competing-risks survival problem**, and the statistical machinery for it has existed for decades.

Modelling it that way fixes all three weaknesses at once:

| Weakness | How survival analysis addresses it |
|---|---|
| Censored animals discarded | **Right-censoring is native.** An animal still in care at day 400 contributes the information "not yet adopted after 400 days" — which is real, strong signal. Nothing is thrown away |
| Outcomes collapsed | **Competing risks are modelled separately.** Adoption, transfer and reclaim each get their own cumulative incidence. A reclaim-likely stray is no longer mislabelled as hard to adopt |
| Two models disagree | **One model, both answers.** Probability and duration are read off the same fitted curve, so they cannot contradict each other |

### What it produces

For each animal, a **cumulative incidence function** for adoption: the probability of having been adopted by time *t*. From one curve you get everything the product needs:

```
P(adopted by 7 days)   → 0.04    ┐
P(adopted by 30 days)  → 0.15    │ the bucket probabilities the UI
P(adopted by 90 days)  → 0.37    │ already shows — read directly
P(adopted by 365 days) → 0.68    ┘ off the curve

median time to adoption → the point where the curve crosses 0.5
overall adoption probability → the curve's plateau
```

This is a better fit for the interface we already designed. [05](./05-ml-spec.md) §4 says the bucket probabilities are what the UI actually shows, "because '63% chance of more than 90 days' is honest in a way that '265 days' is not". A survival model produces exactly those numbers as its native output, rather than as a post-hoc bucketing of a point estimate.

It is also more honest in a way that matters for this specific product. A curve says "at 90 days, 63% of animals like this one are still waiting" — a statement about a population, which is what the model actually knows. A point estimate of 265 days implies a precision about *this animal* that no model trained on Austin data possesses.

### Candidate algorithms

| Approach | Library | Notes |
|---|---|---|
| **Random Survival Forest** | `scikit-survival` | Non-parametric, captures interactions, no proportional-hazards assumption, closest in spirit to the Random Forest the brief names. **Chosen as primary.** ⚠️ Verify training time on 80k rows; RSF is heavier than a plain forest and may need subsampling |
| **Gradient-boosted survival** | `scikit-survival`, or XGBoost's `survival:aft` objective | Usually strongest on tabular; AFT gives interpretable time-scale coefficients |
| **Cox proportional hazards** | `lifelines`, `scikit-survival` | The interpretable comparator — the survival analogue of the logistic-regression baseline the brief asks for. Check the proportional-hazards assumption before trusting it |
| **Kaplan–Meier / Aalen–Johansen** | `lifelines` | Not a predictor — the descriptive baseline. Stratified by species × age band × size, this is the "empirical lookup" baseline of [05](./05-ml-spec.md) §5, done correctly with censoring |
| **Fine–Gray** | `lifelines` | Explicit competing-risks regression on the subdistribution hazard, if cause-specific models prove insufficient |

### Metrics

Survival models need their own evaluation, and the ones in [05](./05-ml-spec.md) §5 do not transfer directly:

- **Harrell's / Uno's concordance index** — does the model rank animals in the right order by risk? This is *precisely* the claim the product makes (relative ranking, not absolute numbers), so it is the primary metric.
- **Integrated Brier Score** — calibration across the whole time range, not at a single horizon.
- **Time-dependent AUC** at 30, 90 and 180 days — the horizons a shelter actually plans around.
- Everything still broken down by species, age band and size, per [05](./05-ml-spec.md) §5.

### Costs, honestly

- **Less familiar.** More concepts to hold, and a reviewer needs to understand censoring to read the evaluation.
- **Explanation is harder.** SHAP over a survival forest is possible but less turnkey. Since `top_factors` is a product requirement ([04](./04-api-contracts.md) §4), this needs validating early — falling back to the model's own permutation importances is acceptable but weaker.
- **Compute.** RSF is materially slower than a classifier. ⚠️ Benchmark before committing.
- **Ceremony risk.** If concordance is no better than the simple classifier's AUC, the added complexity is not earned. Test it, do not assume it.

### Build order

Survival is the target, but the comparators are built first — they are a day's work, they unblock the UI while the survival model is being tuned, and without them there is no way to know whether the primary model earned its complexity.

```
Phase 3a  Comparators: classifier + regressor on uncensored stays.
          Low-risk, unblocks the API and the dashboard against real numbers.
Phase 3b  PRIMARY: competing-risks survival model, same features, same
          temporal split, INCLUDING the censored rows.
          Validate per-prediction attribution here — it is an API requirement.
Phase 3c  Head to head: concordance vs AUC on ranking, bucket calibration
          vs bucket calibration. Survival ships unless it loses, in which
          case 05 §4 reverts and the reason is recorded.
```

**The failure condition is explicit.** If the survival model does not beat the comparators on ranking quality, or if per-prediction attribution cannot populate `top_factors`, it does not ship and doc 05 reverts to the two-model formulation. Complexity has to pay for itself, and "we chose the more sophisticated method" is not a result.

---

## 4. Techniques worth adopting regardless of formulation

These apply whether we ship the two-model version or the survival version.

**Calibration is not optional.** The number is shown to a human as a probability, so 0.7 must mean roughly seven in ten. Already required by [05](./05-ml-spec.md) §5; the mechanics are isotonic regression or Platt scaling fitted on the validation fold, never on test. A well-discriminating, badly-calibrated model is worse than useless here because it looks authoritative.

**Conformal prediction for honest intervals.** [04](./04-api-contracts.md) §4 promises a `prediction_interval`, and an interval invented from residual quantiles has no guarantee behind it. Conformal methods (`MAPIE`) give distribution-free coverage guarantees — "90% of the time the true value falls in this range" is a claim that survives scrutiny. Low cost, high credibility, and it fits a product whose central design commitment is honesty about uncertainty.

**CatBoost for high-cardinality categoricals.** `breed` has ~2,000 distinct values ([05](./05-ml-spec.md) §1). One-hot encoding it is a mess and target encoding by hand leaks. CatBoost handles this natively with ordered target statistics that are designed to avoid exactly that leakage. Worth a straight comparison against the manual breed-grouping approach, which is hand-built and lossy.

**Two-stage / hurdle framing** as a fallback if survival is rejected: first "does this animal leave quickly?", then "given it does not, how long?". Cheaper than survival, addresses the skew, does not address censoring.

**Quantile regression** as a cheaper route to intervals: train for the 10th, 50th and 90th percentile of days rather than the mean. LightGBM supports it directly. Less principled than conformal, much better than a point estimate.

**LLM-assisted feature extraction — the one genuinely good use of a language model in the pipeline.** Not as a predictor, but as a preprocessor for the free-text fields that are currently handled with regex and lookup tables:
- mapping ~2,000 free-text breed strings to size class and breed group (currently a hand-built map that sends anything unrecognised to `Other`)
- extracting structured temperament tags from shelter free-text notes
- normalising colour and pattern strings

This is a **one-off offline labelling job**, run once, output reviewed by a human, committed as a static mapping file. The LLM never runs at prediction time, so it adds no latency, no cost per prediction, and no dependency. It is a better use of a language model than any attempt to make it predict.

---

## 5. Why not fine-tune an LLM for the forecasting task

Taking the question seriously rather than dismissing it, because the answer is instructive.

**It could be made to work.** Serialise each animal into a sentence — *"Female mixed-breed dog, 3 years, medium, stray intake, normal condition, February"* — and fine-tune a language model to predict adoption or duration. This is a real technique and it does produce non-random predictions.

**It is nonetheless the wrong tool here, for six reasons:**

1. **Tree ensembles beat neural networks on tabular data of this size and shape.** This is a well-established empirical result — Grinsztajn et al. (2022), *"Why do tree-based models still outperform deep learning on typical tabular data?"*, is the canonical reference. The gap is largest exactly where we are: modest row counts, heterogeneous features, no natural spatial or sequential structure. ⚠️ Worth re-checking against current literature before treating as settled, but the finding has held up.

2. **Calibration would get worse, and calibration is the requirement.** A fine-tuned LLM emitting "31%" as text tokens has no probabilistic guarantee behind that number. Tree models with isotonic calibration have a well-understood path to trustworthy probabilities. Since the product shows probabilities to humans making resource decisions, this alone is close to disqualifying.

3. **Explanations get harder, and they are a product requirement.** `top_factors` needs per-feature attributions ([04](./04-api-contracts.md) §4). SHAP over a forest is standard and fast. Attribution over a fine-tuned transformer is an active research area, not a Tuesday afternoon.

4. **The features are already structured.** Fine-tuning would mean converting clean typed columns into prose so a text model can convert them back into an implicit structure. That is a lossy round trip performed for no gain.

5. **Cost and operational weight.** GPU for training, GPU or an API for inference, versus a ~10 MB joblib file that scores 500 animals in under a second on CPU. The nightly batch in [05](./05-ml-spec.md) §7 becomes an infrastructure problem instead of a cron job.

6. **80,000 rows is small for fine-tuning and ample for trees.** It sits in the region where a forest is comfortable and a fine-tuned transformer is likely to memorise.

**TabPFN deserves a mention** as the interesting middle ground: a transformer pre-trained on synthetic tabular tasks that performs in-context classification without task-specific training. Genuinely strong on small tabular problems and worth an afternoon in `05_train_adoption.ipynb` as a comparator. ⚠️ Verify current dataset-size limits and licence before considering it for production; it is a promising research direction rather than the safe default.

**Where fine-tuning *would* become the right answer:** if the strongest predictor turned out to be the shelter's free-text description — its warmth, specificity and length — rather than the animal's attributes. That is a genuinely plausible hypothesis, and it is testable cheaply: add text embeddings of the description as features to the tree model and see whether they help. If they dominate, revisit. Note that this hypothesis cannot be tested on Austin data at all, since it has no descriptions — it becomes answerable only once the platform has its own text, which is another argument for §6.

---

## 6. The transfer problem — where "fine-tuning" *is* the right word

There is one place in this project where fine-tuning, properly understood, is exactly the correct technique: **adapting an Austin-trained model to Italian data as it accumulates.**

[05](./05-ml-spec.md) §9 already stages this as retrain-from-scratch at 500 and 3,000 local outcomes. Domain-adaptation techniques do better than waiting for those thresholds:

| Technique | What it does | When |
|---|---|---|
| **Sample-weighted retraining** | Train on both datasets, weighting local rows far higher | From the first ~200 local outcomes. Simple, robust, the default |
| **Importance weighting** | Reweight Austin rows by how similar they are to the Italian distribution, so the transferable examples count for more | When local data is too thin to weight naively |
| **Warm-start / incremental boosting** | Continue training an Austin-fitted booster on local data — *this is fine-tuning, applied correctly* | Once local data is consistent enough not to whipsaw the model |
| **Hierarchical / mixed-effects** | Model a global effect plus per-region and per-shelter deviations | At 10+ shelters with meaningful volume — arguably the right long-term structure, since shelters differ from each other as much as countries do |
| **Fixed offset calibration** | Keep the Austin model for *ranking*, learn a local mapping to correct absolute values | Cheapest useful step, and it directly targets the documented "absolute numbers will be wrong" problem |

That last row is worth acting on early. The Austin caveat says only relative ranking is claimed. A calibration layer fitted on a few hundred local outcomes could make the absolute numbers defensible too, at a fraction of the cost of full retraining — and it degrades gracefully, because if the local data is too thin the layer simply stays near-identity.

---

## 7. Decision summary

| Question | Answer |
|---|---|
| Train or fine-tune, for forecasting? | **Train.** Gradient-boosted / random forest ensembles on tabular features. Fine-tuning an LLM is the wrong tool — §5 |
| Formulation? | **Competing-risks survival analysis, primary** — §3. Uses censored data, separates outcome types, yields probability and duration from one coherent model. Adopted into [05](./05-ml-spec.md) |
| Does that block Phase 3? | **No.** Comparators built first in 3a, survival in 3b, head-to-head in 3c — §3 build order |
| Primary algorithm? | Random Survival Forest, with gradient-boosted survival as the likely stronger contender and Cox as the interpretable comparator |
| Primary metric? | **Concordance index** — it measures ranking, which is the only claim the product makes |
| Intervals? | Conformal prediction, for coverage guarantees rather than invented ranges |
| High-cardinality breed? | Compare CatBoost's native handling against the hand-built grouping |
| Any LLM in the pipeline? | Yes — **offline, one-off, for feature extraction from free text.** Never at prediction time, never as the predictor |
| Adapting to Italy? | Sample-weighted retraining, plus a cheap calibration layer early — §6 |
| GPU needed? | **No**, at any point on the current trajectory |

## 8. Considered and rejected

| Idea | Why not |
|---|---|
| Fine-tuned LLM as the predictor | §5 — worse on every axis that matters here |
| Deep tabular networks (TabNet, FT-Transformer) | Consistently at or below gradient boosting at this scale, for far more complexity |
| Learned adopter–animal matching | No labelled pairs exist; would be trained on invented labels. Revisit at 12 months of outcomes — [06](./06-matching-algorithm.md) §8 |
| Computer vision on animal photos | Photo *quality* plausibly drives adoption, but training a quality scorer needs labels we do not have, and a model that judges how appealing an animal looks is an ethical hazard we should not build. Photo count stays a rule-based advisory |
| AutoML | Would produce an unexplainable model for a product whose central requirement is explanation |
| Per-shelter models | Not enough data per shelter for years. Hierarchical modelling is the right version of this instinct — §6 |
| Online / continuously updating learning | [05](./05-ml-spec.md) §9 is right: retraining is quarterly and human-reviewed. Automatic retraining at this scale is a way to silently ship a worse model |
| Reinforcement learning on adoption outcomes | Feedback loop measured in months, tiny sample, and it would optimise a system that decides about living animals. No |
| **`gigatoken`** ([marcelroed/gigatoken](https://github.com/marcelroed/gigatoken)) | A genuinely impressive Rust text tokenizer — ~1000× faster than HuggingFace `tokenizers`, ~24 GB/s. It accelerates **text tokenization for LLM pretraining and inference pipelines**, which is a bottleneck this project does not have: the forecasting model is tabular, with zero text tokenization anywhere in training. Our only LLM traffic is Claude API calls, where tokenization happens server-side at Anthropic. Even in the one place text could enter — the description-embedding experiment in §5 — we would be embedding a few thousand short strings, where the encoder forward pass dominates and tokenization is noise. Right tool, wrong problem |
