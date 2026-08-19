#!/usr/bin/env python3
"""Generate the morning digest from recent evidence items using Claude API."""

import json
import os
import sys
from datetime import datetime, timezone, timedelta

import anthropic

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(REPO_ROOT, "evidence", "items")
DIGEST_DIR = os.path.join(REPO_ROOT, "digest")
MAP_FILE = os.path.join(REPO_ROOT, "map", "HYPOTHESES.md")
CONTRACT_FILE = os.path.join(REPO_ROOT, "governance", "CONTRACT.md")


def load_recent_evidence(hours: int = 48) -> list:
    """Load evidence items from the last N hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    items = []

    if not os.path.isdir(EVIDENCE_DIR):
        return items

    for fname in os.listdir(EVIDENCE_DIR):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(EVIDENCE_DIR, fname)) as f:
            try:
                item = json.load(f)
            except json.JSONDecodeError:
                continue
        try:
            ts = datetime.fromisoformat(item["timestamp"])
            if ts > cutoff:
                items.append(item)
        except (KeyError, ValueError):
            items.append(item)  # include if we can't parse timestamp

    return items


def load_current_hypotheses() -> str:
    """Load the current hypothesis map."""
    if os.path.exists(MAP_FILE):
        with open(MAP_FILE) as f:
            return f.read()
    return "No hypotheses yet."


def generate_digest(evidence: list, hypotheses: str) -> str:
    """Use Claude to synthesize evidence into a morning digest."""
    client = anthropic.Anthropic()

    evidence_text = "\n\n".join(
        f"[{i['source']}] {i['title']}\n{i['url']}\n{i['summary']}"
        for i in evidence
    )

    prompt = f"""You are WorldSignal, a daily intelligence digest for a startup founder
focused on AI, autonomous systems, and post-labor economics.

Your job is to produce a morning digest that leaves the reader feeling:
- ORIENTED: "I know where things are flowing"
- INSPIRED: "I see where we're heading next"
- NOT STRESSED: avoid alarmism, provocation, or anxiety about things they can't change

## Filtering principles
- Importance over popularity. A quiet paradigm shift matters more than a loud launch.
- No provocation. If the primary value is emotional reaction, skip it.
- Relevance to trajectory. What does this tell us about where the world is HEADING?
- Actionable or model-updating. Should the reader change a belief or make a decision?

## Current hypothesis map
{hypotheses}

## Today's evidence ({len(evidence)} items)
{evidence_text}

## Output format
Produce a markdown digest with:

1. **The Current** (2-3 sentences) — the overall flow/direction you sense from today's evidence
2. **Signals** (3-7 items) — the most important items, each with:
   - One-line summary
   - "So what": why this matters for the reader's worldview or startup
   - Source link
3. **Trajectory Update** — any hypotheses that strengthened, weakened, or emerged
4. **Spark** — one item chosen specifically for generative energy / inspiration

Keep the entire digest under 500 words. Write in a calm, clear, forward-looking tone.
No hype. No fear. Just clarity about where things are flowing."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1500,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text


def save_digest(content: str) -> str:
    """Save digest to file, return filepath."""
    os.makedirs(DIGEST_DIR, exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    filepath = os.path.join(DIGEST_DIR, f"{today}.md")

    header = f"# WorldSignal — {today}\n\n"
    with open(filepath, "w") as f:
        f.write(header + content)

    return filepath


def main():
    evidence = load_recent_evidence(hours=48)
    if not evidence:
        print("No recent evidence to digest. Run ingestion first.")
        return 1

    print(f"Generating digest from {len(evidence)} evidence items...")
    hypotheses = load_current_hypotheses()
    digest = generate_digest(evidence, hypotheses)

    filepath = save_digest(digest)
    print(f"Digest saved to {filepath}")
    print("\n" + "=" * 60)
    print(digest)
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
