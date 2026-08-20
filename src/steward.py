#!/usr/bin/env python3
"""Stewardship loop — the autonomous governance agent.

Reads configuration from governance/steward_config.json.
Uses hypothesis_store, proposals, and monitors modules.

Algorithm:
1. Load config
2. Run pipeline (ingest → sync → digest) using configured sources
3. Run monitors (health checks, triggers, staleness)
4. Check hypothesis store for staleness/conflicts
5. Check proposals for pending/approved/expired
6. Build dispatch manifest (what subagents to spin up)
7. Write loop entry + output manifest
8. Commit + push
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "src"))

EVIDENCE_DIR = os.path.join(REPO_ROOT, "evidence", "items")
DIGEST_DIR = os.path.join(REPO_ROOT, "digest")
LOOP_DIR = os.path.join(REPO_ROOT, "governance", "loop")
METRICS_FILE = os.path.join(REPO_ROOT, "governance", "metrics.json")
DISPATCH_FILE = os.path.join(REPO_ROOT, "governance", "dispatch_manifest.json")


def load_config() -> dict:
    config_path = os.path.join(REPO_ROOT, "governance", "steward_config.json")
    with open(config_path) as f:
        return json.load(f)


def run_pipeline(config: dict) -> tuple:
    """Run the full ingestion pipeline. Returns (results_dict, new_evidence_by_source)."""
    timeout = config["monitoring"].get("pipeline_timeout_seconds", 120)
    results = {}

    evidence_before = _count_evidence_by_source()

    scripts = set()
    for source, script in config["sources"]["scripts"].items():
        scripts.add(script)

    for script in sorted(scripts):
        name = os.path.splitext(os.path.basename(script))[0]
        try:
            r = subprocess.run(
                ["python3", os.path.join(REPO_ROOT, script)],
                capture_output=True, text=True, timeout=timeout,
                cwd=REPO_ROOT,
            )
            results[name] = {
                "status": "ok" if r.returncode == 0 else "error",
                "output": r.stdout.strip()[-200:],
                "error": r.stderr.strip()[-200:] if r.returncode != 0 else None,
            }
        except subprocess.TimeoutExpired:
            results[name] = {"status": "timeout", "output": None, "error": f"Timed out after {timeout}s"}
        except Exception as e:
            results[name] = {"status": "error", "output": None, "error": str(e)}

    try:
        r = subprocess.run(
            ["python3", os.path.join(REPO_ROOT, "src/evidence_store.py")],
            capture_output=True, text=True, timeout=timeout, cwd=REPO_ROOT,
        )
        results["vector_sync"] = {
            "status": "ok" if r.returncode == 0 else "error",
            "output": r.stdout.strip()[-200:],
        }
    except Exception as e:
        results["vector_sync"] = {"status": "error", "error": str(e)}

    try:
        r = subprocess.run(
            ["python3", os.path.join(REPO_ROOT, "src/generate_digest.py")],
            capture_output=True, text=True, timeout=timeout, cwd=REPO_ROOT,
        )
        results["digest"] = {
            "status": "ok" if r.returncode == 0 else "error",
            "output": r.stdout.strip()[-500:],
        }
    except Exception as e:
        results["digest"] = {"status": "error", "error": str(e)}

    evidence_after = _count_evidence_by_source()
    new_evidence = {}
    for source in set(list(evidence_after.keys()) + list(evidence_before.keys())):
        diff = evidence_after.get(source, 0) - evidence_before.get(source, 0)
        if diff > 0:
            new_evidence[source] = diff

    return results, new_evidence


def _count_evidence_by_source() -> dict:
    counts = {}
    if not os.path.isdir(EVIDENCE_DIR):
        return counts
    for fname in os.listdir(EVIDENCE_DIR):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(EVIDENCE_DIR, fname)) as f:
                item = json.load(f)
            src = item.get("source", "unknown")
            counts[src] = counts.get(src, 0) + 1
        except (json.JSONDecodeError, KeyError):
            counts["parse_error"] = counts.get("parse_error", 0) + 1
    return counts


def snapshot_metrics(new_evidence: dict) -> dict:
    """Collect current metrics snapshot."""
    now = datetime.now(timezone.utc)
    evidence_by_source = _count_evidence_by_source()
    total_evidence = sum(evidence_by_source.values())

    config = load_config()
    approved_sources = set(config["sources"]["approved"])
    active_sources = set(evidence_by_source.keys()) & approved_sources
    missing_sources = approved_sources - active_sources

    digest_count = 0
    latest_digest = None
    if os.path.isdir(DIGEST_DIR):
        digests = sorted(f for f in os.listdir(DIGEST_DIR) if f.endswith(".md"))
        digest_count = len(digests)
        if digests:
            latest_digest = digests[-1]

    loop_entries = 0
    if os.path.isdir(LOOP_DIR):
        loop_entries = len([f for f in os.listdir(LOOP_DIR) if f.endswith(".md")])

    snapshot = {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "evidence_total": total_evidence,
        "evidence_by_source": evidence_by_source,
        "new_evidence": new_evidence,
        "digest_count": digest_count,
        "latest_digest": latest_digest,
        "loop_entries": loop_entries,
        "source_coverage": {
            "active": sorted(active_sources),
            "missing": sorted(missing_sources),
            "ratio": f"{len(active_sources)}/{len(approved_sources)}",
        },
    }

    try:
        with open(METRICS_FILE) as f:
            metrics = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        metrics = {"schema_version": 1, "snapshots": []}

    metrics["snapshots"].append(snapshot)
    with open(METRICS_FILE, "w") as f:
        json.dump(metrics, f, indent=2)

    return snapshot


def write_loop_entry(snapshot: dict, health_report: dict, pipeline_results: dict,
                     trigger_report: dict, dispatch_manifest: dict,
                     hypothesis_alerts: list, proposal_summary: dict):
    """Write today's governance loop entry."""
    os.makedirs(LOOP_DIR, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filepath = os.path.join(LOOP_DIR, f"{today}.md")

    pipeline_summary = "\n".join(
        f"  - {name}: {r['status']}" for name, r in pipeline_results.items()
    )

    issues_text = ""
    for issue in health_report.get("issues", []):
        issues_text += f"  - [{issue['severity']}] {issue['source']}: {issue['message']}\n"
    if not issues_text:
        issues_text = "  None\n"

    triggers_text = ""
    for t in trigger_report.get("triggers", []):
        triggers_text += f"  - **{t['trigger']}** ({t['urgency']}): {t['reason']}\n"
    if not triggers_text:
        triggers_text = "  None\n"

    dispatch_text = ""
    for req in dispatch_manifest.get("requests", []):
        dispatch_text += f"  - [{req['priority']}] {req['action']}: {req.get('target', 'general')}\n"
    if not dispatch_text:
        dispatch_text = "  None\n"

    hypothesis_text = ""
    for alert in hypothesis_alerts:
        hypothesis_text += f"  - {alert['hypothesis']}: {alert['action']} — {alert['reason']}\n"
    if not hypothesis_text:
        hypothesis_text = "  None\n"

    proposal_text = ""
    if proposal_summary.get("pending"):
        proposal_text += f"  - Pending: {len(proposal_summary['pending'])} proposals\n"
    if proposal_summary.get("approved"):
        proposal_text += f"  - Approved (awaiting implementation): {len(proposal_summary['approved'])} proposals\n"
    if proposal_summary.get("expired"):
        proposal_text += f"  - Expired this run: {len(proposal_summary['expired'])} proposals\n"
    if not proposal_text:
        proposal_text = "  None\n"

    new_ev = snapshot.get("new_evidence", {})
    new_ev_text = json.dumps(new_ev) if new_ev else "none"

    content = f"""# Loop Entry — {today}

## Pipeline Run
{pipeline_summary}

## Metrics Snapshot
- Evidence total: {snapshot['evidence_total']}
- New this run: {new_ev_text}
- Evidence by source: {json.dumps(snapshot['evidence_by_source'])}
- Source coverage: {snapshot['source_coverage']['ratio']} ({', '.join(snapshot['source_coverage']['active'])} active)
- Missing sources: {', '.join(snapshot['source_coverage']['missing']) or 'none'}
- Digests generated: {snapshot['digest_count']}

## Health Assessment
- **Healthy:** {'Yes' if health_report['healthy'] else 'No'}
- **Errors:** {health_report['error_count']}
- **Warnings:** {health_report['warning_count']}

### Issues
{issues_text}
### Triggers Fired
{triggers_text}
### Dispatch Manifest
{dispatch_text}
### Hypothesis Alerts
{hypothesis_text}
### Proposal Activity
{proposal_text}
## Steward Action Required
{'None — system is healthy.' if health_report['healthy'] and not trigger_report.get('any_fired') else 'See issues, triggers, and dispatch manifest above.'}
"""

    with open(filepath, "w") as f:
        f.write(content)

    return filepath


def write_dispatch_manifest(manifest: dict):
    """Write dispatch manifest for the cloud agent to read."""
    with open(DISPATCH_FILE, "w") as f:
        json.dump(manifest, f, indent=2)


def git_commit_and_push():
    """Commit loop entry + new evidence + digest and push."""
    try:
        subprocess.run(["git", "add", "-A"], cwd=REPO_ROOT, check=True, capture_output=True)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        msg = f"Stewardship loop — {today}\n\nAutonomous daily run: ingest, digest, metrics, monitors, loop entry."
        subprocess.run(
            ["git", "commit", "-m", msg],
            cwd=REPO_ROOT, check=True, capture_output=True,
        )
        subprocess.run(
            ["git", "push"],
            cwd=REPO_ROOT, check=True, capture_output=True,
        )
        print("Committed and pushed.")
    except subprocess.CalledProcessError as e:
        print(f"Git operation failed: {e.stderr.decode() if e.stderr else e}")


def main():
    print("=" * 60)
    print("WorldSignal Stewardship Loop")
    print("=" * 60)

    # 0. Load config
    config = load_config()
    print(f"\nConfig loaded. Cadence: {config['cadence']['interval_hours']}h")
    print(f"  Sources: {', '.join(config['sources']['approved'])}")
    print(f"  Dispatch: {'enabled' if config['dispatch']['enabled'] else 'disabled'}")

    # 1. Run pipeline
    print("\n[1/7] Running pipeline...")
    pipeline_results, new_evidence = run_pipeline(config)
    for name, result in pipeline_results.items():
        print(f"  {name}: {result['status']}")
    print(f"  New evidence: {json.dumps(new_evidence)}")

    # 2. Snapshot metrics
    print("\n[2/7] Snapshotting metrics...")
    snapshot = snapshot_metrics(new_evidence)
    print(f"  Evidence: {snapshot['evidence_total']} total")
    print(f"  Sources: {snapshot['source_coverage']['ratio']} active")

    # 3. Run monitors
    print("\n[3/7] Running monitors...")
    import monitors
    health_report = monitors.full_health_check(pipeline_results, new_evidence)
    print(f"  Healthy: {health_report['healthy']}")
    print(f"  Errors: {health_report['error_count']}, Warnings: {health_report['warning_count']}")
    for issue in health_report["issues"]:
        print(f"    [{issue['severity']}] {issue['source']}: {issue['message']}")

    # 4. Check hypothesis store
    print("\n[4/7] Checking hypotheses...")
    import hypothesis_store
    hypothesis_store.migrate_from_markdown()
    hypothesis_alerts = hypothesis_store.check_staleness()
    active_hypotheses = hypothesis_store.list_active()
    print(f"  Active hypotheses: {len(active_hypotheses)}")
    if hypothesis_alerts:
        print(f"  Alerts: {len(hypothesis_alerts)}")
        for a in hypothesis_alerts:
            print(f"    {a['hypothesis']}: {a['action']}")

    # 5. Check proposals
    print("\n[5/7] Checking proposals...")
    import proposals
    expired = proposals.check_expired()
    pending_list = proposals.pending()
    approved_list = proposals.approved_awaiting_implementation()
    proposal_summary = {
        "pending": pending_list,
        "approved": approved_list,
        "expired": expired,
    }
    print(f"  Pending: {len(pending_list)}, Approved: {len(approved_list)}, Expired: {len(expired)}")

    # 6. Evaluate triggers + build dispatch manifest
    print("\n[6/7] Evaluating triggers...")
    hypothesis_conflicts = []
    trigger_report = monitors.evaluate_triggers(
        pipeline_results, new_evidence, hypothesis_conflicts, config
    )
    print(f"  Triggers fired: {trigger_report['any_fired']}")
    for t in trigger_report.get("triggers", []):
        print(f"    {t['trigger']}: {t['reason']}")

    dispatch_manifest = monitors.build_dispatch_manifest(
        health_report["issues"], trigger_report, hypothesis_alerts, config
    )
    print(f"  Dispatch requests: {len(dispatch_manifest.get('requests', []))}")
    for req in dispatch_manifest.get("requests", []):
        print(f"    [{req['priority']}] {req['action']}: {req.get('target', '')}")

    write_dispatch_manifest(dispatch_manifest)

    # 7. Write loop entry + commit
    print("\n[7/7] Writing loop entry...")
    entry_path = write_loop_entry(
        snapshot, health_report, pipeline_results,
        trigger_report, dispatch_manifest, hypothesis_alerts, proposal_summary
    )
    print(f"  Written to {entry_path}")

    git_commit_and_push()

    # Summary
    print("\n" + "=" * 60)
    if health_report["healthy"] and not trigger_report["any_fired"]:
        print("STEWARDSHIP: All healthy. No triggers. Sleeping.")
    elif health_report["healthy"]:
        print(f"STEWARDSHIP: Healthy but {len(trigger_report['triggers'])} trigger(s) fired.")
    else:
        print(f"STEWARDSHIP: {health_report['error_count']} error(s). See loop entry.")

    if dispatch_manifest.get("requests"):
        print(f"DISPATCH: {len(dispatch_manifest['requests'])} subagent(s) recommended.")
        print("  The cloud agent should read governance/dispatch_manifest.json and act.")

    print("=" * 60)

    return 0 if health_report["healthy"] else 1


if __name__ == "__main__":
    sys.exit(main())
