# PetMatch AI — Operational State

Updated: 2026-10-03
Base: `main` at `631ff394ea0b0aa507b3632682ee0e6c9e595e64`
Branch: `codex/phase1-next-public-catalog`
Unit: Add the first public Next.js catalogue backed by published Prisma animals.

## Previous unit

- PR #22 merged with all checks green at `631ff394ea0b0aa507b3632682ee0e6c9e595e64`.
- Feature branch deleted; local `main` was clean and synced before this unit.
- Bun 1.4.2 is installed at `C:\Users\gioma\.bun\bin\bun.exe`.
- `graphify-out/` is local, current, and ignored by Git.

## Scope and constraints

- Read public animal records from `petmatch_web`; include only available animals from active shelters.
- Support base filters for species, size and text search, with pagination.
- Keep Django + Streamlit MVP as the product priority; this is the parallel Next.js release.
- Do not change original product documentation under `docs/`.
- Do not add object storage; photo delivery is a separate integration decision.

## Progress

- [x] Confirmed current main and created a dedicated feature branch.
- [x] Implement `/it/animali` per the product specification, with public-status/shelter filters, text/species/size filters, pagination and responsive layout.
- [x] Link the home page to the catalogue and update the operational roadmap.
- [x] Docker build passes; temporary MySQL fixture confirmed card rendering, search and species filtering, then was removed.
- [x] Refresh Graphify incrementally; ignored output remains local.
- [x] Review final diff; original `docs/` files remain unchanged.
- [ ] Open PR, wait for green CI, merge with merge commit, delete branch.

## Next action

Open a PR for this reviewed unit, wait for green CI, merge with a merge commit, then delete the branch.
