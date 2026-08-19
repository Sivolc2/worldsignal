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

## Running the pipeline

### Quick run (full pipeline)
```bash
bash run.sh          # ingest all sources → sync to vector store → generate digest
bash run.sh ingest   # just ingestion
bash run.sh sync     # just vector store sync
bash run.sh digest   # just digest generation
```

### Using subagents for parallel work

When operating autonomously, use the Agent tool to parallelize:

**Parallel ingestion** — launch one subagent per source:
- Agent 1: `cd /home/ec2-user/worldsignal && python3 src/ingest_arxiv.py`
- Agent 2: `cd /home/ec2-user/worldsignal && python3 src/ingest_github.py`
- Agent 3: `cd /home/ec2-user/worldsignal && python3 src/ingest_podcasts.py`

**Sequential steps** (must wait for ingestion):
- After all ingestion agents complete: `python3 src/evidence_store.py`
- After sync: `python3 src/generate_digest.py`

**Deeper analysis** — use subagents for:
- Querying the vector store for clusters around a topic
- Researching a specific signal in depth (web search)
- Updating the hypothesis map based on new evidence patterns
- Drafting governance proposals when signals suggest scope changes

### Architecture

```
src/
  ingest_arxiv.py      — arXiv cs.AI/CL/LG recent papers
  ingest_github.py     — GitHub trending AI/ML repos via search API
  ingest_podcasts.py   — Dwarkesh + Moonshot via RSS
  evidence_store.py    — ChromaDB vector store (sync + query)
  generate_digest.py   — Claude API synthesis → morning digest
```

Evidence items are JSON files in `evidence/items/`. Schema in `evidence/.schema.md`.
Vector store persists in `evidence/chromadb/` (gitignored).
Digests output to `digest/YYYY-MM-DD.md`.

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
