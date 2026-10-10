# PetMatch AI — Operational State

Updated: 2026-10-10
Branch: `chore/clean-modules-types-docs` at `400bc88`, pushed to `origin`
Working tree: clean
Merge status: not merged.

CI on the branch passed on Ubuntu 24.04 (GitHub Actions run `38040076466`). It now runs on branch pushes, checks Django matching, typechecks and tests the web app during its image build, and runs ML service contract tests. The full Compose smoke test passed.

## Completed unit

PR #23 added the first public Next.js catalogue backed by published Prisma animal records.

- `/it/animali` shows available animals from active shelters.
- Search supports text, species, size, and pagination.
- The home page links to the Next.js catalogue and the Streamlit MVP.
- The operational roadmap records the current status in `ROADMAP-OPERATIVA.md`.

Commit `26d8cc9` also updated the project documentation, cleaned existing modules, added the Bun lockfile, and repaired the generated Prisma client setup. TypeScript typecheck and the Next.js production build passed; `python manage.py check` passed. A local web smoke check returned 200 for `/`; `/api/health` returned 503 because Docker Desktop and the database were unavailable.

## Current scope and constraints

- Django + Streamlit remains the MVP priority; Next.js + Prisma is a parallel release.
- Next.js shelter animal drafting, validated publication, and photo handling are implemented locally.
- Next.js Prisma uses MySQL, so the new flow was validated against the Compose MySQL service; SQLite cannot run this schema directly. Django MVP media continues to use its local volume.
- FastAPI exposes authenticated mock predictions and shelter triage stores append-only results. The Cox artifact is excluded because its feature list contains target leakage; no validated model is served.
- Product requirements and intended architecture are in `docs/`; implementation status is in `ROADMAP-OPERATIVA.md`.

## Shelter authoring unit (2026-10-09)

- Shelter staff can create and edit drafts, complete the animal and behavior profile, upload photos, and publish when required fields and one processed, accessible photo are ready. Access is restricted to shelter memberships. Onboarding and admin review are now implemented below.
- Photos are validated and normalized with Sharp, metadata is stripped, and WebP sizes are generated. Staff can edit alt text, choose a cover, reorder, and remove photos from the listing; removal is logical and retains the stored bytes. Compose stores them in a persistent local volume; production can use a private S3-compatible bucket.
- The MySQL migration applied successfully. Docker web service is healthy; `/api/health` returned 200, the shelter page redirects unauthenticated users (307), and the shelter API returns 401 without a session. Parser checks accepted a valid draft, rejected an invalid date and microchip, and publication validation accepted a complete profile.
- TypeScript typecheck, six shelter/photo unit tests, and production build passed. Tests cover draft and publish validation, invalid inputs, image derivatives, EXIF orientation and metadata stripping, and unsupported image data. Graphify index was updated. SQLite was not used for this Next.js flow because its Prisma datasource is MySQL.

## Current matching checkpoint

The Next.js matching scope now includes the resumable quiz, saved anonymous/account profiles, score breakdowns, favorites, browse integration, animal details, cache invalidation, optional Claude explanations with deterministic fallback, verified account carry-over, notifications, unsubscribe, and a scheduled digest worker.

Verification on 2026-10-08: Prisma schema validation, TypeScript typecheck, production build, Compose config, 10 automated scoring/digest tests, local page smoke checks, and all three required GitHub CI checks passed. The test suite covers both documented examples (91 and 46), weight total, exclusions, unknown data, the 48-hour policy, and 10,000 animals (<300 ms). GitHub CI started the full Compose stack and verified Next.js-to-MySQL connectivity. A three-person usability run and end-to-end email delivery/unsubscribe test remain outstanding.

## Next planned unit

Usability run with three people, end-to-end email delivery/unsubscribe validation, and ML artifact retraining/evaluation to replace the labelled mock.

## Shelter onboarding, ML integration, and translation (2026-10-09)

- Shelter registration validates legal/contact/location data, creates the user, pending shelter, and first membership atomically, then uses the existing email verification. Admins review verified contacts in a protected queue, approve, or reject with a reason. A CLI promotes only an existing verified account to `platform_admin`.
- FastAPI provides health, model-info, single and batch inference behind a bearer token. The existing Cox artifact was inspected and excluded because its feature list includes `duration_days` and `is_adopted`; a clearly labelled deterministic mock keeps the complete web-to-service flow usable. Staff triage reads latest predictions for active shelters only; new runs are appended to `animal_predictions`.
- Self-hosted LibreTranslate/Argos supplies automatic Italian/English text translation at display time. Original text remains in the database and is restored when switching back. Translation failure preserves the source content.
- TypeScript typecheck, the six existing shelter/photo tests, Python compile, Compose config, Next.js production build, Prisma client generation in Docker, and the MySQL migration passed. Live smoke checks returned 200 for web health and registration, 403/401 for unauthenticated admin/shelter APIs, 400 for invalid shelter registration, and a successful Italian-to-English translation. ML health and authorized prediction worked; model-info correctly returned 401 without a token. No test shelter account was created.
- The local Prisma CLI could not download its pinned engine through the sandbox proxy, but Docker build generated the client and the migration container applied the migration successfully.
