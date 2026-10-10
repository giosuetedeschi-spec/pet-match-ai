# ML artifact validation and reconstruction decision

**Decision (2026-10-10): do not use the checked-in Cox artifact for predictions.** Keep the FastAPI mock explicitly labelled as a mock; Django matching may continue to calculate compatibility scores, but its prediction fields must stay empty until a replacement passes validation.

## Validation findings

- The serialized feature list in `trained-model/model_features.joblib` contains `duration_days` and `is_adopted`. Both describe the outcome being predicted and are unavailable at inference time. This is direct target leakage, so any reported performance from this artifact is invalid.
- The former Django inference input used a different feature schema (animal age, size, energy, adopter household attributes), which did not match the stored training columns. The previous loader could therefore return missing values or fail during inference; that legacy path has now been removed.
- `trained-model/features.py` also includes `duration_days` and `event_type` in its feature output. The training feature builder itself needs a leakage deny-list before it can be reused.
- There is no Austin intake/outcome training dataset, reproducible training command, artifact metadata, model card, or evaluation metrics in this checkout. The serialized artifact cannot be independently reproduced or evaluated here.
- Austin Animal Center outcomes (Texas, 2013–2018) are not local Italian shelter outcomes. Even a leakage-free model trained on Austin data would require local validation before its probabilities could be presented as calibrated for Italian shelters.

These findings fail the release gate. No accuracy or calibration claim is supported by the repository evidence.

## Reconstruction plan

1. **Acquire and identify source data.** Use the documented Austin public dataset only for an initial research baseline. Store raw files outside Git, record their SHA-256 hashes and source/version, and retain the existing no-personal-data constraint.
2. **Rebuild stays and labels.** Pair each intake with the next chronological outcome for the same animal ID; retain right-censored stays; map adoption, transfer, return-to-owner, death, and excluded outcomes separately. Record row counts and parse failures at every stage.
3. **Create one inference-safe feature function.** Use only fields available when a shelter publishes an animal. Keep outcome dates, event type, duration, adoption state, and post-intake changes on an explicit deny-list. Test that the same function builds training and serving features.
4. **Use time-based evaluation.** Preserve the documented 2017 temporal split. Compare against a constant baseline, species × age-band × size Kaplan–Meier baseline, and simple classifier/regressor comparators. Fit tuning and calibration on train/validation only; touch the test fold once.
5. **Apply the release gate.** Report concordance, integrated Brier score, time-dependent AUC, and bucket calibration, overall and by species, age band, and size. Reject segments whose calibration or ranking is poor. Save dataset hash, feature list, split boundaries, code commit, package versions, metrics, and model card with every artifact.
6. **Validate locally before operational use.** Collect consented, de-identified Italian shelter outcomes and repeat the temporal evaluation. Until that evidence exists, any Austin-trained result must be labelled exploratory and must not drive intake, transfer, euthanasia, or adopter decisions.

The detailed target schema and metric definitions remain in `docs/05-ml-spec.md`; this document records why the current artifact fails and the work needed to produce a reviewable replacement.
