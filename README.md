# PetMatch AI

A web platform for responsible animal adoption in Italy, built for **both** sides of the process:

- **Adopters** — browse dogs and cats from shelters across the country, take a guided lifestyle quiz, get explained, ranked matches, ask an AI assistant anything about adoption and care, apply, and book a visit.
- **Shelters** — manage animal records (identity, behaviour, full medical history), see which animals are predicted to wait the longest and act before they do, review applications, schedule visits, and stop answering the same five questions by email.

## Status

> **This repository currently contains planning documentation only.**
> No application code, no scaffold. The design and technical decisions are settled and written down in [`docs/`](./docs); the build starts once those documents are approved.

## At a glance

| | |
|---|---|
| **Web app** | Next.js (TypeScript, App Router), Tailwind + shadcn/ui, Prisma |
| **Database** | MySQL |
| **ML service** | Python + FastAPI, scikit-learn (Random Forest baseline) |
| **AI assistant** | Claude API with retrieval over a curated knowledge base and live database tools |
| **Languages** | Italian and English, from day one |
| **Scope** | Dogs and cats, many shelters, one platform |
| **Local dev** | Docker Compose — MySQL, ML service, web app; no third-party credentials required |

## Machine learning

A **competing-risks survival model**, trained offline on the [Austin Animal Center Shelter Intakes and Outcomes](https://www.kaggle.com/datasets/aaronschlegel/austin-animal-center-shelter-intakes-and-outcomes) dataset (~80,000 real records). One fitted curve per animal answers both questions a shelter has:

1. **Adoption probability** — how likely is this animal to be adopted?
2. **Length of stay** — how likely is it to still be waiting at 7, 30, 90 days?

Survival analysis rather than a classifier plus a regressor because animals still in care have no outcome yet — and they are disproportionately the long stays this feature exists to find. A survival model treats them as training signal instead of discarding them, keeps adoption distinct from transfer and reclaim, and cannot contradict itself the way two separate models can.

The Kaggle data is a *training source only*. The live catalogue is always real animals entered by real shelters. The limits of transferring an Austin, Texas model to the Italian context are documented honestly in [`docs/05-ml-spec.md`](./docs/05-ml-spec.md), along with the decisions these predictions must never be used for.

Matching adopters to animals is deliberately **not** machine learning: it is a transparent weighted scoring system, so every match can explain itself. See [`docs/06-matching-algorithm.md`](./docs/06-matching-algorithm.md).

## Documentation

**Start at [`docs/INDEX.md`](./docs/INDEX.md)** — a routing table, every normative constant, and the hard rules, so you do not have to read 42,000 words to make a change. [`docs/README.md`](./docs/README.md) has the full contents and a suggested reading order.

## Licence

Not yet chosen. To be decided before the first public release.
