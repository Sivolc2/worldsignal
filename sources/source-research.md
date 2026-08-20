# Source Research — 2026-08-19

Findings from browsing each target source to validate ingestion approach.

## Alpha Signal (alphasignal.ai)

- **Web archive**: 1118 articles at time of research
- **Topic filters**: AGENTS, API, LLMS, OPEN SOURCE, REASONING, RESEARCH, ROBOTICS, VISION
- **RSS feed**: `https://alphasignal.ai/feed.xml` (100 entries) — XML with categories per article
- **Atom feed**: `https://alphasignal.ai/atom.xml` (alternative)
- **Sample articles**:
  - "Does Self-Improvement Still Work on an Engineered Agent Harness?"
  - "Cerebras CS-4 Hits 30x Faster Inference"
  - "Anthropic's Claude Designs Drug-Binding Proteins"
  - "Z.ai's GLM-5.3 Tops Open-Weights Leaderboard"
- **Ingestion**: RSS feed works cleanly with feedparser. Categories map to tags.
- **Script**: `src/ingest_alphasignal.py` — 20 items per run

## Dwarkesh Podcast (dwarkesh.com → Substack)

- **Platform**: Migrated to Substack (dwarkesh.substack.com)
- **Original broken URL**: `https://api.substack.com/feed/podcast/1084858.rss` — returned XML parse error
- **Working URL**: `https://api.substack.com/feed/podcast/69345.rss` — 136 entries
- **Discovery method**: Browsed dwarkesh.com, inspected `<link rel="alternate">` tag in page source
- **Sample episodes**:
  - "Ryan Greenblatt – What happens once AI can automate AI research?"
  - "8 Predictions for the Era of Continual Learning"
  - "Why smarter AI models could drive up compute prices 10x"
- **Ingestion**: Standard RSS via feedparser. Summaries available in HTML (stripped to text).
- **Script**: `src/ingest_podcasts.py` — 5 episodes per run

## Moonshot Podcast

- **RSS feed**: `https://feeds.megaphone.fm/moonshot` — 19 episodes, RSS 2.0 with iTunes extensions
- **Host**: Astro Teller, from X/Alphabet's Moonshot Factory
- **Note**: Entries have no `link` attribute, only `id` (UUID) and audio `enclosure`. Ingester falls back to `id` for URL field.
- **Sample episodes**:
  - "The Moonshot Mindset with Adam Savage and Sergey Brin"
- **Ingestion**: feedparser works after handling missing `link`. 5 episodes per run.
- **Script**: `src/ingest_podcasts.py`

## GitHub Trending

- **Browsed**: github.com/trending
- **Current trending repos** (at time of browse):
  - MoneyPrinterTurbo, OpenViking, munder-difflin, Anthropic-Cybersecurity-Skills, nautilus_trader, superpowers, omlx, immich
- **Ingestion**: GitHub search API with topics: artificial-intelligence, llm, machine-learning, deep-learning, agents
- **Script**: `src/ingest_github.py` — scans 5 topics, deduplicates

## arXiv

- **Categories**: cs.AI, cs.CL, cs.LG
- **Ingestion**: arXiv RSS/Atom API via feedparser
- **Script**: `src/ingest_arxiv.py` — 72 papers typical daily yield

## Pipeline Status After Research

| Source | Status | Items |
|--------|--------|-------|
| arXiv | Active | 72 |
| GitHub | Active | 36 |
| Alpha Signal | Active (new) | 20 |
| Dwarkesh | Active (fixed) | 5 |
| Moonshot | Active (new) | 5 |
| **Total** | **5/5** | **138** |
