# Steward Configuration Reference

All configurable parameters live in `governance/steward_config.json`.
The steward reads this file at the start of every run.

## Sections

### `cadence`

Controls when and how often the steward wakes up.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `interval_hours` | int | 24 | Hours between scheduled runs |
| `schedule_utc` | string | "13:00" | UTC time for the daily trigger |
| `timezone` | string | "America/Los_Angeles" | Steward's display timezone |
| `schedule_local` | string | "06:00" | Local time equivalent (informational) |

### `triggers.early_wake`

Conditions that should wake the steward before the next scheduled run.
The steward checks these at the end of each run and outputs a trigger
manifest if any condition is met.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `source_failure_count` | int | 2 | Wake early if this many sources fail in a single run |
| `evidence_staleness_hours` | int | 48 | Wake early if no new evidence for this long |
| `hypothesis_conflict` | bool | true | Wake early if new evidence directly conflicts with an active hypothesis |
| `proposal_approved` | bool | true | Wake early when a steward-approved proposal is waiting for implementation |

### `monitoring`

Validation checks the steward runs to determine system health.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `pipeline_timeout_seconds` | int | 120 | Max time for any single pipeline step |
| `min_evidence_per_source` | int | 1 | Flag a source if it produces fewer items than this |
| `min_total_evidence_per_run` | int | 5 | Unhealthy if total new evidence below this |
| `source_health_check` | bool | true | Run per-source health validation |
| `digest_required` | bool | true | Fail health check if no digest is generated |
| `max_digest_age_hours` | int | 36 | Flag if most recent digest is older than this |

### `dispatch`

Controls subagent dispatch behavior.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | bool | true | Master switch for subagent dispatch |
| `max_concurrent_subagents` | int | 3 | Cap on parallel subagents per run |
| `allowed_actions` | list | (see config) | Action types the steward can dispatch |
| `auto_approve_within_scope` | bool | true | Dispatch immediately for in-scope work |
| `require_proposal_outside_scope` | bool | true | Force proposal for out-of-scope work |

### `hypotheses`

Hypothesis store behavior.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `store_path` | string | "map/hypotheses.json" | JSON backing store (relative to repo root) |
| `render_path` | string | "map/HYPOTHESES.md" | Rendered markdown output |
| `max_evidence_age_days` | int | 90 | Evidence older than this is flagged as stale |
| `auto_weaken_if_no_evidence_days` | int | 30 | Auto-transition to "weakening" if no new evidence |
| `auto_retire_if_weakened_days` | int | 60 | Auto-retire if weakened for this long |

### `proposals`

Proposal lifecycle parameters.

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `store_path` | string | "governance/proposals/index.json" | Proposal index |
| `proposals_dir` | string | "governance/proposals" | Directory for proposal markdown files |
| `auto_expire_days` | int | 14 | Proposals auto-expire if not acted on |

### `sources`

Source registry. Maps source names to ingestion scripts.

| Field | Type | Description |
|-------|------|-------------|
| `approved` | list | Source names approved in the contract |
| `scripts` | object | Map of source name to ingestion script path |
