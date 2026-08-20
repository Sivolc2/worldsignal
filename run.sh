#!/usr/bin/env bash
# WorldSignal — full pipeline run
# Usage: ./run.sh [ingest|digest|sync|all]
# Default: all

set -euo pipefail
cd "$(dirname "$0")"

CMD="${1:-all}"

ingest() {
  echo "=== Ingesting sources ==="
  python3 src/ingest_arxiv.py &
  python3 src/ingest_github.py &
  python3 src/ingest_podcasts.py &
  python3 src/ingest_alphasignal.py &
  wait
  echo "=== Ingestion complete ==="
}

sync() {
  echo "=== Syncing to vector store ==="
  python3 src/evidence_store.py
}

digest() {
  echo "=== Generating digest ==="
  python3 src/generate_digest.py
}

case "$CMD" in
  ingest) ingest ;;
  sync)   sync ;;
  digest) digest ;;
  all)
    ingest
    sync
    digest
    ;;
  *)
    echo "Usage: ./run.sh [ingest|digest|sync|all]"
    exit 1
    ;;
esac
