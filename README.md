# Engineering Memory Benchmark

**Don't Choose Your Memory Tool — Layer Them.**

An empirical study comparing retrieval methods for LLM-generated engineering artifacts (Architecture Decision Records). Tests 5 retrieval conditions + 3 model tiers on a production K8s engineering platform with 3 months of accumulated engineering history.

## Key Finding

Layered retrieval (typed discovery → semantic context → file verification) scores **0.954** on a 5-dimension rubric, beating every individual method:

| Condition | Mean Score | Cost/ADR |
|---|---|---|
| A — No memory | 0.572 | ~$1.00 |
| B — Semantic search (Qdrant) | 0.720 | ~$1.50 |
| C — Grep + file read | 0.918 | ~$1.80 |
| D — Typed-fact retrieval only | 0.650 | ~$1.20 |
| **E — All three layered** | **0.954** | **~$2.50** |

Sonnet + layered retrieval (0.88) matches Opus + layered (0.91) at 5x less cost. Haiku fails on complex topics (0.35) despite rich context — there's a minimum model capability floor.

## Four Findings

1. **Retrieval methods compose super-linearly** — E > max(B,C,D) because each layer catches errors the others introduce
2. **Semantic search can hurt below baseline** — returns adjacent-but-wrong context that the LLM trusts
3. **Extraction quality is the binding constraint** — typed retrieval is only as good as what was extracted
4. **Model matters less than retrieval** — Sonnet+E ≈ Opus+E, but Haiku+E fails (capability floor between Haiku and Sonnet)

## Repository Structure

```
├── PAPER.md                    Full paper (3,700 words)
├── data/
│   ├── ground-truth/           5 real ADRs from production (gold standard)
│   ├── condition-a/            Generated with no memory
│   ├── condition-b/            Generated with semantic search only
│   ├── condition-c/            Generated with grep + file read
│   ├── condition-d/            Generated with typed memory tools only
│   ├── condition-e/            Generated with all three layered (Opus)
│   ├── condition-e-sonnet/     Generated with layered retrieval (Sonnet)
│   └── condition-e-haiku/      Generated with layered retrieval (Haiku)
├── scores/                     23 JSON score files (per-claim decomposition)
├── rubric/
│   └── locked-rubric-v1.md     Immutable scoring rubric (5 dimensions)
├── scripts/
│   └── score_with_gpt4o.py     GPT-4o dual-judge scoring script
├── calibration-manifest.json   15 calibration artifacts
└── LICENSE                     CC-BY-4.0
```

## Methodology

- **Rubric**: 5 dimensions (technical correctness, citation, completeness, conciseness, pattern adoption), locked per RULERS methodology (arXiv 2601.08654)
- **Judge**: Claude Opus 4.7 (primary) + GPT-4o (dual-judge validation, 100% rank agreement on top condition)
- **Isolation**: Each condition runs in a fresh LLM session with only the tools that condition allows
- **Evidence trail**: Every score JSON includes per-claim reasoning explaining why each score was given

## The 3-Step Workflow (for practitioners)

```
Step 1 — DISCOVERY (typed memory)
  "What decisions/problems exist about this topic?"
  → recall_decisions(topic=X), find_problems(topic=X)

Step 2 — CONTEXT (semantic search)
  "What else is related?"
  → auto_search_vault(query=X)

Step 3 — VERIFICATION (file access)
  "Do the facts check out against source?"
  → grep + read the actual files
```

Skip layers only for trivial lookups. The full workflow costs 5% more than grep alone but consistently produces better output.

## Platform

Built on [Rootweaver](https://gitlab.com/ryanduffy.uk/rootweaver-platform) — a typed engineering-memory platform running on single-node K3s (RTX 4080). 248 sessions, 2,748 typed facts, 6,135 artifacts, 376 v2-quality enriched facts across 3 months of real engineering work.

## Citation

```
Duffy, R. G. (2026). Don't Choose Your Memory Tool — Layer Them: How Typed
Discovery + Semantic Context + File Verification Produces Near-Human Engineering
Artifacts. https://github.com/rduffyuk/engineering-memory-benchmark
```

## Author

**Ryan G. Duffy** — SRE, AI-orchestration practitioner
- ORCID: [0009-0009-6464-0617](https://orcid.org/0009-0009-6464-0617)
- Blog: [rduffy.uk](https://blog.rduffy.uk)
- Email: rduffyuk@gmail.com

## License

CC-BY-4.0 — use freely with attribution.
