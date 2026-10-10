# PetMatch AI

PetMatch AI is a platform in development for responsible dog and cat adoption in Italy. It serves adopters and shelters, with a public animal catalogue and tools for shelters to manage animals and adoption applications.

## Current status

The Next.js portal supports shelter applications at `/it/rifugio/registrazione`, approval at `/it/admin/rifugi`, animal drafts, photo uploads, and validated publication. Shelter triage at `/it/rifugio/triage` is backed by a private FastAPI service. Italian and English display text uses self-hosted LibreTranslate; original database content remains unchanged.

The repository contains a working Django + Streamlit MVP and a parallel Next.js release under active development. The product described in [`docs/`](./docs) is the target specification; several features in it are still planned.

- **Django + Streamlit MVP:** shelter animal management and publication, public catalogue, basic municipality search, applications, and visit scheduling.
- **Next.js + Prisma:** public catalogue, adopter matching, shelter onboarding/review, and animal authoring with photo validation.
- **ML service:** FastAPI serves a clearly labelled deterministic mock. The saved Cox model is excluded because its feature list contains target leakage; Django matching leaves forecast fields empty until a replacement passes validation. See [`docs/13-ml-validation-and-reconstruction.md`](./docs/13-ml-validation-and-reconstruction.md).
- **Automatic translation:** LibreTranslate (Argos Translate engine) runs as a private Compose service for Italian/English UI and content display.

See [`ROADMAP-OPERATIVA.md`](./ROADMAP-OPERATIVA.md) for the work tracker and [`STATE.md`](./STATE.md) for the latest repository checkpoint.

## Run the Django + Streamlit demo

```powershell
docker compose up -d mysql mail django streamlit
```

Django runs migrations, imports municipality data, and idempotently seeds the demo catalogue at startup. Open Streamlit at <http://localhost:8501>; the API is at <http://localhost:8000>. The seed creates 6 approved shelters, 120 animals (100 available), and placeholder photos labelled as demo images. Demo shelter users have no usable password; create a local admin with `docker compose exec django python manage.py createsuperuser` if needed. To rerun the seed, use `docker compose exec django python manage.py seed_data`.

## Product direction

The target product covers a bilingual catalogue, explained adopter-to-animal matches, a guided lifestyle quiz, applications and visit scheduling, shelter management, and shelter-facing forecasts to help identify animals that may wait longer for adoption. The full scope and its safeguards are specified in [`docs/INDEX.md`](./docs/INDEX.md).

The forecasting design uses shelter intake and outcome data for relative ranking. It must not drive adopter decisions or determine whether an animal is accepted, transferred, or euthanised. The data and model limitations are described in [`docs/05-ml-spec.md`](./docs/05-ml-spec.md).

## Technology in the repository

| Component | Current implementation |
|---|---|
| MVP | Django REST API + Streamlit |
| Parallel web release | Next.js, TypeScript, Prisma |
| Databases | MySQL; separate `petmatch_mvp` and `petmatch_web` databases |
| ML service | Python + FastAPI, authenticated mock endpoints, append-only prediction history |
| Translation | Self-hosted LibreTranslate / Argos Translate |
| Local services | Docker Compose, including MySQL, Mailpit, ML, and translation |

## Documentation

Start with [`docs/INDEX.md`](./docs/INDEX.md) for the product specification and its safety rules. [`docs/README.md`](./docs/README.md) lists all 12 documents and their intended use. These documents define the target product and architecture; the operational roadmap records what is implemented now.

## Licence

No licence file is included at this stage.
