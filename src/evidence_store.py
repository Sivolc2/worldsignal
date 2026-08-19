#!/usr/bin/env python3
"""Evidence store: vectorize evidence items and manage clusters via ChromaDB."""

import json
import os
import sys

import chromadb

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EVIDENCE_DIR = os.path.join(REPO_ROOT, "evidence", "items")
CHROMA_DIR = os.path.join(REPO_ROOT, "evidence", "chromadb")
CLUSTERS_DIR = os.path.join(REPO_ROOT, "evidence", "clusters")


def get_client():
    """Get persistent ChromaDB client."""
    return chromadb.PersistentClient(path=CHROMA_DIR)


def get_collection(client):
    """Get or create the evidence collection."""
    return client.get_or_create_collection(
        name="evidence",
        metadata={"description": "WorldSignal evidence point cloud"},
    )


def load_evidence_items() -> list:
    """Load all evidence JSON files."""
    items = []
    if not os.path.isdir(EVIDENCE_DIR):
        return items
    for fname in os.listdir(EVIDENCE_DIR):
        if not fname.endswith(".json"):
            continue
        with open(os.path.join(EVIDENCE_DIR, fname)) as f:
            try:
                items.append(json.load(f))
            except json.JSONDecodeError:
                continue
    return items


def sync_to_vectordb():
    """Sync evidence items into ChromaDB. Idempotent by evidence ID."""
    client = get_client()
    collection = get_collection(client)

    items = load_evidence_items()
    if not items:
        print("No evidence items to sync")
        return 0

    # Get existing IDs
    existing = set(collection.get()["ids"])

    new_items = [i for i in items if i["id"] not in existing]
    if not new_items:
        print(f"All {len(items)} items already in vector store")
        return 0

    # Prepare documents for embedding (ChromaDB handles embedding internally)
    ids = [i["id"] for i in new_items]
    documents = [
        f"{i['title']}. {i['summary']}" for i in new_items
    ]
    metadatas = [
        {
            "source": i["source"],
            "url": i["url"],
            "timestamp": i["timestamp"],
            "tags": json.dumps(i.get("tags", [])),
        }
        for i in new_items
    ]

    collection.add(ids=ids, documents=documents, metadatas=metadatas)
    print(f"Added {len(new_items)} new items to vector store (total: {len(existing) + len(new_items)})")
    return len(new_items)


def query_similar(text: str, n_results: int = 10) -> list:
    """Query the evidence store for items similar to the given text."""
    client = get_client()
    collection = get_collection(client)
    results = collection.query(query_texts=[text], n_results=n_results)
    return results


def get_all_evidence_summary() -> dict:
    """Return summary stats about the evidence store."""
    client = get_client()
    collection = get_collection(client)
    count = collection.count()

    items = load_evidence_items()
    sources = {}
    for i in items:
        src = i.get("source", "unknown")
        sources[src] = sources.get(src, 0) + 1

    return {"total_items": count, "by_source": sources}


def main():
    """Sync all evidence to vector store and print summary."""
    added = sync_to_vectordb()
    summary = get_all_evidence_summary()
    print(f"\nEvidence store: {summary['total_items']} items")
    for src, count in sorted(summary["by_source"].items()):
        print(f"  {src}: {count}")
    return added


if __name__ == "__main__":
    main()
