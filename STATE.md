# PetMatch AI — Operational State

Updated: 2026-10-08
Base: `main` at `10ad3ff` (merge PR #23)
Branch: `chore/clean-modules-types-docs` at `26d8cc9`, pushed to `origin`
Working tree: clean at the time of this checkpoint
Merge status: direct push to protected `main` was rejected; a pull request and three required status checks are needed. The branch is published, but no PR had been opened when last checked because the local GitHub CLI authentication was invalid.

## Completed unit

PR #23 added the first public Next.js catalogue backed by published Prisma animal records.

- `/it/animali` shows available animals from active shelters.
- Search supports text, species, size, and pagination.
- The home page links to the Next.js catalogue and the Streamlit MVP.
- The operational roadmap records the current status in `ROADMAP-OPERATIVA.md`.

Commit `26d8cc9` also updated the project documentation, cleaned existing modules, added the Bun lockfile, and repaired the generated Prisma client setup. TypeScript typecheck and the Next.js production build passed; `python manage.py check` passed. A local web smoke check returned 200 for `/`; `/api/health` returned 503 because Docker Desktop and the database were unavailable.

## Current scope and constraints

- Django + Streamlit remains the MVP priority; Next.js + Prisma is a parallel release.
- Next.js shelter animal creation and publication are not implemented yet.
- Photo delivery to the Next.js release remains an open integration task; Django MVP media uses its local volume.
- The FastAPI ML service is scaffolded, but `/health` reports `model: not-configured`.
- Product requirements and intended architecture are in `docs/`; implementation status is in `ROADMAP-OPERATIVA.md`.

## Next planned unit

Implement the shelter flow to create and publish animals in the Next.js release, with validation. Keep photo integration separate until its storage and delivery path is decided.
