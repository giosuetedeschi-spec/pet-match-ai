# PetMatch AI — Operational State

Updated: 2026-10-08
Base: `main` at `cb82556` (merge PR #24)
Branch: `chore/clean-modules-types-docs`, matching implementation merged to `main`
Working tree: post-merge checkpoint update
Merge status: PR #24 merged after all three required CI checks passed.

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

## Current matching checkpoint

The Next.js matching scope now includes the resumable quiz, saved anonymous/account profiles, score breakdowns, favorites, browse integration, animal details, cache invalidation, optional Claude explanations with deterministic fallback, verified account carry-over, notifications, unsubscribe, and a scheduled digest worker.

Verification on 2026-10-08: Prisma schema validation, TypeScript typecheck, production build, Compose config, 10 automated scoring/digest tests, local page smoke checks, and all three required GitHub CI checks passed. The test suite covers both documented examples (91 and 46), weight total, exclusions, unknown data, the 48-hour policy, and 10,000 animals (<300 ms). GitHub CI started the full Compose stack and verified Next.js-to-MySQL connectivity. A three-person usability run and end-to-end email delivery/unsubscribe test remain outstanding.

## Next planned unit

Next.js shelter flow to create and publish animals with validation. Photo integration remains a separate storage/delivery decision.
