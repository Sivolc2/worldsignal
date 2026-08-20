#!/usr/bin/env python3
"""Hypothesis store — structured CRUD for the hypothesis map.

JSON backing store at map/hypotheses.json, rendered to map/HYPOTHESES.md.
All mutations go through this module to keep the two in sync.
"""

import json
import os
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_config():
    config_path = os.path.join(REPO_ROOT, "governance", "steward_config.json")
    with open(config_path) as f:
        return json.load(f)


def _store_path():
    config = _load_config()
    return os.path.join(REPO_ROOT, config["hypotheses"]["store_path"])


def _render_path():
    config = _load_config()
    return os.path.join(REPO_ROOT, config["hypotheses"]["render_path"])


def load() -> dict:
    """Load the hypothesis store. Returns {hypotheses: [...], metadata: {...}}."""
    path = _store_path()
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"schema_version": 1, "hypotheses": [], "next_id": 1}


def save(store: dict):
    """Save the hypothesis store and render markdown."""
    path = _store_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(store, f, indent=2)
    render(store)


def add(title: str, claim: str, evidence_for: list = None,
        evidence_against: list = None, implications: str = "") -> dict:
    """Add a new hypothesis. Returns the created hypothesis."""
    store = load()
    hid = store.get("next_id", len(store["hypotheses"]) + 1)
    now = datetime.now(timezone.utc).isoformat()

    hypothesis = {
        "id": f"H{hid}",
        "title": title,
        "claim": claim,
        "status": "emerged",
        "evidence_for": evidence_for or [],
        "evidence_against": evidence_against or [],
        "implications": implications,
        "created": now,
        "last_updated": now,
    }

    store["hypotheses"].append(hypothesis)
    store["next_id"] = hid + 1
    save(store)
    return hypothesis


def update(hypothesis_id: str, **kwargs) -> dict:
    """Update fields on an existing hypothesis. Returns updated hypothesis."""
    store = load()
    for h in store["hypotheses"]:
        if h["id"] == hypothesis_id:
            for key, value in kwargs.items():
                if key in h:
                    h[key] = value
            h["last_updated"] = datetime.now(timezone.utc).isoformat()
            save(store)
            return h
    raise ValueError(f"Hypothesis {hypothesis_id} not found")


def add_evidence(hypothesis_id: str, side: str, date: str, source: str,
                 summary: str, link: str = "") -> dict:
    """Add evidence for or against a hypothesis."""
    if side not in ("for", "against"):
        raise ValueError("side must be 'for' or 'against'")

    store = load()
    for h in store["hypotheses"]:
        if h["id"] == hypothesis_id:
            entry = {"date": date, "source": source, "summary": summary, "link": link}
            h[f"evidence_{side}"].append(entry)
            h["last_updated"] = datetime.now(timezone.utc).isoformat()
            save(store)
            return h
    raise ValueError(f"Hypothesis {hypothesis_id} not found")


def transition(hypothesis_id: str, new_status: str) -> dict:
    """Transition a hypothesis to a new status."""
    valid = {"emerged", "active", "strengthening", "weakening", "retired"}
    if new_status not in valid:
        raise ValueError(f"Invalid status: {new_status}. Must be one of {valid}")
    return update(hypothesis_id, status=new_status)


def check_staleness() -> list:
    """Check for hypotheses that need attention based on config thresholds."""
    config = _load_config()
    store = load()
    now = datetime.now(timezone.utc)
    alerts = []

    weaken_days = config["hypotheses"]["auto_weaken_if_no_evidence_days"]
    retire_days = config["hypotheses"]["auto_retire_if_weakened_days"]

    for h in store["hypotheses"]:
        if h["status"] == "retired":
            continue

        last = datetime.fromisoformat(h["last_updated"])
        age_days = (now - last).days

        if h["status"] == "weakening" and age_days >= retire_days:
            alerts.append({
                "hypothesis": h["id"],
                "action": "auto_retire",
                "reason": f"Weakened for {age_days} days (threshold: {retire_days})",
            })
        elif h["status"] in ("emerged", "active", "strengthening") and age_days >= weaken_days:
            alerts.append({
                "hypothesis": h["id"],
                "action": "auto_weaken",
                "reason": f"No new evidence for {age_days} days (threshold: {weaken_days})",
            })

    return alerts


def get(hypothesis_id: str) -> dict:
    """Get a single hypothesis by ID."""
    store = load()
    for h in store["hypotheses"]:
        if h["id"] == hypothesis_id:
            return h
    raise ValueError(f"Hypothesis {hypothesis_id} not found")


def list_active() -> list:
    """List all non-retired hypotheses."""
    store = load()
    return [h for h in store["hypotheses"] if h["status"] != "retired"]


def detect_conflicts(new_evidence: dict) -> list:
    """Check if new evidence conflicts with any active hypothesis.
    Returns list of conflict descriptions."""
    store = load()
    conflicts = []
    tags = set(new_evidence.get("tags", []))
    title_words = set(new_evidence.get("title", "").lower().split())

    for h in store["hypotheses"]:
        if h["status"] == "retired":
            continue
        claim_words = set(h["claim"].lower().split())
        overlap = title_words & claim_words
        if len(overlap) >= 3:
            conflicts.append({
                "hypothesis": h["id"],
                "title": h["title"],
                "overlap_words": list(overlap),
                "note": "Potential relevance detected — manual review recommended",
            })

    return conflicts


def render(store: dict = None):
    """Render the hypothesis store to markdown."""
    if store is None:
        store = load()

    lines = [
        "# Hypothesis Map",
        "",
        "> A living document. Each hypothesis represents a claim about where the world",
        "> is heading. Evidence accumulates for or against each. New hypotheses emerge",
        "> from the evidence clusters. This is the product.",
        "",
        "## How to read this map",
        "",
        "- **Emerged** — new hypothesis surfaced from evidence clustering",
        "- **Active** — currently accumulating evidence",
        "- **Strengthening** — recent evidence supports this",
        "- **Weakening** — recent evidence challenges this",
        "- **Retired** — enough evidence to confirm or reject",
        "",
        "---",
        "",
        "## Hypotheses",
        "",
    ]

    status_emoji = {
        "emerged": "",
        "active": "",
        "strengthening": "",
        "weakening": "",
        "retired": "(retired) ",
    }

    active = [h for h in store["hypotheses"] if h["status"] != "retired"]
    retired = [h for h in store["hypotheses"] if h["status"] == "retired"]

    for h in active:
        lines.append(f"### {h['id']}: {h['title']}")
        lines.append("")
        lines.append(f"**Claim:** {h['claim']}")
        lines.append(f"**Status:** {h['status']}")
        lines.append("**Evidence for:**")
        if h["evidence_for"]:
            for e in h["evidence_for"]:
                link_part = f" [link]({e['link']})" if e.get("link") else ""
                lines.append(f"- [{e['date']}] [{e['source']}] {e['summary']}{link_part}")
        else:
            lines.append("- (none yet)")
        lines.append("**Evidence against:**")
        if h["evidence_against"]:
            for e in h["evidence_against"]:
                link_part = f" [link]({e['link']})" if e.get("link") else ""
                lines.append(f"- [{e['date']}] [{e['source']}] {e['summary']}{link_part}")
        else:
            lines.append("- (none yet)")
        lines.append(f"**Last updated:** {h['last_updated'][:10]}")
        if h.get("implications"):
            lines.append(f"**Implications for steward:** {h['implications']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    if retired:
        lines.append("## Retired Hypotheses")
        lines.append("")
        for h in retired:
            lines.append(f"### {h['id']}: {h['title']} (retired)")
            lines.append("")
            lines.append(f"**Claim:** {h['claim']}")
            lines.append(f"**Retired:** {h['last_updated'][:10]}")
            lines.append("")

    path = _render_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        f.write("\n".join(lines))


def migrate_from_markdown():
    """One-time migration: parse existing HYPOTHESES.md into the JSON store."""
    render_path = _render_path()
    if not os.path.exists(render_path):
        return

    store = load()
    if store["hypotheses"]:
        return

    with open(render_path) as f:
        content = f.read()

    import re
    blocks = re.split(r"^### (H\d+):", content, flags=re.MULTILINE)

    hid = 0
    for i in range(1, len(blocks), 2):
        hypothesis_id = blocks[i]
        body = blocks[i + 1]

        title_match = re.match(r"\s*(.+?)(?:\s*\(retired\))?\s*\n", body)
        title = title_match.group(1).strip() if title_match else "Unknown"

        claim_match = re.search(r"\*\*Claim:\*\*\s*(.+)", body)
        claim = claim_match.group(1).strip() if claim_match else ""

        status_match = re.search(r"\*\*Status:\*\*\s*(\w+)", body)
        status = status_match.group(1).strip() if status_match else "emerged"

        implications_match = re.search(r"\*\*Implications for steward:\*\*\s*(.+)", body)
        implications = implications_match.group(1).strip() if implications_match else ""

        evidence_for = []
        for_section = re.search(r"\*\*Evidence for:\*\*\n((?:- .+\n)*)", body)
        if for_section:
            for line in for_section.group(1).strip().split("\n"):
                ev_match = re.match(
                    r"- \[(\d{4}-\d{2}-\d{2})\] \[(\w+)\] (.+?)(?:\s*\[link\]\((.+?)\))?$",
                    line.strip()
                )
                if ev_match:
                    evidence_for.append({
                        "date": ev_match.group(1),
                        "source": ev_match.group(2),
                        "summary": ev_match.group(3).strip(),
                        "link": ev_match.group(4) or "",
                    })

        evidence_against = []
        against_section = re.search(r"\*\*Evidence against:\*\*\n((?:- .+\n)*)", body)
        if against_section:
            for line in against_section.group(1).strip().split("\n"):
                ev_match = re.match(
                    r"- \[(\d{4}-\d{2}-\d{2})\] \[(\w+)\] (.+?)(?:\s*\[link\]\((.+?)\))?$",
                    line.strip()
                )
                if ev_match:
                    evidence_against.append({
                        "date": ev_match.group(1),
                        "source": ev_match.group(2),
                        "summary": ev_match.group(3).strip(),
                        "link": ev_match.group(4) or "",
                    })

        num = int(hypothesis_id[1:])
        hid = max(hid, num)

        store["hypotheses"].append({
            "id": hypothesis_id,
            "title": title,
            "claim": claim,
            "status": status,
            "evidence_for": evidence_for,
            "evidence_against": evidence_against,
            "implications": implications,
            "created": "2026-08-19T00:00:00+00:00",
            "last_updated": "2026-08-19T00:00:00+00:00",
        })

    store["next_id"] = hid + 1
    save(store)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        migrate_from_markdown()
        store = load()
        print(f"Migrated {len(store['hypotheses'])} hypotheses")
    else:
        store = load()
        active = list_active()
        print(f"Hypothesis store: {len(active)} active, {len(store['hypotheses']) - len(active)} retired")
        for h in active:
            ef = len(h["evidence_for"])
            ea = len(h["evidence_against"])
            print(f"  {h['id']}: {h['title']} [{h['status']}] (+{ef}/-{ea})")
        alerts = check_staleness()
        if alerts:
            print(f"\nAlerts: {len(alerts)}")
            for a in alerts:
                print(f"  {a['hypothesis']}: {a['action']} — {a['reason']}")
