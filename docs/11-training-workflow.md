# 11 — Training Workflow (Colab-first)

How the models in [05](./05-ml-spec.md) actually get built, starting in Google Colab and graduating to repository scripts. Which models to build, and the alternatives worth trying, is [12 — Modelling Approaches](./12-modelling-approaches.md).

## 1. Why Colab to start, and what it is not

**Good reasons to start there:**
- Zero environment setup. The Kaggle dataset is ~80k rows of CSV; the whole pipeline runs in RAM on a free CPU instance in minutes. No GPU is needed for tree models, so the free tier is genuinely sufficient.
- Exploration is iterative and visual. Distributions, missingness, calibration curves and confusion matrices want a notebook, not a script rerun.
- Shareable. A Colab link is the cheapest way to show someone the evidence behind a modelling decision.
- The Kaggle API works there, so the dataset never has to be manually downloaded and re-uploaded.

**What Colab is not, and must never become:**
- **Not the source of truth.** The moment a decision is made in a notebook, it moves into `services/ml/training/` as a script. Notebooks explore; scripts produce artifacts.
- **Not reproducible on its own.** Sessions are ephemeral, base images change under you, and "it worked yesterday" is not a claim a notebook can support.
- **Not a place for secrets.** No `kaggle.json` committed, no API keys in cells. Use Colab's secrets manager.
- **Not for anything touching personal data.** This is not a constraint we happen to satisfy — the training data is animal outcome data with no personal data in it at all ([09](./09-compliance-gdpr.md) §3), and that is what makes an external notebook environment acceptable in the first place. If that ever changes, this workflow stops.

**Practical limits of the free tier** ⚠️ (verify against current Colab terms, they change): sessions time out after roughly 12 hours and sooner when idle, disk is ephemeral, and RAM is around 12 GB. All comfortably above what this dataset needs, but they rule out long unattended runs — which is another reason hyperparameter search eventually belongs in a script on a machine you control.

## 2. Notebook sequence

Eight notebooks, each with one job, each ending by writing an artifact the next one reads. They live in `services/ml/notebooks/` and **are committed** — with outputs stripped — because the reasoning behind a modelling choice is worth keeping even after the code moves to scripts.

```
services/ml/notebooks/
├── 00_setup.ipynb          environment, Kaggle auth, data download, integrity check
├── 01_eda.ipynb            distributions, missingness, the quirks in 05 §1 verified
├── 02_etl.ipynb            cleaning + chronological intake↔outcome join → stays
├── 03_features.ipynb       feature engineering, leakage audit
├── 04_baselines.ipynb      the three baselines from 05 §5 — the bar to beat
├── 05_train_adoption.ipynb classification: RF, logistic, gradient boosting
├── 06_train_los.ipynb      length of stay: survival + regression (see doc 12)
└── 07_evaluate_export.ipynb metrics, calibration, model card, artifact export
```

### `00_setup`

Pins everything, authenticates, downloads, verifies.

```python
# Pinned — an unpinned notebook is a notebook that breaks silently
!pip install -q scikit-learn==1.5.2 pandas==2.2.3 numpy==2.1.3 \
                lightgbm==4.5.0 catboost==1.2.7 scikit-survival==0.23.1 \
                shap==0.46.0 joblib==1.4.2 pyarrow==18.1.0

import os, random, numpy as np
SEED = 42
random.seed(SEED); np.random.seed(SEED); os.environ["PYTHONHASHSEED"] = str(SEED)

# Kaggle credentials from Colab secrets — never a committed kaggle.json
from google.colab import userdata
os.environ["KAGGLE_USERNAME"] = userdata.get("KAGGLE_USERNAME")
os.environ["KAGGLE_KEY"]      = userdata.get("KAGGLE_KEY")

!kaggle datasets download -d aaronschlegel/austin-animal-center-shelter-intakes-and-outcomes \
    -p /content/data/raw --unzip

# Integrity check: record the checksum that identifies this exact dataset version
import hashlib, pathlib
for f in sorted(pathlib.Path("/content/data/raw").glob("*.csv")):
    print(f.name, hashlib.sha256(f.read_bytes()).hexdigest()[:16], f"{f.stat().st_size/1e6:.1f} MB")
```

The checksum matters. It goes into `metadata.json` for every model trained from it, so a model can always be traced to the exact data that produced it.

**Persistence.** Colab's disk vanishes with the session. Mount Drive for intermediate parquet files during a working session; treat Drive as a scratchpad, never as the store of record. Anything that matters gets committed to the repository or written to object storage.

### `01_eda`

Verifies every quirk claimed in [05](./05-ml-spec.md) §1 rather than trusting the document. Each one gets a cell that prints the evidence:

```python
# The quirk that breaks a naive pipeline: animal_id is NOT unique
dupes = intakes.animal_id.value_counts()
print(f"animals with >1 intake: {(dupes > 1).sum():,} of {dupes.size:,}")
print(f"max intakes for one animal: {dupes.max()}")
# A naive merge on animal_id alone inflates the dataset — demonstrate it:
naive = intakes.merge(outcomes, on="animal_id")
print(f"naive merge rows: {len(naive):,}  vs  intake rows: {len(intakes):,}")
```

Also: age-string parse failure rate, `sex_upon_intake` value counts, breed cardinality, outcome type distribution, the share of intakes with no outcome (the right-censored population — size it here, because [12](./12-modelling-approaches.md) turns it from a problem into training data), and adoption rate by species, age band and size.

**Output:** `eda_findings.md` — a written summary that becomes the factual basis for `05 §1` staying accurate.

### `02_etl`

The chronological join, implemented once and correctly:

```python
def build_stays(intakes: pd.DataFrame, outcomes: pd.DataFrame) -> pd.DataFrame:
    """Pair each intake with the first outcome that follows it, per animal.
    Never merge on animal_id alone — see 01_eda for what that does."""
    iv = intakes.sort_values(["animal_id", "intake_datetime"])
    ov = outcomes.sort_values(["animal_id", "outcome_datetime"])
    stays = pd.merge_asof(
        iv, ov,
        left_on="intake_datetime", right_on="outcome_datetime",
        by="animal_id", direction="forward", allow_exact_matches=False,
    )
    stays["days_to_outcome"] = (
        stays.outcome_datetime - stays.intake_datetime
    ).dt.total_seconds() / 86400
    stays["is_censored"] = stays.outcome_datetime.isna()   # still in care at export
    return stays
```

`is_censored` is the column that makes doc 12's approach possible. Do not drop those rows here.

Every step appends to a row-count report:

```python
report = {"raw_intakes": len(intakes_raw), "after_species_filter": len(intakes),
          "after_dedupe": len(intakes_dd), "stays_built": len(stays),
          "stays_with_outcome": int((~stays.is_censored).sum()),
          "stays_censored": int(stays.is_censored.sum())}
```

That dictionary is the ETL report referenced in [05](./05-ml-spec.md) §2. It is written to `etl_report.json` and is the first thing to check when a model behaves oddly.

### `03_features`

Implements the feature table in [05](./05-ml-spec.md) §3. Two rules enforced here:

1. **Only features the platform can supply at prediction time.** `photo_count` and friends are excluded from the model and handled as rule-based advisories.
2. **Leakage audit.** Nothing derived from the outcome may enter the features. `age_upon_outcome`, `outcome_subtype`, `sex_upon_outcome` are all traps — the last one is subtle, because sterilisation often happens *during* the stay as part of the adoption process, so `sex_upon_outcome` partly encodes the answer. The notebook prints the feature list and asserts against a deny-list.

```python
LEAKY = {"age_upon_outcome", "outcome_type", "outcome_subtype",
         "sex_upon_outcome", "outcome_datetime", "days_to_outcome", "is_censored"}
assert not (set(X.columns) & LEAKY), f"leakage: {set(X.columns) & LEAKY}"
```

### `04_baselines`

The three baselines from [05](./05-ml-spec.md) §5, computed on the temporal test split before any model is trained. Doing this first sets an honest bar and prevents the common failure of celebrating a 0.78 AUC that a lookup table also achieves.

### `05_train_adoption` / `06_train_los`

Model families, hyperparameter search on the validation fold, and the comparison table. Details and the recommended approaches are in [12](./12-modelling-approaches.md).

### `07_evaluate_export`

Test split touched once. Produces:
- metrics overall **and broken down by species, age band, size** — the breakdown is what determines which segments are shown in the UI at all
- calibration curve and Brier score; isotonic calibration fitted on validation if needed
- SHAP summary, and the per-prediction attribution the `top_factors` API field depends on
- `model_card.md`, generated not hand-written
- artifacts exported in the layout [05](./05-ml-spec.md) §6 expects

```python
import joblib, json
out = pathlib.Path(f"/content/artifacts/{MODEL_NAME}-{VERSION}")
out.mkdir(parents=True, exist_ok=True)
joblib.dump(pipeline, out / "model.joblib")
(out / "metadata.json").write_text(json.dumps({
    "model_name": MODEL_NAME, "version": VERSION, "algorithm": ALGO,
    "trained_at": datetime.now(timezone.utc).isoformat(),
    "dataset_sha256": DATA_CHECKSUM, "code_commit": GIT_SHA,
    "seed": SEED, "features": list(X.columns),
    "train_rows": len(X_train), "params": best_params,
    "library_versions": {"scikit-learn": sklearn.__version__, ...},
}, indent=2))
```

Artifacts are **not** committed to git — they are binary, they are large, and they change often. They go to object storage under `models/{name}/{version}/`, and the service loads them by version at startup. `metadata.json` and `model_card.md` *are* committed, because they are the human record.

## 3. Graduating out of Colab

Notebooks are for deciding. Scripts are for producing. The transition is not optional and should happen at the end of Phase 3, not "eventually".

| Stage | Where | Produces | Trigger to move on |
|---|---|---|---|
| **Explore** | Colab | Findings, decisions, a chosen approach | The approach stops changing |
| **Consolidate** | `services/ml/training/*.py` | Reproducible artifacts from a single command | First model served in the app |
| **Automate** | CI job, manually triggered | Versioned artifacts + model card, published to storage | Second retraining round, or first local-data retrain |

The consolidated form is one command:

```bash
python -m training.run --model adoption --algo rf --version 1.0.0 --seed 42
```

Which must: read raw data from a fixed location, run the identical ETL and feature code the service imports, train, evaluate, write artifacts and the model card, and refuse to complete if the metadata is incomplete.

**The rule that keeps this honest:** `features.py` is imported by the notebooks, the training scripts and the FastAPI service. The notebook does not have its own copy of the feature logic. This is the same structural guarantee against training/serving skew described in [05](./05-ml-spec.md) §6, and it is why the notebooks live inside `services/ml/` rather than in a separate analysis repo.

## 4. Reproducibility checklist

Every notebook run that informs a decision must record all of these, and `07_evaluate_export` refuses to write artifacts if any are missing:

- [ ] Dataset SHA-256 and row count
- [ ] Pinned library versions
- [ ] Random seed, set for Python, NumPy and the estimator
- [ ] Git commit of the feature code
- [ ] Split boundaries as explicit dates, never fractions
- [ ] Full hyperparameter grid searched, and the chosen values
- [ ] Metrics on validation and, once only, on test
- [ ] Per-segment breakdowns

A model version that cannot be reproduced from that record is not released.

## 5. Costs and alternatives

Free Colab is sufficient for this project's entire first year: tree models on 80k rows train in seconds to low minutes on CPU. ⚠️ Colab Pro (~€10/month) buys longer sessions and more RAM, and is worth it only if hyperparameter search becomes tedious — not for the models themselves.

If Colab proves annoying, the alternatives in order of sensibleness:
1. **Local Jupyter in the project's Docker image** — same environment as production, no upload dance, fully offline. The natural destination once the pipeline stabilises.
2. **Kaggle Notebooks** — the dataset is already there, so no download step at all, and sessions are comparably generous. Good for the first exploratory pass.
3. Managed notebook services (SageMaker, Vertex) — real cost, real setup, and no benefit at this data size. Not justified.

There is no point in this project's trajectory where model training requires a GPU. If a proposal implies one, that is a signal the approach has drifted away from what the problem needs — see [12](./12-modelling-approaches.md) §5.
