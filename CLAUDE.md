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
5. If the loop entry suggests a contract change, write a proposal via
   `python3 -c "import sys; sys.path.insert(0,'src'); import proposals; proposals.propose(...)"`

## Configuration

All steward behavior is configured in **`governance/steward_config.json`**.
See `governance/CONFIG.md` for field-by-field documentation.

Key config sections:
- **cadence** — how often the steward wakes (default: 24h at 6am PT)
- **triggers.early_wake** — conditions that wake the steward early
- **monitoring** — health check thresholds
- **dispatch** — subagent dispatch rules and limits
- **hypotheses** — staleness thresholds, auto-weaken/retire
- **proposals** — lifecycle parameters, auto-expire
- **sources** — approved sources and their ingestion scripts

## Autonomous Stewardship Loop

This project runs a daily autonomous loop via `python3 src/steward.py`.
Scheduled at **6:00 AM PT** daily (configurable in steward_config.json).

### The stewardship algorithm (7 steps)

1. **Load config** from `governance/steward_config.json`
2. **Run pipeline** — ingest all configured sources → sync → digest
3. **Snapshot metrics** — evidence counts, source coverage, new evidence delta
4. **Run monitors** — pipeline health, source health, digest freshness, staleness
5. **Check hypotheses** — staleness alerts, auto-weaken/retire recommendations
6. **Check proposals** — pending decisions, approved-awaiting-implementation, expired
7. **Evaluate triggers + dispatch** — build dispatch manifest for subagents
8. **Write loop entry + commit + push**

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
- **Within scope + boundaries (CONTRACT.md §4, §5):** Dispatch immediately.
- **Scope-adjacent:** Dispatch to prototype, note in loop entry for review.
- **Outside scope:** Write a proposal via `proposals.propose()`. Do NOT dispatch.

**Dispatch manifest:** After each run, `governance/dispatch_manifest.json` contains
structured requests for the cloud agent to act on. Each request has:
- `action` — what type of work (must be in `config.dispatch.allowed_actions`)
- `priority` — high/medium/low
- `scope` — in_scope / scope_adjacent / out_of_scope
- `prompt` — suggested prompt for the subagent

The cloud agent reads this manifest and dispatches subagents accordingly.

**When to dispatch subagents:**

1. **Fix broken sources** — dispatch_manifest will have `fix_source` actions
2. **Build approved features** — `build_feature` actions from approved proposals
3. **Investigate stale hypotheses** — `investigate_thread` actions
4. **Deep-dive signals** — agent judgment based on digest content
5. **New hypothesis threads** — agent judgment from evidence patterns
6. **Metric instrumentation** — `implement_metric` when picture is incomplete

### Early Wake Triggers

The steward can wake before the next scheduled run when:
- Multiple sources fail in a single run (`source_failure_count`)
- Evidence store goes stale (`evidence_staleness_hours`)
- New evidence conflicts with an active hypothesis (`hypothesis_conflict`)
- An approved proposal awaits implementation (`proposal_approved`)

Thresholds are configurable in `steward_config.json → triggers.early_wake`.

## Hypothesis Store

Hypotheses are stored in `map/hypotheses.json` and rendered to `map/HYPOTHESES.md`.
All mutations go through `src/hypothesis_store.py` to keep them in sync.

```python
import hypothesis_store

hypothesis_store.add("Title", "One-sentence claim", implications="Why it matters")
hypothesis_store.add_evidence("H1", "for", "2026-08-20", "arxiv", "Summary", "https://...")
hypothesis_store.transition("H1", "strengthening")
hypothesis_store.check_staleness()  # returns alerts for stale hypotheses
hypothesis_store.list_active()      # all non-retired
```

Auto-lifecycle (configurable):
- **Auto-weaken** if no new evidence for N days (default: 30)
- **Auto-retire** if weakened for N days (default: 60)

## Proposal System

Proposals go through: proposed → approved/rejected → implemented/expired.

```python
import proposals

proposals.propose("Title", what="...", why="...", scope="in_scope", dispatch_action="fix_source")
proposals.decide("P001", "approved")
proposals.mark_implemented("P001")
proposals.pending()                        # awaiting decision
proposals.approved_awaiting_implementation()  # ready to dispatch
proposals.check_expired()                  # auto-expire after N days
```

Each proposal gets a markdown file in `governance/proposals/` for human review
and an entry in `governance/proposals/index.json`.

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
python3 src/steward.py        # full stewardship loop (daily autonomous run)
bash run.sh                   # just the pipeline (ingest → sync → digest)
bash run.sh ingest            # just ingestion
bash run.sh sync              # just vector store sync
bash run.sh digest            # just digest generation
python3 src/monitors.py       # standalone health check
python3 src/hypothesis_store.py          # list hypotheses + staleness
python3 src/hypothesis_store.py migrate  # one-time markdown → JSON migration
python3 src/proposals.py                 # proposal summary
python3 src/proposals.py pending         # list pending proposals
python3 src/proposals.py approved        # list approved awaiting implementation
```

## Architecture

```
governance/
  CONTRACT.md            — the governance contract (source of truth)
  steward_config.json    — all configurable steward params
  CONFIG.md              — config field documentation
  metrics.json           — append-only metric snapshots
  dispatch_manifest.json — subagent dispatch requests (written each run)
  loop/                  — daily loop entries
  proposals/             — proposal markdown files + index.json

src/
  steward.py             — autonomous stewardship loop (the daily cron target)
  monitors.py            — health checks, triggers, early wake, dispatch manifests
  hypothesis_store.py    — hypothesis CRUD (JSON store + markdown render)
  proposals.py           — proposal lifecycle management
  ingest_arxiv.py        — arXiv cs.AI/CL/LG recent papers
  ingest_github.py       — GitHub trending AI/ML repos via search API
  ingest_podcasts.py     — Dwarkesh + Moonshot via RSS
  ingest_alphasignal.py  — Alpha Signal AI news via RSS
  evidence_store.py      — ChromaDB vector store (sync + query)
  generate_digest.py     — Claude API synthesis → morning digest

map/
  hypotheses.json        — structured hypothesis store (backing data)
  HYPOTHESES.md          — rendered hypothesis map (human-readable)
```

Evidence items: `evidence/items/*.json` (schema in `evidence/.schema.md`)
Vector store: `evidence/chromadb/` (gitignored)
Digests: `digest/YYYY-MM-DD.md`

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
