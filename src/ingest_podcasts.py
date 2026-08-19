#!/usr/bin/env python3
"""Ingest recent episodes from Dwarkesh and Moonshot podcasts via RSS."""

import json
import os
import sys
import uuid
from datetime import datetime, timezone

import feedparser

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(REPO_ROOT, "evidence", "items")

FEEDS = {
    "dwarkesh": "https://api.substack.com/feed/podcast/1084858.rss",
    "moonshot": "https://feeds.simplecast.com/4TzR5MpK",
}

MAX_EPISODES = 5  # per feed


def fetch_episodes(name: str, url: str, max_episodes: int = 5) -> list:
    """Fetch recent podcast episodes from RSS feed."""
    feed = feedparser.parse(url)
    episodes = []

    for entry in feed.entries[:max_episodes]:
        published = getattr(entry, "published", None) or getattr(entry, "updated", "")
        summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
        # Strip HTML tags from summary
        import re
        summary = re.sub(r"<[^>]+>", "", summary).strip()[:500]

        episode = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": name,
            "title": entry.title.strip(),
            "url": entry.link,
            "summary": summary,
            "relevance": None,
            "tags": [name, "podcast"],
            "cluster": None,
            "hypotheses": [],
            "direction": "neutral",
            "shared": False,
            "steward_reaction": None,
        }
        episodes.append(episode)

    return episodes


def save_evidence(episodes: list) -> int:
    """Save episodes as evidence items. Returns count saved."""
    os.makedirs(EVIDENCE_DIR, exist_ok=True)

    existing_urls = set()
    for f in os.listdir(EVIDENCE_DIR):
        if f.endswith(".json"):
            with open(os.path.join(EVIDENCE_DIR, f)) as fh:
                try:
                    existing_urls.add(json.load(fh).get("url"))
                except json.JSONDecodeError:
                    pass

    saved = 0
    for ep in episodes:
        if ep["url"] in existing_urls:
            continue
        filepath = os.path.join(EVIDENCE_DIR, f"{ep['id']}.json")
        with open(filepath, "w") as f:
            json.dump(ep, f, indent=2)
        saved += 1
        existing_urls.add(ep["url"])

    return saved


def main():
    all_episodes = []
    for name, url in FEEDS.items():
        print(f"Fetching {name} podcast RSS...")
        episodes = fetch_episodes(name, url)
        all_episodes.extend(episodes)
        print(f"  Found {len(episodes)} episodes")

    saved = save_evidence(all_episodes)
    print(f"Podcasts: {len(all_episodes)} episodes found, {saved} new evidence items saved")
    return saved


if __name__ == "__main__":
    sys.exit(0 if main() >= 0 else 1)
