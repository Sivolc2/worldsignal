# Hypothesis Map

> A living document. Each hypothesis represents a claim about where the world
> is heading. Evidence accumulates for or against each. New hypotheses emerge
> from the evidence clusters. This is the product.

## How to read this map

- **Active** — currently accumulating evidence
- **Strengthening** — recent evidence supports this
- **Weakening** — recent evidence challenges this
- **Emerged** — new hypothesis surfaced from evidence clustering
- **Retired** — enough evidence to confirm or reject

---

## Hypotheses

### H1: Agent reliability is the next capability frontier

**Claim:** As raw capability plateaus, the competitive gap opens around reliability, consistency, and verifiability of agent behavior — not raw performance.
**Status:** emerged
**Evidence for:**
- [2026-08-19] [arxiv] Self-improving agents are fragile under variance and task reordering [link](https://arxiv.org/abs/2608.18066v1)
- [2026-08-19] [arxiv] LLM preference judgments are not self-consistent — cannot be reproduced by a single coherent utility function [link](https://arxiv.org/abs/2608.17644v1)
- [2026-08-19] [arxiv] API model migrations hide item-level regressions behind aggregate scores [link](https://arxiv.org/abs/2608.17719v1)
**Evidence against:**
- (none yet)
**Last updated:** 2026-08-19
**Implications for steward:** Products that instrument, audit, and guarantee agent behavior will command premium trust. Relevant to Paperclip's autonomous company stack.

---

### H2: Agent memory is commoditizing into middleware

**Claim:** Persistent cross-session memory is consolidating from a product differentiator into a standardized infrastructure layer.
**Status:** emerged
**Evidence for:**
- [2026-08-19] [github] claude-mem (91k stars), mem0 (63k stars) and multiple harness projects all targeting the same layer [link](https://github.com/thedotmack/claude-mem)
**Evidence against:**
- (none yet)
**Last updated:** 2026-08-19
**Implications for steward:** Build above the memory layer, not at it. Memory-as-a-product plays are likely to be commoditized.

---

### H3: Versioned workspaces will define agent auditability

**Claim:** Agents need explicit state management (git-like workspace awareness) to be auditable, rollback-capable, and trusted in knowledge work.
**Status:** emerged
**Evidence for:**
- [2026-08-19] [arxiv] StagedWorkspace — agents editing documents need explicit workspace-state contracts [link](https://arxiv.org/abs/2608.18050v1)
**Evidence against:**
- (none yet)
**Last updated:** 2026-08-19
**Implications for steward:** "Git for agent workspaces" is an entire product category waiting. Early movers define audit/trust standards.

---

### Template

```
### H[N]: [Title]

**Claim:** [One sentence]
**Status:** active | strengthening | weakening | emerged | retired
**Evidence for:**
- [date] [source] [summary] [link]
**Evidence against:**
- [date] [source] [summary] [link]
**Last updated:** [date]
**Implications for steward:** [what this means for the startup / worldview]
```
