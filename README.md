# PetMatch AI

PetMatch AI is a platform in development for responsible dog and cat adoption in Italy. It serves adopters and shelters, with a public animal catalogue and tools for shelters to manage animals and adoption applications.

## Current status

The repository contains a working Django + Streamlit MVP and a parallel Next.js release under active development. The product described in [`docs/`](./docs) is the target specification; several features in it are still planned.

- **Django + Streamlit MVP:** shelter animal management and publication, public catalogue, basic municipality search, applications, and visit scheduling.
- **Next.js + Prisma:** Italian public catalogue at `/it/animali`; the adopter flow at `/it/abbinamento` saves an anonymous, resumable profile, ranks animals with explained compatibility scores, supports radius expansion and favorites, and can sort the catalogue by match. This matching release has not yet been live-verified against a running database.
- **ML service:** the FastAPI service currently reports `not-configured`; the documented forecasting model is not available as a live feature yet.

See [`ROADMAP-OPERATIVA.md`](./ROADMAP-OPERATIVA.md) for the work tracker and [`STATE.md`](./STATE.md) for the latest repository checkpoint.

## Product direction

The target product covers a bilingual catalogue, explained adopter-to-animal matches, a guided lifestyle quiz, applications and visit scheduling, shelter management, and shelter-facing forecasts to help identify animals that may wait longer for adoption. The full scope and its safeguards are specified in [`docs/INDEX.md`](./docs/INDEX.md).

The forecasting design uses shelter intake and outcome data for relative ranking. It must not drive adopter decisions or determine whether an animal is accepted, transferred, or euthanised. The data and model limitations are described in [`docs/05-ml-spec.md`](./docs/05-ml-spec.md).

## Technology in the repository

| Component | Current implementation |
|---|---|
| MVP | Django REST API + Streamlit |
| Parallel web release | Next.js, TypeScript, Prisma |
| Databases | MySQL; separate `petmatch_mvp` and `petmatch_web` databases |
| ML service | Python + FastAPI scaffold; model endpoint is not configured |
| Local services | Docker Compose, including MySQL and Mailpit |

## Documentation

Start with [`docs/INDEX.md`](./docs/INDEX.md) for the product specification and its safety rules. [`docs/README.md`](./docs/README.md) lists all 12 documents and their intended use. These documents define the target product and architecture; the operational roadmap records what is implemented now.

## Licence

Not yet chosen. To be decided before the first public release.
