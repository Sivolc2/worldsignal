#!/usr/bin/env python3
"""Stewardship loop — the autonomous governance agent.

Runs daily. Algorithm:
1. Run pipeline (ingest → sync → digest)
2. Snapshot metrics (evidence count, source coverage, pipeline health)
3. Review recent loop entries + hypothesis map
4. Decide: healthy? picture complete? new threads to propose?
5. Write loop entry + commit
"""

import json
import os
import subprocess
import sys
from datetime import datetime, timezone, timedelta

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(REPO_ROOT, "evidence", "items")
DIGEST_DIR = os.path.join(REPO_ROOT, "digest")
LOOP_DIR = os.path.join(REPO_ROOT, "governance", "loop")
PROPOSALS_DIR = os.path.join(REPO_ROOT, "governance", "proposals")
METRICS_FILE = os.path.join(REPO_ROOT, "governance", "metrics.json")
MAP_FILE = os.path.join(REPO_ROOT, "map", "HYPOTHESES.md")
CONTRACT_FILE = os.path.join(REPO_ROOT, "governance", "CONTRACT.md")


def run_pipeline() -> dict:
    """Run the full ingestion pipeline. Returns status dict."""
    results = {}
    scripts = [
        ("arxiv", "src/ingest_arxiv.py"),
        ("github", "src/ingest_github.py"),
        ("podcasts", "src/ingest_podcasts.py"),
    ]

    for name, script in scripts:
        try:
            r = subprocess.run(
                ["python3", os.path.join(REPO_ROOT, script)],
                capture_output=True, text=True, timeout=120,
                cwd=REPO_ROOT,
            )
            results[name] = {
                "status": "ok" if r.returncode == 0 else "error",
                "output": r.stdout.strip()[-200:],
                "error": r.stderr.strip()[-200:] if r.returncode != 0 else None,
            }
        except subprocess.TimeoutExpired:
            results[name] = {"status": "timeout", "output": None, "error": "Timed out after 120s"}
        except Exception as e:
            results[name] = {"status": "error", "output": None, "error": str(e)}

    # Sync to vector store
    try:
        r = subprocess.run(
            ["python3", os.path.join(REPO_ROOT, "src/evidence_store.py")],
            capture_output=True, text=True, timeout=120,
            cwd=REPO_ROOT,
        )
        results["vector_sync"] = {
            "status": "ok" if r.returncode == 0 else "error",
            "output": r.stdout.strip()[-200:],
        }
    except Exception as e:
        results["vector_sync"] = {"status": "error", "error": str(e)}

    # Generate digest
    try:
        r = subprocess.run(
            ["python3", os.path.join(REPO_ROOT, "src/generate_digest.py")],
            capture_output=True, text=True, timeout=120,
            cwd=REPO_ROOT,
        )
        results["digest"] = {
            "status": "ok" if r.returncode == 0 else "error",
            "output": r.stdout.strip()[-500:],
        }
    except Exception as e:
        results["digest"] = {"status": "error", "error": str(e)}

    return results


def snapshot_metrics() -> dict:
    """Collect current metrics snapshot."""
    now = datetime.now(timezone.utc)

    # Evidence counts by source
    evidence_by_source = {}
    total_evidence = 0
    if os.path.isdir(EVIDENCE_DIR):
        for fname in os.listdir(EVIDENCE_DIR):
            if not fname.endswith(".json"):
                continue
            total_evidence += 1
            try:
                with open(os.path.join(EVIDENCE_DIR, fname)) as f:
                    item = json.load(f)
                src = item.get("source", "unknown")
                evidence_by_source[src] = evidence_by_source.get(src, 0) + 1
            except (json.JSONDecodeError, KeyError):
                evidence_by_source["parse_error"] = evidence_by_source.get("parse_error", 0) + 1

    # Digest count
    digest_count = 0
    latest_digest = None
    if os.path.isdir(DIGEST_DIR):
        digests = sorted([f for f in os.listdir(DIGEST_DIR) if f.endswith(".md")])
        digest_count = len(digests)
        if digests:
            latest_digest = digests[-1]

    # Loop entry count
    loop_entries = 0
    if os.path.isdir(LOOP_DIR):
        loop_entries = len([f for f in os.listdir(LOOP_DIR) if f.endswith(".md")])

    # Source coverage (which approved sources have evidence?)
    approved_sources = {"arxiv", "github", "alphasignal", "dwarkesh", "moonshot"}
    active_sources = set(evidence_by_source.keys()) & approved_sources
    missing_sources = approved_sources - active_sources

    snapshot = {
        "timestamp": now.isoformat(),
        "date": now.strftime("%Y-%m-%d"),
        "evidence_total": total_evidence,
        "evidence_by_source": evidence_by_source,
        "digest_count": digest_count,
        "latest_digest": latest_digest,
        "loop_entries": loop_entries,
        "source_coverage": {
            "active": sorted(active_sources),
            "missing": sorted(missing_sources),
            "ratio": f"{len(active_sources)}/{len(approved_sources)}",
        },
    }

    # Append to metrics file
    try:
        with open(METRICS_FILE) as f:
            metrics = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        metrics = {"schema_version": 1, "snapshots": []}

    metrics["snapshots"].append(snapshot)
    with open(METRICS_FILE, "w") as f:
        json.dump(metrics, f, indent=2)

    return snapshot


def assess_health(snapshot: dict, pipeline_results: dict) -> dict:
    """Assess system health and decide what to do."""
    issues = []
    proposals = []
    healthy = True

    # Pipeline health
    for name, result in pipeline_results.items():
        if result.get("status") != "ok":
            issues.append(f"Pipeline step '{name}' failed: {result.get('error', 'unknown error')}")
            healthy = False

    # Source coverage
    missing = snapshot["source_coverage"]["missing"]
    if missing:
        issues.append(f"Missing sources: {', '.join(missing)}")
        if len(missing) > 2:
            proposals.append(
                f"Source coverage is {snapshot['source_coverage']['ratio']}. "
                f"Propose adding ingestion for: {', '.join(missing)}"
            )

    # Evidence growth (compare to previous snapshot if available)
    try:
        with open(METRICS_FILE) as f:
            metrics = json.load(f)
        if len(metrics["snapshots"]) >= 2:
            prev = metrics["snapshots"][-2]
            growth = snapshot["evidence_total"] - prev["evidence_total"]
            if growth == 0:
                issues.append("No new evidence since last run — ingestion may be stale")
                healthy = False
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass

    # Digest exists for today
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    if snapshot.get("latest_digest") != f"{today}.md":
        issues.append(f"No digest generated for {today}")

    return {
        "healthy": healthy and len(issues) == 0,
        "issues": issues,
        "proposals": proposals,
        "picture_complete": len(missing) == 0 and healthy,
    }


def get_recent_loop_entries(days: int = 7) -> list:
    """Read recent loop entries."""
    entries = []
    if not os.path.isdir(LOOP_DIR):
        return entries

    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    for fname in sorted(os.listdir(LOOP_DIR)):
        if fname.endswith(".md") and fname >= cutoff:
            with open(os.path.join(LOOP_DIR, fname)) as f:
                entries.append({"date": fname.replace(".md", ""), "content": f.read()})

    return entries


def write_loop_entry(snapshot: dict, health: dict, pipeline_results: dict):
    """Write today's governance loop entry."""
    os.makedirs(LOOP_DIR, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filepath = os.path.join(LOOP_DIR, f"{today}.md")

    pipeline_summary = "\n".join(
        f"  - {name}: {r['status']}" for name, r in pipeline_results.items()
    )

    issues_text = "\n".join(f"  - {i}" for i in health["issues"]) if health["issues"] else "  None"
    proposals_text = "\n".join(f"  - {p}" for p in health["proposals"]) if health["proposals"] else "  None"

    content = f"""# Loop Entry — {today}

## Pipeline Run
{pipeline_summary}

## Metrics Snapshot
- Evidence total: {snapshot['evidence_total']}
- Evidence by source: {json.dumps(snapshot['evidence_by_source'])}
- Source coverage: {snapshot['source_coverage']['ratio']} ({', '.join(snapshot['source_coverage']['active'])} active)
- Missing sources: {', '.join(snapshot['source_coverage']['missing']) or 'none'}
- Digests generated: {snapshot['digest_count']}
- Loop entries: {snapshot['loop_entries']}

## Health Assessment
- **Healthy:** {'Yes' if health['healthy'] else 'No'}
- **Picture complete:** {'Yes' if health['picture_complete'] else 'No'}

### Issues
{issues_text}

### Proposed New Threads
{proposals_text}

## Steward Action Required
{'None — system is healthy.' if health['healthy'] and health['picture_complete'] else 'See issues and proposals above.'}
"""

    with open(filepath, "w") as f:
        f.write(content)

    return filepath


def git_commit_and_push():
    """Commit loop entry + new evidence + digest and push."""
    try:
        subprocess.run(["git", "add", "-A"], cwd=REPO_ROOT, check=True, capture_output=True)
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        msg = f"Stewardship loop — {today}\n\nAutonomous daily run: ingest, digest, metrics, loop entry."
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

    # 1. Run pipeline
    print("\n[1/5] Running pipeline...")
    pipeline_results = run_pipeline()
    for name, result in pipeline_results.items():
        status = result["status"]
        print(f"  {name}: {status}")

    # 2. Snapshot metrics
    print("\n[2/5] Snapshotting metrics...")
    snapshot = snapshot_metrics()
    print(f"  Evidence: {snapshot['evidence_total']} items")
    print(f"  Sources: {snapshot['source_coverage']['ratio']} active")

    # 3. Assess health
    print("\n[3/5] Assessing health...")
    health = assess_health(snapshot, pipeline_results)
    print(f"  Healthy: {health['healthy']}")
    print(f"  Picture complete: {health['picture_complete']}")
    if health["issues"]:
        print(f"  Issues: {len(health['issues'])}")
        for issue in health["issues"]:
            print(f"    - {issue}")

    # 4. Write loop entry
    print("\n[4/5] Writing loop entry...")
    entry_path = write_loop_entry(snapshot, health, pipeline_results)
    print(f"  Written to {entry_path}")

    # 5. Commit and push
    print("\n[5/5] Committing...")
    git_commit_and_push()

    print("\n" + "=" * 60)
    if health["healthy"] and health["picture_complete"]:
        print("STEWARDSHIP: All healthy. Sleeping.")
    elif health["healthy"]:
        print("STEWARDSHIP: Healthy but picture incomplete. Proposals logged.")
    else:
        print("STEWARDSHIP: Issues detected. See loop entry.")
    print("=" * 60)

    return 0 if health["healthy"] else 1


if __name__ == "__main__":
    sys.exit(main())
