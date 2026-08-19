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

## Autonomous Stewardship Loop

This project runs a daily autonomous loop via `python3 src/steward.py`.
Scheduled at **6:00 AM PT** daily.

### The stewardship algorithm

The daily run is NOT about tackling known issues. It is about:

1. **Run pipeline** — ingest → sync → digest (parallel where possible)
2. **Snapshot metrics** — evidence count, source coverage, pipeline health
   (appended to `governance/metrics.json`)
3. **Assess health** — are things working? is the picture complete?
4. **Decide:**
   - **Healthy + complete picture:** Review recent loop entries, log "healthy,"
     sleep. Nothing to do.
   - **Healthy + incomplete picture:** Propose a NEW metric or signal that
     would close the biggest gap. Write the proposal. Sleep.
   - **Unhealthy:** Identify the issue, propose a fix. If the fix is within
     scope and boundaries, implement it. Write loop entry. Sleep.
   - **New evidence pattern:** If today's evidence suggests a new hypothesis
     or shifts an existing one, update `map/HYPOTHESES.md`. This is the
     primary creative output of each run.
5. **Write loop entry** to `governance/loop/YYYY-MM-DD.md`
6. **Commit + push**

### What the agent should NOT do on daily runs

- Do NOT work through a backlog of known issues
- Do NOT refactor or restructure existing code unless a metric is failing
- Do NOT add features unless the contract's success signals demand it
- DO propose new threads, hypotheses, and metrics
- DO let the system be quiet when it's healthy

### Using subagents

When operating autonomously, use the Agent tool to parallelize:

**Parallel ingestion** — one subagent per source:
- `python3 src/ingest_arxiv.py`
- `python3 src/ingest_github.py`
- `python3 src/ingest_podcasts.py`

**Sequential** (after ingestion): `python3 src/evidence_store.py` then
`python3 src/generate_digest.py`

**Deeper analysis subagents** for:
- Researching a specific signal in depth (web search)
- Querying the vector store for emerging clusters
- Drafting governance proposals when signals suggest scope changes
- Updating the hypothesis map with new evidence patterns

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

## Running the pipeline

```bash
python3 src/steward.py   # full stewardship loop (daily autonomous run)
bash run.sh              # just the pipeline (ingest → sync → digest)
bash run.sh ingest       # just ingestion
bash run.sh sync         # just vector store sync
bash run.sh digest       # just digest generation
```

## Architecture

```
src/
  steward.py           — autonomous stewardship loop (the daily cron target)
  ingest_arxiv.py      — arXiv cs.AI/CL/LG recent papers
  ingest_github.py     — GitHub trending AI/ML repos via search API
  ingest_podcasts.py   — Dwarkesh + Moonshot via RSS
  evidence_store.py    — ChromaDB vector store (sync + query)
  generate_digest.py   — Claude API synthesis → morning digest
```

Evidence items: `evidence/items/*.json` (schema in `evidence/.schema.md`)
Vector store: `evidence/chromadb/` (gitignored)
Digests: `digest/YYYY-MM-DD.md`
Metrics: `governance/metrics.json` (append-only snapshots)
Loop entries: `governance/loop/YYYY-MM-DD.md`

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
