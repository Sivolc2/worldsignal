# CLAUDE.md — WorldSignal

This repo is governed by a contract at `governance/CONTRACT.md`.

## Prime Directive

Read the contract before doing anything. Your job is to serve the loop:
**Intent → Build → Measure → Refine.**

## Session workflow

1. Read `governance/CONTRACT.md`
2. Run `bash tests/check_contract.sh`
   - If blockers: help the steward resolve them
   - If operable: proceed to build within scope
3. Build toward the stated intent, within the boundaries
4. At end of session, write a loop entry to `governance/loop/YYYY-MM-DD.md`:
   - What you built
   - What signals moved (or didn't)
   - Proposed refinements to intent, scope, or signals
5. If the loop entry suggests a contract change, write a proposal to
   `governance/proposals/YYYY-MM-DD-title.md`

## What this project builds

Three layers, in order of priority:

1. **Daily digest** — filtered morning briefing from approved sources
   (see `sources/SOURCES.md`). Must leave the steward feeling oriented and
   inspired, never stressed. Output goes to `digest/`.
2. **Evidence point cloud** — every meaningful signal becomes a vectorized
   evidence item in `evidence/items/`. Clustered and queryable.
3. **Hypothesis map** — living document at `map/HYPOTHESES.md` tracking
   claims about where the world is heading, with evidence for/against.

The digest feeds the evidence store. The evidence store renders as the map.

## Key rules

- Never build outside the contract's scope without steward approval
- Treat success signals as hypotheses, not fixed targets — propose better ones
- Boundaries are hard constraints; everything else evolves
- The agent proposes, the steward decides
- **No engagement bait.** If content is designed to provoke, skip it.
- **Importance > popularity.** Seek the unpopular-but-significant.
- Evidence store is **append-only** — never delete, only reclassify.

## Tests

- `tests/check_contract.sh` — is the contract complete enough to operate?
- `tests/check_boundaries.sh` — does the repo state respect boundaries?
