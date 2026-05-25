#!/usr/bin/env python3
"""
Score pilot ADR outputs with GPT-4o as second judge (dual-judge protocol).
Uses urllib — no external packages needed.
"""

import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

PILOT_DIR = Path(__file__).parent
API_KEY = os.environ["OPENAI_API_KEY"]
MODEL = "gpt-4o"
ENDPOINT = "https://api.openai.com/v1/chat/completions"

ADRS = ["ADR-012", "ADR-029", "ADR-034", "ADR-043", "ADR-048"]
CONDITIONS = ["A", "B", "C"]
COND_LABELS = {"A": "no memory", "B": "semantic search", "C": "grep+read"}

GT_FILES = {
    "ADR-012": "ADR-012-Journal-Pipeline-Quality-Overhaul.md",
    "ADR-029": "ADR-029-KEDA-GPU-Swap-Controller.md",
    "ADR-034": "ADR-034-Data-Source-Connector-Architecture.md",
    "ADR-043": "ADR-043-Memory-System-Derived-Data-GDPR-Position.md",
    "ADR-048": "ADR-048-Egress-Control-Strategy.md",
}

RUBRIC = """Score this LLM-generated ADR against the ground truth on 5 dimensions.

D1 — Technical correctness (ordinal):
  0.0 = factual errors about the system, decision rationale contradicts known constraints
  0.5 = core decision correct but tradeoff analysis incomplete, or one factual error in peripheral detail
  1.0 = all technical claims correct, tradeoffs and alternatives consistent with engineering context

D2 — Citation of prior art (ratio 0.0-1.0):
  Decompose the generated output into claims that SHOULD reference prior work (prior ADRs, Jira tickets, file paths, incidents, named documents). A claim is "cited" ONLY if it names a specific reference (VW-NNN, ADR-NNN, file path, document title). Generic phrases like "as previously discussed" do NOT count.
  Score = cited_claims / total_citable_claims

D3 — Completeness (ratio 0.0-1.0):
  Required sections (from ground truth): Context, Decision, Consequences (positive AND negative), Alternatives (≥1), Status, Related links.
  Score = sections_present / total_required_sections

D4 — Conciseness (ordinal):
  0.0 = ≥3 paragraphs repeat information or contain generic AI filler
  0.5 = ≤2 instances of restated information or one deletable paragraph
  1.0 = every paragraph advances a distinct point, no filler

D5 — Pattern adoption (ratio 0.0-1.0):
  Check: frontmatter structure, status enum, alternatives comparison format, consequences split into positive/negative, related section with specific links.
  Score = adopted_patterns / applicable_patterns

Output ONLY valid JSON (no markdown, no explanation) with this exact structure:
{
  "technical_correctness": <0 | 0.5 | 1.0>,
  "citation_of_prior_art": <0.0-1.0>,
  "completeness": <0.0-1.0>,
  "conciseness": <0 | 0.5 | 1.0>,
  "pattern_adoption": <0.0-1.0>,
  "notes": "<one sentence summary of most notable quality difference vs ground truth>"
}"""


def call_gpt4o(system_prompt: str, user_prompt: str) -> dict:
    body = json.dumps(
        {
            "model": MODEL,
            "temperature": 0,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
    ).encode()

    req = urllib.request.Request(
        ENDPOINT,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
    )

    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
                content = data["choices"][0]["message"]["content"]
                return json.loads(content)
        except (urllib.error.HTTPError, json.JSONDecodeError, KeyError) as e:
            print(f"  Attempt {attempt+1} failed: {e}", file=sys.stderr)
            if attempt < 2:
                time.sleep(2**attempt)
    return {}


def main():
    results = {}

    for adr in ADRS:
        print(f"\n{'='*60}")
        print(f"Scoring {adr}")
        print(f"{'='*60}")

        gt_path = PILOT_DIR / "ground-truth" / GT_FILES[adr]
        gt_text = gt_path.read_text()

        adr_results = {
            "adr": adr,
            "judge": MODEL,
            "scored_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "conditions": {},
        }

        for cond in CONDITIONS:
            gen_path = PILOT_DIR / f"condition-{cond.lower()}" / f"{adr}.md"
            if not gen_path.exists():
                print(f"  {cond}: MISSING {gen_path}")
                continue

            gen_text = gen_path.read_text()
            print(f"  {cond} ({COND_LABELS[cond]}): scoring...", end=" ", flush=True)

            user_prompt = (
                f"GROUND TRUTH (the real ADR written and used in production):\n\n{gt_text}\n\n"
                f"---\n\n"
                f"GENERATED (produced by LLM under Condition {cond}: {COND_LABELS[cond]}):\n\n{gen_text}"
            )

            scores = call_gpt4o(RUBRIC, user_prompt)
            if scores:
                avg = (
                    sum(
                        float(scores.get(k, 0))
                        for k in [
                            "technical_correctness",
                            "citation_of_prior_art",
                            "completeness",
                            "conciseness",
                            "pattern_adoption",
                        ]
                    )
                    / 5
                )
                print(
                    f"avg={avg:.3f} (tc={scores.get('technical_correctness')}, cite={scores.get('citation_of_prior_art')}, comp={scores.get('completeness')}, conc={scores.get('conciseness')}, pat={scores.get('pattern_adoption')})"
                )
                adr_results["conditions"][cond] = scores
            else:
                print("FAILED")
                adr_results["conditions"][cond] = {"error": "API call failed"}

        results[adr] = adr_results
        out_path = PILOT_DIR / "scores" / f"{adr}-scores-gpt4o.json"
        out_path.write_text(json.dumps(adr_results, indent=2))

    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY — GPT-4o Judge")
    print(f"{'='*60}")
    print(f"{'ADR':<12} {'A':>8} {'B':>8} {'C':>8}")
    for adr in ADRS:
        r = results.get(adr, {}).get("conditions", {})
        avgs = []
        for c in CONDITIONS:
            s = r.get(c, {})
            if "error" not in s and s:
                avg = (
                    sum(
                        float(s.get(k, 0))
                        for k in [
                            "technical_correctness",
                            "citation_of_prior_art",
                            "completeness",
                            "conciseness",
                            "pattern_adoption",
                        ]
                    )
                    / 5
                )
                avgs.append(f"{avg:.3f}")
            else:
                avgs.append("?")
        print(f"{adr:<12} {avgs[0]:>8} {avgs[1]:>8} {avgs[2]:>8}")


if __name__ == "__main__":
    main()
