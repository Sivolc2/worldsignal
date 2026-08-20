#!/usr/bin/env python3
"""Monitors — validation checks, trigger evaluation, early wake detection.

Produces a health report and a dispatch manifest for the steward.
The dispatch manifest tells the cloud agent what subagents to spin up.
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_config() -> dict:
    config_path = os.path.join(REPO_ROOT, "governance", "steward_config.json")
    with open(config_path) as f:
        return json.load(f)


def check_pipeline_health(pipeline_results: dict, config: dict) -> list:
    """Validate pipeline results against monitoring thresholds."""
    issues = []
    mon = config["monitoring"]

    failure_count = 0
    for name, result in pipeline_results.items():
        if result.get("status") != "ok":
            issues.append({
                "severity": "error",
                "source": name,
                "message": f"Pipeline step '{name}' failed: {result.get('error', 'unknown')}",
            })
            failure_count += 1

    if mon.get("digest_required") and pipeline_results.get("digest", {}).get("status") != "ok":
        issues.append({
            "severity": "error",
            "source": "digest",
            "message": "Digest generation required but failed or missing",
        })

    return issues


def check_source_health(evidence_by_source: dict, config: dict) -> list:
    """Check per-source evidence counts against thresholds."""
    issues = []
    mon = config["monitoring"]
    approved = config["sources"]["approved"]
    min_per_source = mon.get("min_evidence_per_source", 1)

    for source in approved:
        count = evidence_by_source.get(source, 0)
        if count < min_per_source:
            issues.append({
                "severity": "warning",
                "source": source,
                "message": f"Source '{source}' produced {count} items (min: {min_per_source})",
            })

    total = sum(evidence_by_source.get(s, 0) for s in approved)
    min_total = mon.get("min_total_evidence_per_run", 5)
    if total < min_total:
        issues.append({
            "severity": "error",
            "source": "total",
            "message": f"Total new evidence ({total}) below minimum ({min_total})",
        })

    return issues


def check_digest_freshness(config: dict) -> list:
    """Check if the most recent digest is too old."""
    issues = []
    digest_dir = os.path.join(REPO_ROOT, "digest")
    max_age = config["monitoring"].get("max_digest_age_hours", 36)

    if not os.path.isdir(digest_dir):
        issues.append({
            "severity": "warning",
            "source": "digest",
            "message": "No digest directory found",
        })
        return issues

    digests = sorted(f for f in os.listdir(digest_dir) if f.endswith(".md"))
    if not digests:
        issues.append({
            "severity": "warning",
            "source": "digest",
            "message": "No digests found",
        })
        return issues

    latest = digests[-1].replace(".md", "")
    try:
        digest_date = datetime.strptime(latest, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        age_hours = (datetime.now(timezone.utc) - digest_date).total_seconds() / 3600
        if age_hours > max_age:
            issues.append({
                "severity": "warning",
                "source": "digest",
                "message": f"Latest digest ({latest}) is {age_hours:.0f}h old (max: {max_age}h)",
            })
    except ValueError:
        pass

    return issues


def check_evidence_staleness(config: dict) -> list:
    """Check if evidence store has gone stale."""
    issues = []
    stale_hours = config["triggers"]["early_wake"].get("evidence_staleness_hours", 48)
    evidence_dir = os.path.join(REPO_ROOT, "evidence", "items")

    if not os.path.isdir(evidence_dir):
        return issues

    now = datetime.now(timezone.utc)
    latest_ts = None

    for fname in os.listdir(evidence_dir):
        if not fname.endswith(".json"):
            continue
        try:
            with open(os.path.join(evidence_dir, fname)) as f:
                item = json.load(f)
            ts = datetime.fromisoformat(item["timestamp"])
            if latest_ts is None or ts > latest_ts:
                latest_ts = ts
        except (json.JSONDecodeError, KeyError, ValueError):
            continue

    if latest_ts:
        age_hours = (now - latest_ts).total_seconds() / 3600
        if age_hours > stale_hours:
            issues.append({
                "severity": "warning",
                "source": "evidence",
                "message": f"No new evidence for {age_hours:.0f}h (threshold: {stale_hours}h)",
            })

    return issues


def evaluate_triggers(pipeline_results: dict, evidence_by_source: dict,
                      hypothesis_conflicts: list, config: dict) -> dict:
    """Evaluate early-wake triggers. Returns trigger report."""
    triggers = config["triggers"]["early_wake"]
    fired = []

    failure_count = sum(1 for r in pipeline_results.values() if r.get("status") != "ok")
    if failure_count >= triggers.get("source_failure_count", 2):
        fired.append({
            "trigger": "source_failure",
            "reason": f"{failure_count} sources failed (threshold: {triggers['source_failure_count']})",
            "urgency": "high",
        })

    if triggers.get("hypothesis_conflict") and hypothesis_conflicts:
        fired.append({
            "trigger": "hypothesis_conflict",
            "reason": f"{len(hypothesis_conflicts)} hypothesis conflict(s) detected",
            "urgency": "medium",
            "details": hypothesis_conflicts,
        })

    from proposals import approved_awaiting_implementation
    if triggers.get("proposal_approved"):
        awaiting = approved_awaiting_implementation()
        if awaiting:
            fired.append({
                "trigger": "proposal_approved",
                "reason": f"{len(awaiting)} approved proposal(s) awaiting implementation",
                "urgency": "medium",
                "proposals": [p["id"] for p in awaiting],
            })

    return {
        "any_fired": len(fired) > 0,
        "triggers": fired,
    }


def build_dispatch_manifest(health_issues: list, trigger_report: dict,
                            hypothesis_alerts: list, config: dict) -> dict:
    """Build a dispatch manifest — tells the cloud agent what subagents to spin up.

    The manifest is a structured list of dispatch requests. Each request has:
    - action: what type of work (must be in config.dispatch.allowed_actions)
    - priority: high/medium/low
    - prompt: suggested prompt for the subagent
    - scope: in_scope / scope_adjacent / out_of_scope
    """
    dispatch = config["dispatch"]
    if not dispatch.get("enabled"):
        return {"dispatch_enabled": False, "requests": []}

    allowed = set(dispatch.get("allowed_actions", []))
    max_agents = dispatch.get("max_concurrent_subagents", 3)
    requests = []

    for issue in health_issues:
        if issue["severity"] == "error" and issue["source"] not in ("total", "digest"):
            if "fix_source" in allowed:
                requests.append({
                    "action": "fix_source",
                    "priority": "high",
                    "scope": "in_scope",
                    "target": issue["source"],
                    "prompt": f"Fix broken source '{issue['source']}': {issue['message']}. "
                              f"Check the ingestion script, verify the feed URL, and ensure "
                              f"it produces evidence items.",
                })

    for trigger in trigger_report.get("triggers", []):
        if trigger["trigger"] == "proposal_approved":
            for pid in trigger.get("proposals", []):
                if "build_feature" in allowed:
                    requests.append({
                        "action": "build_feature",
                        "priority": "medium",
                        "scope": "in_scope",
                        "target": pid,
                        "prompt": f"Implement approved proposal {pid}. Read the proposal "
                                  f"markdown in governance/proposals/ for full details.",
                    })

    for alert in hypothesis_alerts:
        if alert["action"] == "auto_weaken" and "investigate_thread" in allowed:
            requests.append({
                "action": "investigate_thread",
                "priority": "low",
                "scope": "in_scope",
                "target": alert["hypothesis"],
                "prompt": f"Hypothesis {alert['hypothesis']} has gone stale: {alert['reason']}. "
                          f"Search for new evidence. If evidence exists, add it. If the "
                          f"hypothesis should be retired, recommend retirement.",
            })

    if len(requests) > max_agents:
        requests.sort(key=lambda r: {"high": 0, "medium": 1, "low": 2}[r["priority"]])
        requests = requests[:max_agents]

    return {
        "dispatch_enabled": True,
        "requests": requests,
        "capped": len(requests) == max_agents,
    }


def full_health_check(pipeline_results: dict = None, new_evidence_by_source: dict = None) -> dict:
    """Run all monitors and return a comprehensive health report.

    Can be run standalone (without pipeline results) for trigger checking,
    or with pipeline results for full post-run validation.
    """
    config = load_config()
    all_issues = []

    if pipeline_results:
        all_issues.extend(check_pipeline_health(pipeline_results, config))
        if config["monitoring"].get("source_health_check") and new_evidence_by_source:
            all_issues.extend(check_source_health(new_evidence_by_source, config))

    all_issues.extend(check_digest_freshness(config))
    all_issues.extend(check_evidence_staleness(config))

    errors = [i for i in all_issues if i["severity"] == "error"]
    warnings = [i for i in all_issues if i["severity"] == "warning"]

    return {
        "healthy": len(errors) == 0,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "issues": all_issues,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


if __name__ == "__main__":
    report = full_health_check()
    print(f"Health: {'OK' if report['healthy'] else 'UNHEALTHY'}")
    print(f"  Errors: {report['error_count']}, Warnings: {report['warning_count']}")
    for issue in report["issues"]:
        print(f"  [{issue['severity']}] {issue['source']}: {issue['message']}")
