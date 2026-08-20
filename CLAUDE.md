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

### What the agent SHOULD do

- DO dispatch subagents to fix broken sources or implement missing ones
- DO dispatch subagents to deep-dive signals and build out the hypothesis map
- DO propose AND implement new metrics when the picture is incomplete
- DO propose new threads, hypotheses, and evidence dimensions
- DO let the system be quiet when it's genuinely healthy and complete

### What the agent should NOT do

- Do NOT work through an external backlog — the contract defines the work
- Do NOT refactor working code for style — only fix what's broken or missing
- Do NOT add features outside the contract's scope without a proposal
- Do NOT invent busywork when the system is healthy

### Subagent Authority

The steward agent MUST use the Agent tool to spin up subagents for work.
Subagents are how the steward gets things done — not just proposed.

**Authority model:**
- **Within scope + boundaries (CONTRACT.md §4, §5):** Dispatch a subagent to
  implement immediately. No proposal needed.
- **Scope-adjacent (plausible but not explicitly listed):** Dispatch a subagent
  to prototype, but note it in the loop entry for steward review.
- **Outside scope:** Write a proposal. Do NOT dispatch.

**When to dispatch subagents:**

1. **Parallel ingestion** — one subagent per source:
   - `python3 src/ingest_arxiv.py`
   - `python3 src/ingest_github.py`
   - `python3 src/ingest_podcasts.py`
   - `python3 src/ingest_alphasignal.py`

2. **Fix broken sources** — if a source is returning empty or erroring:
   - Dispatch a subagent to research the correct RSS/API endpoint (WebSearch)
   - Dispatch another to implement the fix in the ingestion script
   - This is clearly in scope — broken sources degrade the pipeline

3. **Deep-dive a signal** — if today's digest surfaces something important:
   - Dispatch a subagent with WebSearch/WebFetch to research it further
   - Have it write a detailed evidence item with the findings
   - This feeds the hypothesis map

4. **New hypothesis thread** — if evidence patterns suggest a new thread:
   - Dispatch a subagent to survey the landscape around that thread
   - Have it draft the hypothesis entry for `map/HYPOTHESES.md`
   - Have it gather 3-5 supporting/challenging evidence items

5. **Metric instrumentation** — if the picture is incomplete:
   - Dispatch a subagent to implement a new metric in `steward.py`
   - Or to add a new tracking dimension to `governance/metrics.json`

6. **New source integration** — if a source is approved in the contract but
   not yet implemented:
   - Dispatch a subagent to build the ingestion script
   - This is within scope — the contract lists approved sources

**Subagent patterns:**

Launch multiple subagents in parallel when their work is independent:
```
Agent 1: "Research working RSS feed for Dwarkesh podcast. Try..."
Agent 2: "Research Alpha Signal newsletter ingestion approach..."
Agent 3: "Deep-dive on [emerging signal] — search for related..."
```

Use sequential subagents when one depends on another:
```
Agent 1: "Fix podcast RSS feed..." → wait for result
Agent 2: "Run the fixed ingestion and verify..." (uses Agent 1's output)
```

**Sequential** pipeline steps (after ingestion): `python3 src/evidence_store.py`
then `python3 src/generate_digest.py`

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
  ingest_alphasignal.py — Alpha Signal AI news via RSS
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
