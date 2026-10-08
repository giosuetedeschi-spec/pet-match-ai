# PetMatch AI — Operational State

Updated: 2026-10-08
Base: `main` at `10ad3ff` (merge PR #23)
Branch: `chore/clean-modules-types-docs`, matching implementation and completion work in progress
Working tree: matching digest, account carry-over, notification and animal-detail work is in progress
Merge status: direct push to protected `main` was rejected by GitHub (PR required, 3 status checks expected). The local GitHub CLI reports its keyring token as invalid; GitHub CLI API calls also fail through the configured local proxy.

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

Verification on 2026-10-08: Prisma schema validation, TypeScript typecheck, production build, Compose config, and automated scoring/digest tests passed. The test suite covers both documented examples (91 and 46), weight total, exclusions, unknown data, the 48-hour policy, and 10,000 animals (<300 ms). A three-person usability run and live MySQL/SMTP smoke test remain outstanding because Docker/MySQL and `DATABASE_URL` are unavailable here.

## Next planned unit

Next.js shelter flow to create and publish animals with validation. Photo integration remains a separate storage/delivery decision.
