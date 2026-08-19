# Governance Contract

> This is a living contract. It defines a cybernetic loop: the steward states
> intent, the agent builds toward it, outcomes are measured, and both parties
> refine the intent together. The contract evolves as understanding deepens.

---

## 1. Identity

| Field | Value |
|-------|-------|
| **Project name** | WorldSignal |
| **Owner / steward** | Clovis (clovisvt@gmail.com) |
| **Created** | 2026-08-19 |
| **Contract version** | `0.1.0` |

---

## 2. Intent

The steward's current understanding of what this project should become.

**Vision:** Turn the ambient uncertainty of the AI/tech landscape into a felt
sense of where things are flowing — making the world feel less like shadows
moving in the dark and more like a shared progression toward the future.

**Current hypothesis:** A daily filtered digest that feeds a growing evidence
point cloud (vectorized, clustered) which renders as a living hypothesis map
will provide the steward with morning orientation/inspiration and a durable,
shareable model of where the world is heading.

**Open questions the agent should help answer:**
- What clustering dimensions best capture "where energy is flowing" in AI?
- What's the right fidelity for v0.1 of the hypothesis map — markdown? visual?
- How should the evidence point cloud be structured for later querying?
- What does "inspiring" mean operationally — can we detect it in content?
- How to filter for importance vs. popularity (unpopular-but-significant signal)?

---

## 3. The Loop

The governance cycle. Each pass through the loop refines the intent.

```
  ┌─────────────────────────────────────────────┐
  │                                             │
  │   INTENT ──► BUILD ──► MEASURE ──► REFINE   │
  │     ▲                                │      │
  │     └────────────────────────────────┘      │
  │                                             │
  └─────────────────────────────────────────────┘
```

1. **Intent** — Steward writes/updates section 2
2. **Build** — Agent works within Scope (section 4) and Boundaries (section 5)
3. **Measure** — Agent evaluates outcomes against Success Signals (section 6)
4. **Refine** — Agent proposes intent updates in `governance/loop/` with evidence

### Loop cadence

| Trigger | Action |
|---------|--------|
| Start of session | Read contract, run loop check |
| End of session | Write loop entry to `governance/loop/YYYY-MM-DD.md` |
| Signal changes | Propose contract amendment |

---

## 4. Scope

What the agent is allowed to build and do right now.

- **In scope:**
  - Daily morning digest (filtered, quiet, no engagement bait, leaves steward
    feeling oriented and inspired — not stressed or overwhelmed)
  - Evidence point cloud with vector embeddings and cluster groupings
  - Hypothesis map (living document, growing over time, shareable)
  - Source ingestion from: arXiv, GitHub trending, Alpha Signal newsletter,
    Dwarkesh Podcast, Moonshot Podcast
  - Feedback mechanism for steward to react to digest items
  - Noon cadence (optional, deeper state-of-world / podcast summaries)

- **Out of scope:**
  - Real-time monitoring / push notifications
  - Social media posting or auto-sharing
  - Anything requiring paid API subscriptions (start free/local)
  - Building for other users (single-steward tool for now)
  - Text message / urgent comms summarization (different tool)

- **Allowed tools / languages:** Python, bash, markdown, SQLite, local vector
  store (ChromaDB or similar). Claude API for synthesis. Local-first.

---

## 5. Boundaries

Hard constraints. These don't change without a contract amendment.

| Boundary | Limit |
|----------|-------|
| **Budget cap ($/month)** | $50 (Claude API costs) |
| **Allowed external services** | arXiv API, GitHub API, RSS feeds, web scraping of public podcast/newsletter pages |
| **Forbidden actions** | No engagement-optimized content. No content selected for provocation or anxiety. No hallucinated evidence or sources. No auto-posting to any external service. |
| **Data handling** | All data stored locally. No PII collection. Evidence store is append-only (never delete evidence, only reclassify). |

---

## 6. Success Signals

### Leading indicators (are we building the right thing?)

| Signal | How we'd know | Status |
|--------|---------------|--------|
| Steward opens morning digest daily | Consistent use within 1hr of waking | `unknown` |
| Digest items get shared to communities | Steward forwards/quotes to post-labor or autonomous company groups | `unknown` |
| Steward feels oriented after reading | Self-reported: "I know where things are flowing" | `unknown` |
| Evidence clusters feel meaningful | Steward confirms or corrects cluster labels | `unknown` |
| Generative energy | Digest sparks new ideas, creation-engine entries, or conversations | `unknown` |

### Lagging indicators (is the product succeeding?)

| Signal | How we'd know | Status |
|--------|---------------|--------|
| Hypothesis map influences decisions | Steward references map when making startup choices | `unknown` |
| Map becomes a shareable artifact | Steward sends map to community members | `unknown` |
| World feels more legible | Steward reports less "shadows in the dark," more "shared progression" | `unknown` |
| Interest adaptation works | When steward's focus shifts, the tool follows within ~3 days | `unknown` |

### Current blind spots (what we can't measure yet)

- Is filtering aggressive enough, or does noise slip through?
- Are we catching unpopular-but-significant signals, or just quieter popular ones?
- Does the noon cadence add value or is morning enough?
- What "inspiring" means in measurable terms
- How to distinguish "I didn't open it because it's not useful" from "I didn't open it because I'm busy"

---

## 7. Decision Rights

| Decision | Authority |
|----------|-----------|
| Refine intent | Steward (agent proposes) |
| Change scope | Steward |
| Add/remove sources | Agent proposes, steward approves |
| Add dependency | Agent (notify steward) |
| Deploy / publish | Steward |
| Modify this contract | Steward (agent proposes via amendment) |

---

## 8. Amendment Process

1. Agent writes a proposal to `governance/proposals/YYYY-MM-DD-title.md`
   including: what changed, why, and what evidence prompted it
2. Steward reviews — approves, rejects, or refines
3. Approved changes merge into this CONTRACT.md
4. Bump the contract version

---

## 9. Signatures

| Role | Name | Date |
|------|------|------|
| Steward | Clovis | 2026-08-19 |
| Agent | Claude Code | (auto-signed on first read) |
