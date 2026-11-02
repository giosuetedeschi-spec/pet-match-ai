# PetMatch AI

PetMatch AI is a platform in development for responsible dog and cat adoption in Italy. It serves adopters and shelters, with a public animal catalogue and tools for shelters to manage animals and adoption applications.

## Current status

The Next.js portal supports shelter applications at `/it/rifugio/registrazione`, approval at `/it/admin/rifugi`, animal drafts, photo uploads, and validated publication. Shelter triage at `/it/rifugio/triage` is backed by a private FastAPI service. Italian and English display text uses self-hosted LibreTranslate; original database content remains unchanged.

The repository contains a working Django + Streamlit MVP and a parallel Next.js release under active development. The product described in [`docs/`](./docs) is the target specification; several features in it are still planned.

- **Django + Streamlit MVP:** shelter animal management and publication, public catalogue, basic municipality search, applications, and visit scheduling.
- **Next.js + Prisma:** public catalogue, adopter matching, shelter onboarding/review, and animal authoring with photo validation.
- **ML service:** FastAPI serves two shelter-only demo models: an Austin adoption outcome/conditional stay estimate and a Kaggle synthetic dog return-risk estimate for an adopter–dog pair. The public compatibility ranking remains rule-based. Both models are explicitly experimental; see [`docs/14-mvp-ml-demo.md`](./docs/14-mvp-ml-demo.md).
- **Assistant:** shared private FastAPI RAG demo for web and Streamlit, with bilingual cited guidance, relevance-based abstention, a read-only public animal lookup, and a no-credentials retrieval fallback. See [`docs/15-rag-assistant.md`](./docs/15-rag-assistant.md).
- **Automatic translation:** LibreTranslate (Argos Translate engine) runs as a private Compose service for Italian/English UI and content display.

See [`ROADMAP-OPERATIVA.md`](./ROADMAP-OPERATIVA.md) for the work tracker and [`STATE.md`](./STATE.md) for the latest repository checkpoint.

## Run the Django + Streamlit demo

```powershell
docker compose up -d --build mysql mail ml assistant django streamlit
```

Django runs migrations, imports municipality data, and idempotently seeds the demo catalogue at startup. Open Streamlit at <http://localhost:8501>; the API is at <http://localhost:8000>. The seed creates 6 approved shelters, 120 animals (100 available), and placeholder photos labelled as demo images. For the local shelter login, use username `rifugio_esperanza` and password `DemoRifugio123!`. The Austin and Kaggle dog training CSVs are included under `training-data/`, so a clean clone can build the ML image without Kaggle credentials or a manual download. Source links and license attribution are in [`docs/14-mvp-ml-demo.md`](./docs/14-mvp-ml-demo.md). The Compatibilità tab remains rule-based and does not show internal predictions to adopters. See the model caveats and training metrics in that document. To rerun the seed, use `docker compose exec django python manage.py seed_data`.

## Product direction

The target product covers a bilingual catalogue, explained adopter-to-animal matches, a guided lifestyle quiz, applications and visit scheduling, shelter management, and shelter-facing forecasts to help identify animals that may wait longer for adoption. The full scope and its safeguards are specified in [`docs/INDEX.md`](./docs/INDEX.md).

The forecasting design uses shelter intake and outcome data for relative ranking. It must not drive adopter decisions or determine whether an animal is accepted, transferred, or euthanised. The data and model limitations are described in [`docs/05-ml-spec.md`](./docs/05-ml-spec.md).

## Technology in the repository

| Component | Current implementation |
|---|---|
| MVP | Django REST API + Streamlit |
| Parallel web release | Next.js, TypeScript, Prisma |
| Databases | MySQL; separate `petmatch_mvp` and `petmatch_web` databases |
| ML service | Python + FastAPI, bearer-authenticated demo models, shelter-only Streamlit presentation |
| Translation | Self-hosted LibreTranslate / Argos Translate |
| Local services | Docker Compose, including separate MySQL databases, Mailpit, ML, RAG assistant, and translation |

## Documentation

Start with [`docs/INDEX.md`](./docs/INDEX.md) for the product specification and its safety rules. [`docs/README.md`](./docs/README.md) lists the project documents and their intended use. These documents define the target product and architecture; the operational roadmap records what is implemented now.

## Licence

No licence file is included at this stage.
