---
date: 2026-05-24
jira: VW-438
methodology:
- Autorubric (Stanford SCALE, arXiv 2603.00077)
- RULERS (arXiv 2601.08654)
- RAGAS atomic decomposition (arXiv 2309.15217)
- Zimmer ADR review checklist (2023)
status: in-progress
tags:
- layer-3-research
- rubric
- evaluation
- eng-memory-bench
- project/#-layer-3-study
- project/adr
- project/adr-nnn
- project/claude-gpt
- project/compute
- tech/claude-opus-4.7
- tech/d4
- tech/incident-rubric-|-15
- tech/incident-rubric-|-30
- tech/k3s
- tool/kubectl
title: Layer 3 Study — Locked Rubric v1
type: experimental-design
vault-path: 02-Active-Work/Plans
version: '1.0'
---
# Layer 3 Study — Locked Rubric v1

> **IMMUTABLE ONCE STUDY BEGINS.** Per RULERS (arXiv 2601.08654), prompt sensitivity is the primary failure mode in LLM-as-judge evaluations. This rubric text, once version-locked, MUST NOT be reworded between conditions. Changes require a new version (v1.1, v2, etc.) with documented rationale.
>
> **Methodology**: Analytic rubric with binary + ordinal criteria per Autorubric (Stanford SCALE, arXiv 2603.00077). Ground-truth comparison via RAGAS-style atomic decomposition (arXiv 2309.15217). ADR-specific criteria mapped from Zimmer's 7-question ADR review checklist (2023).

## Study thesis

*"Typed-fact retrieval (structured queries by fact_type, severity, status) produces measurably better engineering artifacts than untyped retrieval (semantic similarity) when an LLM generates ADRs, incident reports, and architecture documentation from real engineering history."*

## Artifact types and rubric assignment

| Artifact type | Rubric | Count in study |
|---|---|---|
| ADRs | Decision Rubric | 34 |
| Plans | Decision Rubric | 20 (curated) |
| Incident reports | Incident Rubric | 30 (curated) |
| Implementation reports | Incident Rubric | 15 (curated) |
| HLDs | Architecture Rubric | 10 |
| LLDs | Architecture Rubric | 9 |
| **Total** | | **118** |

---

## Universal dimensions (apply to all three rubric types)

All five dimensions are scored for every artifact. The **behavioral anchors** change per rubric type (below), but the dimension definitions are universal.

| # | Dimension | Type | Range | Definition |
|---|---|---|---|---|
| D1 | Technical correctness | Ordinal | 0 / 0.5 / 1.0 | Are the technical claims in the output factually correct and consistent with the engineering context? |
| D2 | Citation of prior art | Binary per-claim | 0.0–1.0 ratio | Does the output reference relevant prior decisions, incidents, patterns, or artifacts from memory? Score = cited_claims / total_citable_claims (RAGAS atomic decomposition). |
| D3 | Completeness | Binary checklist | 0.0–1.0 ratio | Does the output include all sections/components present in the ground-truth artifact? Score = sections_present / total_ground_truth_sections. |
| D4 | Conciseness | Ordinal | 0 / 0.5 / 1.0 | Does the output avoid padding, repetition, and unnecessary content? |
| D5 | Pattern adoption | Binary per-pattern | 0.0–1.0 ratio | Does the output adopt patterns established in prior artifacts of the same type (naming, structure, terminology, section ordering)? Score = adopted_patterns / applicable_patterns. |

---

## Rubric Type 1: Decision Rubric (ADRs + Plans)

### D1 — Technical correctness (ordinal)

| Score | Behavioral anchor |
|---|---|
| 0.0 | Contains factual errors about the system (wrong component names, incorrect dependency claims, non-existent APIs), OR the decision rationale contradicts known constraints |
| 0.5 | Core decision is correct but tradeoff analysis is incomplete (missing a significant constraint or alternative), OR one factual error in peripheral detail |
| 1.0 | All technical claims are correct. Tradeoffs, constraints, and alternatives are consistent with the actual engineering context. Maps to Zimmer Q2 (option validity) + Q5 (solution soundness) |

### D2 — Citation of prior art (binary per-claim)

**Procedure**: Decompose the output into atomic claims that *should* reference prior work. A claim is "citable" if it:
- Describes a pattern first established in a prior ADR/plan
- References a past incident that informed the decision
- Claims a constraint that was decided elsewhere (e.g., "we use Qdrant" → should cite ADR where Qdrant was chosen)
- References a prior failed approach

**Score**: `cited_claims / total_citable_claims`. A "citation" is any explicit reference (ADR-NNN, VW-NNN, "as established in...", "per the HLD..."). Implicit references ("we tried X before" without naming when/where) score 0.5 per claim.

### D3 — Completeness (binary checklist)

**For ADRs**, the required sections (from Zimmer + Rootweaver convention):
- [ ] Context / problem statement
- [ ] Decision statement
- [ ] Consequences (positive AND negative)
- [ ] Alternatives considered (≥1 alternative)
- [ ] Status field (proposed/accepted/deprecated/superseded)
- [ ] Related links (Jira, prior ADRs, implementation tickets)

**For Plans**, the required sections:
- [ ] Goal / objective statement
- [ ] Task breakdown (numbered or phased)
- [ ] Dependencies / prerequisites
- [ ] Risk / concern section
- [ ] Acceptance criteria
- [ ] Timeline or effort estimate

**Score**: sections_present / total_required_sections.

### D4 — Conciseness (ordinal)

| Score | Behavioral anchor |
|---|---|
| 0.0 | Contains ≥3 paragraphs that repeat information already stated elsewhere in the document, OR includes generic AI-filler ("In conclusion, this decision..." / "It's important to note...") |
| 0.5 | Minor verbosity: ≤2 instances of restated information, OR one paragraph that could be deleted without information loss |
| 1.0 | Every paragraph advances a distinct point not covered elsewhere. No filler. No unnecessary preamble or summary |

### D5 — Pattern adoption (binary per-pattern)

**Patterns to check** (extracted from the 34 existing ADRs):
- [ ] Frontmatter structure (vault-path, title, date, type, status, jira, tags)
- [ ] Status uses enum: proposed | accepted | deprecated | superseded
- [ ] Alternatives section uses comparison table (not just prose)
- [ ] Related section uses wikilink format `[[ADR-NNN]]`
- [ ] Consequences split into positive and negative sub-sections

**Score**: adopted_patterns / applicable_patterns.

---

## Rubric Type 2: Incident Rubric (Incidents + Implementation Reports)

### D1 — Technical correctness (ordinal)

| Score | Behavioral anchor |
|---|---|
| 0.0 | Root cause is wrong or contradicts the evidence, OR resolution steps would not fix the problem, OR severity assessment is clearly miscalibrated |
| 0.5 | Root cause is plausible but incomplete (misses a contributing factor), OR resolution is correct but missing a step |
| 1.0 | Root cause correctly identified and supported by evidence. Resolution matches the actual fix. Severity calibrated to blast radius |

### D2 — Citation of prior art (binary per-claim)

**Citable claims for incidents**:
- References to prior incidents with the same root cause class
- References to ADRs or design decisions that created the vulnerability
- References to monitoring gaps identified in previous post-mortems
- References to VW-NNN tickets that are regressions of prior fixes

### D3 — Completeness (binary checklist)

**For Incidents**, required sections:
- [ ] Summary (what went wrong)
- [ ] Root cause
- [ ] Impact table (service × impact × status)
- [ ] Evidence (kubectl output, logs, metrics)
- [ ] Resolution (what was done)
- [ ] Timeline
- [ ] Prevention / lessons learned
- [ ] Related links (Jira, commits, prior incidents)

**For Implementation Reports**, required sections:
- [ ] Context / objective
- [ ] What was done (implementation detail)
- [ ] Evidence of completion (test output, deployment verification)
- [ ] Open issues / follow-up

### D4 — Conciseness (ordinal)

Same behavioral anchors as Decision Rubric.

### D5 — Pattern adoption (binary per-pattern)

**Patterns to check** (from existing incident reports):
- [ ] Frontmatter: created, jira, resolved, severity, status, tags, title, type, vault-path
- [ ] Severity uses: high | medium | low
- [ ] Impact table present (not just prose)
- [ ] Evidence section includes actual command output (not descriptions of output)
- [ ] Timeline uses table format (Time | Event)

---

## Rubric Type 3: Architecture Rubric (HLDs + LLDs)

### D1 — Technical correctness (ordinal)

| Score | Behavioral anchor |
|---|---|
| 0.0 | Component diagram contradicts actual deployment, OR interface specifications don't match code, OR dependency arrows are wrong |
| 0.5 | Architecture is mostly correct but misses a significant component or dependency, OR port/protocol details are wrong |
| 1.0 | All components, dependencies, interfaces, and deployment details are accurate and consistent with the live system |

### D2 — Citation of prior art (binary per-claim)

**Citable claims for architecture**:
- References to ADRs that drove architecture choices
- References to incidents that caused architecture changes
- References to capacity/performance data from benchmarks

### D3 — Completeness (binary checklist)

**For HLDs**:
- [ ] System overview / context diagram
- [ ] Component list with responsibilities
- [ ] Inter-component communication (protocols, ports)
- [ ] Data flow description
- [ ] Non-functional requirements (performance, security, scalability)

**For LLDs**:
- [ ] Class/module structure
- [ ] API specifications (endpoints, request/response)
- [ ] Data models / schemas
- [ ] Configuration (env vars, feature flags)
- [ ] Dependencies (internal + external)

### D4 — Conciseness (ordinal)

Same behavioral anchors.

### D5 — Pattern adoption (binary per-pattern)

**Patterns to check**:
- [ ] Frontmatter structure matches HLD/LLD convention
- [ ] ASCII/Mermaid diagrams used (not just prose descriptions)
- [ ] Port numbers reference the port allocation table
- [ ] Namespace references match K3s convention
- [ ] Service names match `kubectl get svc` output

---

## Calibration set (5 verdict-balanced examples per rubric type)

> To be populated before study execution. Select from the existing corpus:
> - 2 high-quality examples (expected aggregate ≥0.85)
> - 2 mediocre examples (expected aggregate 0.45-0.65)
> - 1 poor example (expected aggregate ≤0.30)
>
> Use the SAME model (Claude Opus 4.7) to score these examples first, then verify
> scores against human judgment. Adjust behavioral anchors if calibration reveals
> systematic bias.

### Calibration protocol

1. Select 5 calibration artifacts per rubric type (15 total)
2. Score with primary judge (Claude Opus 4.7) using this rubric text verbatim
3. Score with secondary judge (GPT-4o) using this rubric text verbatim
4. Score with human judge (Ryan + optionally 1 external reviewer)
5. Compute pairwise kappa (Claude-GPT, Claude-human, GPT-human)
6. If kappa < 0.6 on any dimension: revise behavioral anchors, re-calibrate
7. Lock rubric version once kappa ≥ 0.6 on all dimensions

---

## Judge prompt template (locked)

```
You are evaluating an engineering artifact generated by an LLM.

GROUND TRUTH: The following is the real artifact that was actually written and used in production.
[INSERT GROUND TRUTH]

GENERATED: The following was produced by an LLM under test conditions.
[INSERT GENERATED OUTPUT]

RUBRIC TYPE: [Decision | Incident | Architecture]

Score the generated artifact on each dimension using EXACTLY the criteria below. Do not infer, interpolate, or add criteria beyond what is specified.

[INSERT RUBRIC TYPE SECTION FROM THIS DOCUMENT — VERBATIM, NOT PARAPHRASED]

Output your scores as JSON:
{
  "technical_correctness": <0 | 0.5 | 1.0>,
  "citation_of_prior_art": <0.0-1.0 ratio>,
  "citation_claims": [{"claim": "...", "cited": true|false, "reference": "..."}],
  "completeness": <0.0-1.0 ratio>,
  "completeness_checklist": [{"section": "...", "present": true|false}],
  "conciseness": <0 | 0.5 | 1.0>,
  "pattern_adoption": <0.0-1.0 ratio>,
  "pattern_checklist": [{"pattern": "...", "adopted": true|false}],
  "notes": "..."
}
```

---

## Statistical design summary

| Parameter | Value |
|---|---|
| Test items | 118 (34 ADR + 30 incident + 15 impl + 20 plan + 10 HLD + 9 LLD) |
| Conditions | 4 (A: no memory, B: semantic only, C: grep+read, D: agentmemory) |
| Runs per cell | K=3 |
| Total evaluations | 1,416 |
| Counterbalancing | Latin square (4 blocks of ~30) |
| Omnibus test | Friedman |
| Pairwise tests | Wilcoxon signed-rank + Bonferroni (6 comparisons) |
| Effect size | Cliff's delta |
| Judge models | Claude Opus 4.7 (primary) + GPT-4o (secondary) |
| Inter-rater reliability | Cohen's kappa per dimension |

---

## Version history

| Version | Date | Change |
|---|---|---|
| v1.0 | 2026-05-24 | Initial rubric. 3 types, 5 dimensions, locked anchors. |

---

## Sources

- Autorubric (Stanford SCALE): https://arxiv.org/abs/2603.00077
- RULERS: https://arxiv.org/abs/2601.08654
- RAGAS: https://arxiv.org/abs/2309.15217
- Zimmer ADR review: https://ozimmer.ch/practices/2023/04/05/ADRReview.html
- Multi-LLM reliability (kappa benchmarks): https://arxiv.org/abs/2512.20352
- Prometheus 2 (cross-family judging): https://github.com/prometheus-eval/prometheus-eval
- Applying Statistics to LLM Evaluations: https://cameronrwolfe.substack.com/p/stats-llm-evals
