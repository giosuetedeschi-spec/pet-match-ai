# PetMatch AI — Operational State

Updated: 2026-10-08
Base: `main` at `10ad3ff` (merge PR #23)
Branch: none; local `main` is synced with `origin/main`
Working tree: documentation updates pending review

## Completed unit

PR #23 added the first public Next.js catalogue backed by published Prisma animal records.

- `/it/animali` shows available animals from active shelters.
- Search supports text, species, size, and pagination.
- The home page links to the Next.js catalogue and the Streamlit MVP.
- The operational roadmap records the current status in `ROADMAP-OPERATIVA.md`.

## Current scope and constraints

- Django + Streamlit remains the MVP priority; Next.js + Prisma is a parallel release.
- Next.js shelter animal creation and publication are not implemented yet.
- Photo delivery to the Next.js release remains an open integration task; Django MVP media uses its local volume.
- The FastAPI ML service is scaffolded, but `/health` reports `model: not-configured`.
- Product requirements and intended architecture are in `docs/`; implementation status is in `ROADMAP-OPERATIVA.md`.

## Next planned unit

Implement the shelter flow to create and publish animals in the Next.js release, with validation. Keep photo integration separate until its storage and delivery path is decided.
