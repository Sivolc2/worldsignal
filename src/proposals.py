#!/usr/bin/env python3
"""Proposal lifecycle — structured propose/approve workflow.

Proposals go through: proposed → approved/rejected → implemented/expired.
Index stored at governance/proposals/index.json.
Each proposal also gets a markdown file for human review.
"""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_config():
    config_path = os.path.join(REPO_ROOT, "governance", "steward_config.json")
    with open(config_path) as f:
        return json.load(f)


def _index_path():
    config = _load_config()
    return os.path.join(REPO_ROOT, config["proposals"]["store_path"])


def _proposals_dir():
    config = _load_config()
    return os.path.join(REPO_ROOT, config["proposals"]["proposals_dir"])


def load_index() -> dict:
    """Load the proposal index."""
    path = _index_path()
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"schema_version": 1, "proposals": [], "next_id": 1}


def save_index(index: dict):
    """Save the proposal index."""
    path = _index_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(index, f, indent=2)


def propose(title: str, what: str, why: str, evidence: str = "",
            scope: str = "in_scope", dispatch_action: str = None) -> dict:
    """Create a new proposal. Returns the proposal record.

    scope: "in_scope" | "scope_adjacent" | "out_of_scope"
    dispatch_action: if in_scope, the action type to dispatch on approval
    """
    index = load_index()
    pid = index.get("next_id", len(index["proposals"]) + 1)
    now = datetime.now(timezone.utc)
    date_str = now.strftime("%Y-%m-%d")

    slug = title.lower().replace(" ", "-")[:40]
    filename = f"{date_str}-{slug}.md"

    proposal = {
        "id": f"P{pid:03d}",
        "title": title,
        "status": "proposed",
        "scope": scope,
        "dispatch_action": dispatch_action,
        "created": now.isoformat(),
        "updated": now.isoformat(),
        "filename": filename,
        "decided_by": None,
        "decided_at": None,
    }

    md_content = f"""# Proposal {proposal['id']}: {title}

**Status:** proposed
**Scope:** {scope}
**Created:** {date_str}
**Dispatch action:** {dispatch_action or 'none'}

## What

{what}

## Why

{why}

## Evidence

{evidence or 'No specific evidence cited.'}

## Decision

_Pending steward review._
"""

    proposals_dir = _proposals_dir()
    os.makedirs(proposals_dir, exist_ok=True)
    with open(os.path.join(proposals_dir, filename), "w") as f:
        f.write(md_content)

    index["proposals"].append(proposal)
    index["next_id"] = pid + 1
    save_index(index)
    return proposal


def decide(proposal_id: str, decision: str, decided_by: str = "steward") -> dict:
    """Approve or reject a proposal.

    decision: "approved" | "rejected"
    """
    if decision not in ("approved", "rejected"):
        raise ValueError("decision must be 'approved' or 'rejected'")

    index = load_index()
    for p in index["proposals"]:
        if p["id"] == proposal_id:
            p["status"] = decision
            p["decided_by"] = decided_by
            p["decided_at"] = datetime.now(timezone.utc).isoformat()
            p["updated"] = p["decided_at"]
            save_index(index)

            md_path = os.path.join(_proposals_dir(), p["filename"])
            if os.path.exists(md_path):
                with open(md_path) as f:
                    content = f.read()
                content = content.replace(
                    "_Pending steward review._",
                    f"**{decision.upper()}** by {decided_by} on {p['decided_at'][:10]}"
                )
                content = content.replace(
                    "**Status:** proposed",
                    f"**Status:** {decision}"
                )
                with open(md_path, "w") as f:
                    f.write(content)

            return p
    raise ValueError(f"Proposal {proposal_id} not found")


def mark_implemented(proposal_id: str) -> dict:
    """Mark an approved proposal as implemented."""
    index = load_index()
    for p in index["proposals"]:
        if p["id"] == proposal_id:
            if p["status"] != "approved":
                raise ValueError(f"Cannot implement {proposal_id}: status is {p['status']}, not approved")
            p["status"] = "implemented"
            p["updated"] = datetime.now(timezone.utc).isoformat()
            save_index(index)
            return p
    raise ValueError(f"Proposal {proposal_id} not found")


def check_expired() -> list:
    """Check for proposals that have expired without a decision."""
    config = _load_config()
    index = load_index()
    expire_days = config["proposals"]["auto_expire_days"]
    now = datetime.now(timezone.utc)
    expired = []

    for p in index["proposals"]:
        if p["status"] != "proposed":
            continue
        created = datetime.fromisoformat(p["created"])
        age = (now - created).days
        if age >= expire_days:
            p["status"] = "expired"
            p["updated"] = now.isoformat()
            expired.append(p)

    if expired:
        save_index(index)
    return expired


def pending() -> list:
    """List proposals awaiting decision."""
    index = load_index()
    return [p for p in index["proposals"] if p["status"] == "proposed"]


def approved_awaiting_implementation() -> list:
    """List approved proposals not yet implemented."""
    index = load_index()
    return [p for p in index["proposals"] if p["status"] == "approved"]


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "pending":
        for p in pending():
            print(f"  {p['id']}: {p['title']} [{p['scope']}] — created {p['created'][:10]}")
    elif len(sys.argv) > 1 and sys.argv[1] == "approved":
        for p in approved_awaiting_implementation():
            action = p.get("dispatch_action", "none")
            print(f"  {p['id']}: {p['title']} — dispatch: {action}")
    else:
        index = load_index()
        by_status = {}
        for p in index["proposals"]:
            by_status.setdefault(p["status"], []).append(p)
        total = len(index["proposals"])
        print(f"Proposals: {total} total")
        for status, items in by_status.items():
            print(f"  {status}: {len(items)}")
