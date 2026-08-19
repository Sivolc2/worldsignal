#!/usr/bin/env python3
"""Ingest GitHub trending repositories (AI/ML focused)."""

import json
import os
import re
import sys
import uuid
from datetime import datetime, timezone

import requests

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(REPO_ROOT, "evidence", "items")

# GitHub trending doesn't have an official API — use the search API instead
# to find recently created repos with high star velocity
GITHUB_API = "https://api.github.com"
TOPICS = ["artificial-intelligence", "llm", "machine-learning", "deep-learning", "agents"]


def fetch_trending_repos(topic: str, max_results: int = 10) -> list:
    """Fetch recently popular repos for a topic via GitHub search API."""
    headers = {}
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"

    url = f"{GITHUB_API}/search/repositories"
    params = {
        "q": f"topic:{topic} stars:>50 pushed:>2026-08-12",
        "sort": "stars",
        "order": "desc",
        "per_page": max_results,
    }

    resp = requests.get(url, params=params, headers=headers, timeout=30)
    if resp.status_code != 200:
        print(f"GitHub API error for topic {topic}: {resp.status_code}")
        return []

    repos = []
    for item in resp.json().get("items", []):
        repo = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": "github",
            "title": f"{item['full_name']}: {item.get('description', 'No description')}"[:200],
            "url": item["html_url"],
            "summary": f"Stars: {item['stargazers_count']}, "
                        f"Language: {item.get('language', 'unknown')}, "
                        f"Topics: {', '.join(item.get('topics', [])[:5])}. "
                        f"{item.get('description', '')}",
            "relevance": None,
            "tags": item.get("topics", [])[:10],
            "cluster": None,
            "hypotheses": [],
            "direction": "neutral",
            "shared": False,
            "steward_reaction": None,
        }
        repos.append(repo)

    return repos


def save_evidence(repos: list) -> int:
    """Save repos as evidence items. Returns count saved."""
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
    for repo in repos:
        if repo["url"] in existing_urls:
            continue
        filepath = os.path.join(EVIDENCE_DIR, f"{repo['id']}.json")
        with open(filepath, "w") as f:
            json.dump(repo, f, indent=2)
        saved += 1
        existing_urls.add(repo["url"])

    return saved


def main():
    all_repos = []
    for topic in TOPICS:
        print(f"Fetching GitHub trending: {topic}...")
        repos = fetch_trending_repos(topic)
        all_repos.extend(repos)

    # Dedupe by URL
    seen = set()
    unique = []
    for r in all_repos:
        if r["url"] not in seen:
            seen.add(r["url"])
            unique.append(r)

    saved = save_evidence(unique)
    print(f"GitHub: {len(unique)} repos found, {saved} new evidence items saved")
    return saved


if __name__ == "__main__":
    sys.exit(0 if main() >= 0 else 1)
