#!/usr/bin/env python3
"""Ingest Alpha Signal AI news via RSS feed."""

import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone

import feedparser

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(REPO_ROOT, "evidence", "items")

FEED_URL = "https://alphasignal.ai/feed.xml"
MAX_ITEMS = 20


def fetch_articles(max_items: int = 20) -> list:
    """Fetch recent articles from Alpha Signal RSS."""
    feed = feedparser.parse(FEED_URL)
    articles = []

    for entry in feed.entries[:max_items]:
        summary = getattr(entry, "summary", "") or getattr(entry, "description", "")
        summary = re.sub(r"<[^>]+>", "", summary).strip()[:500]

        categories = [t.term for t in getattr(entry, "tags", [])]

        article = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "alphasignal",
            "title": entry.title.strip(),
            "url": entry.link,
            "summary": summary,
            "relevance": None,
            "tags": categories if categories else ["ai", "alphasignal"],
            "cluster": None,
            "hypotheses": [],
            "direction": "neutral",
            "shared": False,
            "steward_reaction": None,
        }
        articles.append(article)

    return articles


def save_evidence(articles: list) -> int:
    """Save articles as evidence items. Returns count saved."""
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
    for article in articles:
        if article["url"] in existing_urls:
            continue
        filepath = os.path.join(EVIDENCE_DIR, f"{article['id']}.json")
        with open(filepath, "w") as f:
            json.dump(article, f, indent=2)
        saved += 1
        existing_urls.add(article["url"])

    return saved


def main():
    print("Fetching Alpha Signal RSS...")
    articles = fetch_articles(max_items=MAX_ITEMS)
    saved = save_evidence(articles)
    print(f"Alpha Signal: {len(articles)} articles found, {saved} new evidence items saved")
    return saved


if __name__ == "__main__":
    sys.exit(0 if main() >= 0 else 1)
