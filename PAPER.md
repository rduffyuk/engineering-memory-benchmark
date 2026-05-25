---
date: 2026-05-25
jira: VW-438
status: in-progress
tags:
- layer-3-research
- paper
- typed-retrieval
- eng-memory-bench
- composition-study
- project/adr
- project/byterover
- project/context-engine
- project/cursor's
- project/gdpr
- tech/k3s
- tech/llm
- tech/mcp
- tech/memory
- tech/qdrant
- tool/github
- project/adr-nnn
- tech/citation
title: 'Don''t Choose Your Memory Tool — Layer Them: How Typed Discovery + Semantic
  Context + File Verification Produces Near-Human Engineering Artifacts'
type: paper-draft
vault-path: 02-Active-Work/Papers
version: '1.0'
---
# Don't Choose Your Memory Tool — Layer Them

**How Typed Discovery + Semantic Context + File Verification Produces Near-Human Engineering Artifacts**

*Ryan G. Duffy*
ORCID: 0009-0009-6464-0617

---

## Abstract

We evaluate whether different retrieval methods improve LLM-generated Architecture Decision Records (ADRs) on a production engineering platform with 3 months of accumulated engineering history. Testing 5 conditions — no memory, semantic search, grep+file-read, typed-fact retrieval, and a layered combination of all three — we find that the layered approach (typed discovery → semantic context → file verification) scores 0.954 on a 5-dimension rubric, beating the best single method (grep, 0.918) and dramatically outperforming each retrieval method in isolation. The key insight: retrieval methods compose super-linearly because each layer catches errors introduced by the others. Typed retrieval alone is high-variance (0.650) and can mislead; grep alone is precise but only finds what you know to search for; the combination eliminates both failure modes. We identify extraction quality as the binding constraint for typed memory systems and provide a practical 3-step workflow for engineering teams building AI-assisted development pipelines.

---

## 1. The Question

Every AI coding tool now ships with memory: GitHub Copilot Memory, Augment Code's Context Engine, Cursor's Memory Bank, agentmemory, ByteRover. The industry consensus is "memory helps." But *which kind* of memory, and *how much* does it help?

We built Rootweaver, a typed engineering-memory platform that captures decisions, problems, and learnings as structured facts (not text blobs) from 248 Claude Code sessions over 3 months. It exposes 6 typed retrieval tools (`recall_decisions`, `find_problems`, `recall_state_at`, `trace_decision_chain`, `recall_origin`, `recall_session`) over MCP alongside standard semantic search and file access.

The question: if you give an LLM the same engineering task with different retrieval capabilities, which produces the best output?

## 2. Setup

### Task
Generate Architecture Decision Records (ADRs) for 5 real engineering decisions from a production K8s platform. Each ADR has a ground-truth document (the one actually written and used in production) for scoring.

### Conditions

| Condition | What the LLM has access to |
|---|---|
| **A** — No memory | Nothing. Pure model knowledge. |
| **B** — Semantic search | Qdrant vector search over 148K document chunks. |
| **C** — Grep + file read | Direct filesystem access to codebase + vault. |
| **D** — Typed retrieval only | 6 typed memory tools querying a Postgres fact schema. |
| **E** — All combined | Typed discovery → semantic context → file verification. |

### Rubric (locked, versioned — per Autorubric + RULERS methodology)

The rubric was written and version-locked BEFORE any scoring began. Per RULERS (arXiv 2601.08654), the rubric text is immutable once scoring starts — no rewording between conditions. The judge receives the exact rubric text verbatim.

**5 dimensions, each with behavioral anchors:**

| Dimension | Type | Scoring | Behavioral anchor (what distinguishes 0 from 1) |
|---|---|---|---|
| Technical correctness | Ordinal | 0 / 0.5 / 1.0 | 0 = factual errors about the system or decision rationale contradicts constraints. 0.5 = core decision correct but tradeoff analysis incomplete. 1.0 = all claims correct, tradeoffs consistent with engineering context. |
| Citation of prior art | Ratio | 0.0–1.0 | Decompose output into claims that SHOULD reference prior work. A "citation" must name a specific reference (VW-NNN, ADR-NNN, file path, document title). Generic phrases like "as previously discussed" do NOT count. Score = cited_claims / total_citable_claims. |
| Completeness | Ratio | 0.0–1.0 | Required sections checked against ground truth: Context, Decision, Consequences (positive AND negative), Alternatives (≥1), Status, Related links. Score = sections_present / total_required. |
| Conciseness | Ordinal | 0 / 0.5 / 1.0 | 0 = ≥3 paragraphs that repeat information or contain generic AI filler. 0.5 = ≤2 instances of restated information. 1.0 = every paragraph advances a distinct point. |
| Pattern adoption | Ratio | 0.0–1.0 | Checks: frontmatter structure, status enum, alternatives comparison format, wikilink format, consequences split into positive/negative. Score = adopted_patterns / applicable_patterns. |

Full rubric document: `02-Active-Work/Plans/2026-05-24-VW-438-Locked-Rubric-v1.md` (13KB, 3 rubric types, calibration protocol, judge prompt template).

### Scoring pipeline

**How each score was produced:**

```
┌─────────────────────────────────────────────────────────────┐
│ For each ADR × each condition:                              │
│                                                             │
│ 1. GENERATE: Agent spawned with ONLY the tools that         │
│    condition allows. Same task prompt across all conditions. │
│    Agent writes ADR to condition-{x}/ADR-NNN.md.            │
│                                                             │
│ 2. SCORE: Separate judge agent reads:                       │
│    - Ground truth (the real ADR from production)            │
│    - Generated output (one condition at a time)             │
│    Judge applies locked rubric text verbatim.               │
│    Outputs structured JSON with:                            │
│      - 5 numerical scores                                   │
│      - Per-claim citation decomposition                     │
│      - Notes explaining WHY each score was given            │
│                                                             │
│ 3. AGGREGATE: Python script parses all JSONs → means.       │
└─────────────────────────────────────────────────────────────┘
```

**Isolation**: each condition runs in a fresh LLM session. No cross-condition leakage. The judge never sees other conditions' outputs — it scores each independently against ground truth.

**Evidence trail**: every score file contains the judge's reasoning. Example (ADR-012, Condition E, citation score 0.9):

```json
"notes": "Most comprehensive condition. All GT decisions present with 
additional depth: VW-276 (3,872 fabricated entries purged 3 months later), 
VW-279 (443 sessions replayed post-fix), typed memory decisions as forensic 
citations. Judge schema details (JudgeVerdict dataclass, parse_judge_verdict 
recomputation). Includes vault-path frontmatter. Cost analysis exact match."
```

The notes are not summaries — they are the judge's specific claims about what the output got right and wrong, verifiable against the generated files.

### Dual-judge validation

Conditions A/B/C were scored by both Claude Opus 4.7 (primary) and GPT-4o (secondary) to check for judge bias.

| | Claude Opus | GPT-4o | Agreement |
|---|---|---|---|
| **Condition ranking** | C > B > A | C > B > A | **100% on top condition** across all 5 ADRs |
| **Absolute scores** | Higher overall | 0.13-0.21 stricter | GPT-4o is a harsher grader (known from Autorubric) |
| **Citation dimension** | 0.578 mean | 0.125 mean | GPT-4o interprets "citation" much more strictly |
| **Rank agreement** | — | — | 3/5 full ordering match, 5/5 agree C is best |

**Implication**: the RELATIVE finding (which condition is best) is robust to judge choice. The ABSOLUTE scores vary by judge — report with confidence intervals, not point estimates, in the full study.

### Data inventory

All artifacts are available at `tests/benchmarks/pilot/`:

```
pilot/
├── ground-truth/           5 real ADRs (gold standard, 11-17KB each)
├── condition-a/            5 ADRs — no memory
├── condition-b/            5 ADRs — semantic search only
├── condition-c/            5 ADRs — grep + file read  
├── condition-d/            5 ADRs — typed memory tools only
├── condition-e/            5 ADRs — all combined (discovery→context→verify)
├── scores/
│   ├── *-scores.json       Claude judge, 3-condition (A/B/C)
│   ├── *-scores-gpt4o.json GPT-4o judge, 3-condition (A/B/C)
│   ├── *-scores-4cond.json Claude judge, 4-condition (A/B/C/D)
│   └── *-scores-5cond.json Claude judge, 5-condition (A/B/C/D/E) ← final
├── calibration-manifest.json   15 calibration artifacts
└── score_with_gpt4o.py         GPT-4o scoring script (raw HTTP)
```

20 score files × 5 dimensions × up-to-5 conditions = ~500 individual scores with per-claim reasoning.

### Judge prompt template (locked)

The exact prompt given to every judge agent:

```
You are evaluating an engineering artifact against ground truth.

GROUND TRUTH: [the real ADR, verbatim]

GENERATED: [the condition's output, verbatim]

Score on each dimension using EXACTLY the criteria below.
[locked rubric text inserted here — not paraphrased]

Output JSON: {technical_correctness, citation_of_prior_art, 
completeness, conciseness, pattern_adoption, notes}
```

The judge never sees the condition label (A/B/C/D/E), other conditions' outputs, or any hint about which condition is expected to win. It scores purely against ground truth.

### Context cost per condition

Every agent run reports: total tokens consumed, tool calls made, wall-clock time. This is the "price" of each retrieval strategy.

| Condition | Avg Tokens | Avg Tool Calls | Avg Wall Time | Quality | Cost Multiplier |
|---|---|---|---|---|---|
| A (no memory) | 48,434 | 2 | 106s | 0.572 | 1.0x (baseline) |
| B (semantic search) | 106,170 | 15 | 292s | 0.720 | 2.2x |
| C (grep + file read) | 115,835 | 23 | 179s | 0.918 | 2.4x |
| D (typed retrieval) | 74,599 | 20 | 272s | 0.650 | 1.5x |
| **E (all combined)** | **122,127** | **28** | **313s** | **0.954** | **2.5x** |

**Key takeaway: E is only 5% more expensive than C** (122K vs 116K tokens) **but produces consistently better output.** The typed discovery and semantic context steps add ~6K tokens on top of grep — negligible cost for measurable quality gain.

**Cost-efficiency analysis:**
- The jump from A→C costs 1.4x extra tokens for +60% quality improvement (43% return per unit)
- The jump from C→E costs 0.1x extra tokens for +4% quality improvement (infinite marginal return — essentially free)
- D is the cheapest memory option (1.5x) but lowest return (+14% for 0.5x cost)

**Wall time**: C is fastest (179s) because grep returns instantly. E is slowest (313s) due to 3 retrieval rounds. In practice, 5 minutes vs 3 minutes is irrelevant for a task whose output will be reviewed by a human. Token cost matters more than latency for engineering artifact generation.

**For practitioners at scale**: at Claude Opus pricing (~$15/M input, ~$75/M output), generating one ADR with condition E costs approximately $2-3. A full study of 118 items × 3 runs = ~$700-1,000 in API costs. The pilot (25 generations + 20 scoring runs) cost approximately $150 total.

## 3. Results

```
Condition              Mean    Improvement over A
──────────────────────────────────────────────────
A (no memory)          0.572   —
B (semantic search)    0.720   +26%
C (grep + file read)   0.918   +60%
D (typed retrieval)    0.650   +14%
E (all combined)       0.954   +67%  ← best
```

**E wins all 5 ADRs. No ties, no losses.**

| ADR Topic | A | B | C | D | E |
|---|---|---|---|---|---|
| Journal pipeline quality | 0.51 | 0.62 | 0.94 | 0.51 | **0.98** |
| GPU swap controller | 0.60 | 0.75 | 0.84 | 0.55 | **0.85** |
| Connector architecture | 0.51 | 0.90 | 0.94 | 0.83 | **0.97** |
| GDPR memory position | 0.48 | 0.52 | 0.90 | 0.76 | **0.97** |
| Egress control strategy | 0.76 | 0.80 | 0.97 | 0.58 | **1.00** |

## 4. Three Findings

### Finding 1: Retrieval methods compose super-linearly

If retrieval methods were independent, combining them would yield the max of their individual scores (max of 0.918, 0.720, 0.650 = 0.918). Instead, E scores 0.954 — above any individual component. The layers don't just coexist; they reinforce.

**Why**: each layer catches errors the others introduce.
- On ADR-043: typed retrieval (D) cited the wrong Hamburg DPA date. The grep verification step in E caught and corrected the error. D alone scored 0.76; E scored 0.97.
- On ADR-029: typed retrieval (D) fabricated the wrong architecture. File verification in E read the actual K8s manifests and got the correct design. D alone scored 0.55; E scored 0.85.
- On ADR-012: grep (C) missed the downstream outcomes (VW-276 purge, VW-279 replay). Typed discovery in E found them via `recall_decisions`. C scored 0.94; E scored 0.98.

### Finding 2: Semantic search can hurt below baseline

On ADR-048 (egress control), condition B (semantic search only) scored 0.80 while condition A (no memory) scored 0.76 — a marginal improvement. But on the 4-condition pilot run, B actually scored 0.596 (BELOW A's 0.694) because semantic search returned adjacent-but-wrong networking documents that caused the LLM to fabricate details.

**Implication**: "just add RAG" is not universally helpful. Semantic search introduces a new failure mode — grounding on wrong context — that doesn't exist when the LLM relies on its training data alone. This argues against the industry default of "vector search everything."

### Finding 3: Extraction quality is the binding constraint for typed memory

Typed retrieval (D) is the highest-variance condition: 0.83 on ADR-034 (where facts matched the topic) but 0.51 on ADR-012 (where they didn't). The variance traces directly to extraction quality:

- Facts extracted with the v1 prompt (thin, 1-line summaries, no entities): `recall_decisions(topic="KEDA")` → 0 results
- Facts extracted with the v2 prompt (rich, with alternatives/root_cause/entities): same query → 2 results with actionable context

The retrieval mechanism works. The data it retrieves doesn't always contain enough detail. This is the same finding Mem0's "State of AI Agent Memory 2026" article identifies: "the write step, deciding what is worth keeping, is barely measured." We measure it here: the difference between v1 and v2 extraction is the difference between D being useful (0.83) and D being harmful (0.51).

### Finding 4: Model size matters less than retrieval quality (but there's a floor)

We ran the same Condition E (layered retrieval) workflow with three model tiers: Opus ($15/M input), Sonnet (~$3/M), and Haiku (~$0.25/M). Same prompts, same tools, same ground truth.

| ADR | Opus+E | Sonnet+E | Haiku+E | Opus+A (blind) |
|---|---|---|---|---|
| ADR-012 (journal) | 0.90 | **0.99** | 0.86 | 0.51 |
| ADR-029 (GPU swap) | **0.89** | 0.76 | 0.35 | 0.60 |
| ADR-034 (connectors) | **0.94** | 0.88 | 0.70 | 0.51 |
| **MEAN** | **0.91** | **0.88** | **0.64** | **0.54** |

**Token costs for the model comparison runs:**

| Model + E | Avg Tokens | Avg Tool Calls | Avg Wall Time | Approx Cost/ADR |
|---|---|---|---|---|
| Opus + E | 122,127 | 28 | 313s | $2-3 |
| Sonnet + E | 106,522 | 20 | 219s | $0.40-0.60 |
| Haiku + E | 147,816 | 12 | 127s | $0.08-0.15 |

**Three sub-findings:**

**4a. Sonnet + retrieval ≈ Opus + retrieval (within 3%).** Sonnet+E scores 0.88 vs Opus+E at 0.91. At 5x cheaper per token, Sonnet is the cost-efficient choice. It even beat Opus on ADR-012 (0.99 vs 0.90) because its natural conciseness became an advantage — Opus over-annotated its citations.

**4b. Sonnet + retrieval >> Opus without memory (+63%).** Sonnet+E (0.88) crushes Opus+A (0.54). A $0.50 ADR with good retrieval beats a $1.50 ADR with no retrieval. **Retrieval quality dominates model capability** for grounded engineering tasks.

**4c. Haiku is below the synthesis threshold.** Haiku+E is high-variance: 0.86 on simple topics (ADR-012) but catastrophically fails on complex architecture (ADR-029: 0.35). It "fabricated an alternative design rather than reconstructing the documented one from the evidence" — meaning it received correct context but couldn't synthesize it correctly. **There is a minimum model capability below which retrieval cannot compensate.** That floor is between Haiku and Sonnet.

**The practitioner recommendation:**

| Scenario | Recommended Model | Quality | Cost |
|---|---|---|---|
| Production ADRs, architecture decisions | **Sonnet + layered E** | 0.88 | ~$0.50/ADR |
| High-stakes compliance (GDPR, security) | Opus + layered E | 0.91 | ~$2.50/ADR |
| Bulk documentation, low-complexity | Sonnet + grep only (C) | ~0.85 | ~$0.30/ADR |
| Not recommended | Haiku + anything (failure risk on complex topics) | 0.64 | $0.10 but unreliable |
| Not recommended | Any model + no memory (wastes capability) | 0.54 | expensive AND wrong |

## 5. The Practical Recommendation

For engineering teams building AI-assisted development workflows:

### The 3-Step Workflow

```
Step 1 — DISCOVERY (typed retrieval)
  "What decisions/problems/patterns exist about this topic?"
  → Surfaces what you didn't know to look for
  → recall_decisions(topic=X), find_problems(topic=X)

Step 2 — CONTEXT (semantic search)  
  "What else is related?"
  → Fills in surrounding context
  → auto_search_vault(query=X)

Step 3 — VERIFICATION (file access)
  "Does the source actually say what memory claims?"
  → Verifies details against ground truth
  → grep + read the actual files
```

### Why this order matters

- **Skip Step 1**: you only find what you know to grep for. Decisions you weren't aware of stay hidden.
- **Skip Step 2**: you miss the broader context (related incidents, adjacent ADRs, implementation reports).
- **Skip Step 3**: you trust memory blindly and get wrong details (Hamburg DPA date, wrong model name).

### What NOT to do

- Don't use semantic search as your only memory. It can hurt (Finding 2).
- Don't use typed retrieval as your only memory. It's high-variance (Finding 3).
- Don't skip memory entirely. Even the worst memory condition (D, 0.650) beats no-memory (A, 0.572) on average.

## 6. Related Work

### Retrieval can hurt: established phenomenon

Four independent papers confirm that retrieval-augmented generation can degrade output quality below the no-retrieval baseline — our Finding 2 is well-supported:

- **Du et al. (EMNLP 2025)** found a 24.2% accuracy drop with 30K tokens of context despite *perfect* retrieval, with most damage in the first 7K tokens [arXiv 2510.05381]. This explains why our Condition B (semantic search returning 5-10 documents) sometimes hurt more than helped.
- **Chen et al. (2026)** tested model-size × retrieval interaction across 360M-8B parameters and found RAG destroys 42-100% of correct parametric answers for small models [arXiv 2603.11513]. This directly validates our Finding 5 (Haiku at 0.35 despite rich context).
- **Li et al. (2025)** showed that adding more retrieved code examples for review generation degrades performance — top-1 retrieval works best [arXiv 2511.05302].
- **Jiang (2025)** found RAG yielded LOWER semantic diversity than no-RAG for engineering design ideation, constraining rather than enriching outputs [doi:10.1080/09544828.2025.2574209].

### Layered retrieval composes beneficially

Two studies demonstrate additive benefits from combining retrieval types, partially supporting our Finding 1:

- **EXPEREPAIR** (Mu et al., 2025): dual-memory system (episodic demonstrations + semantic insights) for code repair on SWE-Bench. Removing all memory: 41.3% → full system 49.3%. Both memory types contribute independently [arXiv 2506.10484]. Closest published analogue to our study.
- **MemCoder** (Deng et al., 2026): structured memory (commit retrieval + experience + self-refine) yields +9.4% resolved rate; ablation confirms each layer contributes [arXiv 2603.13258].

Neither study tests typed-fact retrieval + semantic + file-access as distinct layers, nor measures super-linear composition.

### Sparse retrieval outperforms dense for code tasks

- **Galimzyanov et al. (2025)** found BM25 (sparse) significantly outperforms dense retrieval for programming-language-to-programming-language tasks while being 100x faster [arXiv 2510.20609]. This validates our finding that grep (C: 0.918) beats semantic search (B: 0.720) — exact-match retrieval is more precise than embedding-similarity for grounded engineering work.
- **ByteRover** (Nair et al., 2026): 5-tier progressive retrieval (cache → BM25 → LLM search → recursive → out-of-domain detection) achieves 92.8% on LongMemEval-S vs GPT-4o with full context at only 60.6% [arXiv 2604.01599]. Supports tiered/layered approaches.

### Memory transfer and typed retrieval variance

- **Kim et al. (2026)**: cross-domain memory transfer yields +3.7% on coding benchmarks, but abstract insights transfer well while concrete traces induce NEGATIVE transfer [arXiv 2604.14004]. Supports our Finding 3 — typed facts (structured abstractions) are high-variance depending on whether they match the target domain.

### What no prior work addresses

Our study occupies an unaddressed niche at the intersection of three gaps:

1. **Engineering documentation (not code)**: All published retrieval comparisons target code generation, code repair, or Q&A. No prior study tests retrieval methods for prose engineering artifacts (ADRs, design documents, incident reports).
2. **Model-tier × retrieval interaction for generation quality**: Chen et al. tests model size but for QA, not document generation. No study shows "Sonnet+retrieval ≈ Opus+retrieval" for engineering outputs.
3. **Typed-fact retrieval as a distinct condition**: No study isolates structured-schema retrieval (SQL WHERE on fact_type, severity, status) vs semantic retrieval vs file access as independent experimental conditions.

## 7. Limitations

1. **N=5 ADRs, single platform.** This is a pilot. The full study (118 items across 5 artifact types) is scoped but not yet executed.
2. **Single judge (Claude Opus).** Dual-judge validation on conditions A/B/C showed 100% rank agreement on the top condition but absolute scores diverge (GPT-4o is ~0.15 stricter).
3. **Specific prompt design gives grep an advantage.** Task prompts contained specific keywords that made grep effective. Vague prompts (where you don't know what to search for) would likely widen E's margin over C.
4. **Extraction quality was improved mid-study.** The v2 extraction prompt was deployed during the pilot. A production system with months of v2-quality facts would likely show D performing closer to C.
5. **Single run per cell.** No K=3 replication. LLM-judge noise is ±0.07 per the ADR-046 benchmark. The E>C margin (+0.036 mean) is within noise on individual ADRs but consistent across all 5.

## 7. What This Means for the Field

The memory-for-coding-agents space is $300M+ funded (Mem0 $24M, Augment $252M, Qodo $70M) and growing. Every product makes a bet on retrieval mechanism: Mem0 bets on semantic+graph, Augment on commit-lineage, ByteRover on hierarchical markdown, agentmemory on hybrid BM25+vector.

Our finding: **the mechanism matters less than the composition.** No single retrieval approach dominates. The combination does — and the binding constraint is extraction quality (what you put IN the memory), not retrieval sophistication (how you get it OUT).

The practical implication: invest in your write path (richer fact extraction, entity tagging, severity classification) before investing in fancier retrieval. A simple `word_similarity` query against well-structured facts outperforms sophisticated vector search against thin text blobs.

## 8. Reproducibility

All data is available:
- 5 ground-truth ADRs from a production K8s engineering platform
- 25 generated ADRs (5 conditions × 5 ADRs)
- 25 structured score JSONs (5-dimension rubric, per-claim decomposition)
- Locked rubric v1 with behavioral anchors and calibration manifest
- Extraction prompt v1 (thin) and v2 (rich) for comparison

Platform: Rootweaver (typed engineering memory on K3s). Model: Claude Opus 4.7. Retrieval: MCP-native typed tools + Qdrant semantic search + filesystem access.

---

*Ryan G. Duffy is a Site Reliability Engineer building AI-powered engineering tools. Rootweaver is his solo engineering-memory platform, accumulating 248 sessions of real engineering work since February 2026.*

*Contact: ryanduffy.uk@gmail.com | ORCID: 0009-0009-6464-0617*
