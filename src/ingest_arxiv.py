#!/usr/bin/env python3
"""Ingest recent arXiv papers from cs.AI, cs.CL, cs.LG."""

import json
import os
import sys
import time
import uuid
from datetime import datetime, timezone

import feedparser

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(REPO_ROOT, "evidence", "items")

CATEGORIES = ["cs.AI", "cs.CL", "cs.LG"]
MAX_RESULTS = 30  # per category, we'll dedupe

ARXIV_API = "http://export.arxiv.org/api/query"


def fetch_recent_papers(category: str, max_results: int = 10) -> list:
    """Fetch recent papers from arXiv API for a given category."""
    query = f"cat:{category}"
    url = f"{ARXIV_API}?search_query={query}&start=0&max_results={max_results}&sortBy=submittedDate&sortOrder=descending"

    feed = feedparser.parse(url)
    papers = []
    for entry in feed.entries:
        paper = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "arxiv",
            "title": entry.title.replace("\n", " ").strip(),
            "url": entry.link,
            "summary": entry.summary.replace("\n", " ").strip()[:500],
            "relevance": None,  # filled by digest generator
            "tags": [t.term for t in getattr(entry, "tags", [])],
            "cluster": None,
            "hypotheses": [],
            "direction": "neutral",
            "shared": False,
            "steward_reaction": None,
        }
        papers.append(paper)
    return papers


def save_evidence(papers: list) -> int:
    """Save papers as evidence items. Returns count saved."""
    os.makedirs(EVIDENCE_DIR, exist_ok=True)

    # Load existing URLs to dedupe
    existing_urls = set()
    for f in os.listdir(EVIDENCE_DIR):
        if f.endswith(".json"):
            with open(os.path.join(EVIDENCE_DIR, f)) as fh:
                try:
                    existing_urls.add(json.load(fh).get("url"))
                except json.JSONDecodeError:
                    pass

    saved = 0
    for paper in papers:
        if paper["url"] in existing_urls:
            continue
        filepath = os.path.join(EVIDENCE_DIR, f"{paper['id']}.json")
        with open(filepath, "w") as f:
            json.dump(paper, f, indent=2)
        saved += 1
        existing_urls.add(paper["url"])

    return saved


def main():
    all_papers = []
    for cat in CATEGORIES:
        print(f"Fetching {cat}...")
        papers = fetch_recent_papers(cat, max_results=MAX_RESULTS)
        all_papers.extend(papers)
        time.sleep(3)  # be polite to arXiv API

    # Dedupe by URL
    seen = set()
    unique = []
    for p in all_papers:
        if p["url"] not in seen:
            seen.add(p["url"])
            unique.append(p)

    saved = save_evidence(unique)
    print(f"arXiv: {len(unique)} papers found, {saved} new evidence items saved")
    return saved


if __name__ == "__main__":
    sys.exit(0 if main() >= 0 else 1)
