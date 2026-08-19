# Sources

Approved signal sources, per governance contract section 4.

| Source | Type | Cadence | How to ingest |
|--------|------|---------|---------------|
| arXiv (cs.AI, cs.CL, cs.LG) | Research papers | Daily | arXiv API — new submissions |
| GitHub Trending | Repos/tools | Daily | GitHub API / scrape trending page |
| Alpha Signal (news@alphasignal.ai) | Newsletter | Daily | Parse email or web archive |
| Dwarkesh Podcast | Long-form interview | Per episode | RSS feed + transcript scrape |
| Moonshot Podcast | Long-form interview | Per episode | RSS feed + transcript scrape |

## Adding a source

Requires a governance proposal per section 7/8 of the contract. Agent can
propose; steward approves.

## Filtering principles

1. **Importance over popularity.** A paper with 12 citations that shifts a
   paradigm matters more than one with 1200 that confirms consensus.
2. **No provocation.** If the primary value of a story is emotional reaction,
   skip it.
3. **Relevance to trajectory.** Does this item tell us something about where
   the world is *heading*, or just where it is today?
4. **Actionable or model-updating.** Does the steward need to change a belief
   or make a decision because of this? If neither, it's noise.
