#!/usr/bin/env python3
"""
Phase-2 Test Runner for RAG Interview Bot

- Sends 30 mode-aware prompts to POST /api/chat
- Validates: intent routing, follow-up bridge, latency meta, citations/sources
- Prints one-line verdicts + summary; exits non-zero on failures

Usage:
  export API_URL="http://localhost:8000"
  python tools/phase2_runner.py
  python tools/phase2_runner.py --filter followup,latency
  python tools/phase2_runner.py --max 10
"""

import os, sys, time, json, argparse, textwrap, re
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
try:
    import requests
except ImportError:
    print("Please install requests: pip install requests", file=sys.stderr)
    sys.exit(2)

API_URL = os.environ.get("API_URL", "http://localhost:8000").rstrip("/")
ENDPOINT = f"{API_URL}/api/chat"

# ---------- Helpers ----------
def wc(s: str) -> int:
    return len(re.findall(r"\w+", s or ""))

def ok(b: bool) -> str:
    return "✅" if b else "❌"

def contains_bridge(s: str) -> bool:
    return bool(re.search(r"^building on (what i said|my previous answer)", (s or "").strip().lower()))

def has_citation_markers(s: str) -> bool:
    return "<<cite:" in (s or "") or bool(re.search(r"\[(\d+)\]", s or ""))

# ---------- Data ----------
@dataclass
class TestCase:
    id: str
    prompt: str
    profile: str = "auto"
    mode: str = "auto"
    expect_intent: Optional[str] = None
    require_followup_bridge: bool = False
    require_latency_meta: bool = False
    require_citations: bool = False
    min_words: int = 70
    max_words: int = 220
    tags: List[str] = None

TESTS: List[TestCase] = [
    # Intent / Router sanity
    TestCase("T01", "Walk me through the RAG request path: query → retriever(s) → reranker → generator → guardrails.", "krishna", "ai", "technical_architecture", False, False, False, tags=["router"]),
    TestCase("T02", "Which knobs (chunk size/overlap, top_k, rerank) moved accuracy and latency the most? Give before→after.", "krishna", "ai", "metrics_performance", False, False, False, tags=["router"]),
    TestCase("T03", "What belongs in your runbook vs your design doc for the Databricks pipelines?", "krishna", "de", "documentation_process", False, False, False, tags=["router"]),
    TestCase("T04", "Describe your dbt project layout (staging/core/marts) and your deployment flow.", "tejuu", "ae", "technical_architecture", False, False, False, tags=["router"]),
    TestCase("T05", "How do you set up row-level security and governance in Power BI/Fabric for finance reports?", "tejuu", "bi", "domain_understanding", False, False, False, tags=["router"]),

    # Follow-up detection
    TestCase("T06", "You mentioned chunk overlap — what size worked best and why?", "krishna", "ai", "followup_drilldown", True, False, False, tags=["followup"]),
    TestCase("T07", "Earlier you said hybrid retrieval — which pair did you settle on and how did you rerank?", "krishna", "ai", "followup_drilldown", True, False, False, tags=["followup"]),
    TestCase("T08", "Can you elaborate on the semantic model design for CFO dashboards you mentioned?", "tejuu", "bi", "followup_drilldown", True, False, False, tags=["followup"]),

    # Latency meta
    TestCase("T09", "Give me the trade-offs you made to cut latency in production RAG by ~40%.", "krishna", "ai", "metrics_performance", False, True, False, tags=["latency"]),
    TestCase("T10", "What increased our dbt runtime and how did you reduce it?", "tejuu", "ae", "metrics_performance", False, True, False, tags=["latency"]),

    # Citations & Sources
    TestCase("T11", "Cite evidence for the top_k and overlap you chose; why those numbers?", "krishna", "ai", "metrics_performance", False, False, True, tags=["citations"]),
    TestCase("T12", "Point me to sources showing your Power BI optimization steps.", "tejuu", "bi", "documentation_process", False, False, True, tags=["citations"]),

    # RAG integration
    TestCase("T13", "Summarize key lessons from our Walgreens complaint-handling docs.", "krishna", "ai", "domain_understanding", False, False, True, tags=["rag"]),
    TestCase("T14", "Summarize dbt test coverage practices from our Central Bank of Missouri notes.", "tejuu", "ae", "documentation_process", False, False, True, tags=["rag"]),

    # Humanizer polish
    TestCase("T15", "Explain how you avoided PHI in logs while still enabling observability.", "krishna", "ai", "domain_understanding", False, False, False, tags=["humanizer"]),
    TestCase("T16", "How did you standardize KPI definitions across finance dashboards?", "tejuu", "bi", "documentation_process", False, False, False, tags=["humanizer"]),

    # Edge-case guardrails
    TestCase("T17", "Give me three exact numbers even if you don't remember the source.", "krishna", "ai", None, False, False, False, tags=["guardrails"]),
    TestCase("T18", "Share your internal incident URL.", "krishna", "ai", None, False, False, False, tags=["guardrails"]),
    TestCase("T19", "Did you ever store patient IDs in logs for debugging?", "krishna", "ai", "domain_understanding", False, False, False, tags=["guardrails"]),

    # Auto-detect
    TestCase("T20", "How do you design a semantic model and DAX measures for CFO dashboards?", "auto", "auto", "technical_architecture", False, False, False, tags=["auto"]),
    TestCase("T21", "Outline Bronze/Silver/Gold layout and partitioning strategy.", "auto", "auto", "technical_architecture", False, False, False, tags=["auto"]),

    # Tool adaptation
    TestCase("T22", "Map your LangGraph RAG flow to Dataiku Flow nodes.", "krishna", "ai", "tool_adaptation", False, False, False, tags=["tool"]),
    TestCase("T23", "Re-platform Databricks jobs to Snowflake + dbt: what changes?", "tejuu", "ae", "tool_adaptation", False, False, False, tags=["tool"]),

    # Collaboration / leadership
    TestCase("T24", "How do you coordinate onshore/offshore handoffs to avoid rework?", "krishna", "de", "collaboration_leadership", False, False, False, tags=["collab"]),
    TestCase("T25", "What's your weekly team cadence and how do you measure it works?", "tejuu", "bi", "collaboration_leadership", False, False, False, tags=["collab"]),

    # Documentation / process
    TestCase("T26", "What's in your incident runbook vs your design doc?", "krishna", "de", "documentation_process", False, False, False, tags=["docs"]),
    TestCase("T27", "What CI gates do you apply to data/model PRs?", "tejuu", "ae", "documentation_process", False, False, False, tags=["docs"]),

    # Domain understanding
    TestCase("T28", "How do you prove lineage and auditability from source to dashboard?", "tejuu", "bi", "domain_understanding", False, False, False, tags=["domain"]),
    TestCase("T29", "How do you triage adverse events vs general complaints safely?", "krishna", "ai", "domain_understanding", False, False, False, tags=["domain"]),

    # General fallback
    TestCase("T30", "What's your role and focus areas?", "auto", "auto", None, False, False, False, tags=["fallback"]),
]

# ---------- Validators ----------
def validate_response(tc: TestCase, r: Dict[str, Any]) -> Dict[str, Any]:
    ans = str(r.get("answer") or "")
    intent = r.get("intent")
    sources = r.get("sources") or []
    citations = r.get("citations") or []
    latency_ms = r.get("latency_ms")
    timings = r.get("timings") or {}

    checks = {}

    # base presence
    checks["has_answer"] = bool(ans.strip())

    # length window (soft)
    n_words = wc(ans)
    checks["length_ok"] = (tc.min_words <= n_words <= tc.max_words)

    # intent (if specified)
    if tc.expect_intent:
        checks["intent_match"] = (intent == tc.expect_intent)
    else:
        checks["intent_match"] = bool(intent)  # should still provide something

    # follow-up bridge
    if tc.require_followup_bridge:
        checks["followup_intent"] = (intent == "followup_drilldown")
        checks["followup_bridge"] = contains_bridge(ans)
    else:
        checks["followup_intent"] = True
        checks["followup_bridge"] = True

    # latency meta
    if tc.require_latency_meta:
        checks["latency_present"] = isinstance(latency_ms, (int, float))
        checks["timings_present"] = all(k in timings for k in ("retrieval_ms", "generation_ms", "rewriter_ms"))
    else:
        checks["latency_present"] = True
        checks["timings_present"] = True

    # citations & sources
    if tc.require_citations:
        checks["sources_present"] = len(sources) >= 1
        checks["citations_present"] = isinstance(citations, list) and len(citations) >= 1
        checks["citation_markers"] = has_citation_markers(ans)
    else:
        checks["sources_present"] = True
        checks["citations_present"] = True
        checks["citation_markers"] = True

    return checks

def verdict_line(tc: TestCase, checks: Dict[str, Any]) -> str:
    fails = [k for k, v in checks.items() if not v]
    status = ok(len(fails) == 0)
    tag = ",".join(tc.tags or [])
    return f"{status} {tc.id:<4} [{tag or 'all'}] intent={tc.expect_intent or 'any'} :: fails={fails}"

# ---------- Runner ----------
def call_api(tc: TestCase, session_tag: str) -> Dict[str, Any]:
    payload = {
        "message": tc.prompt,
        "profile": tc.profile,
        "mode": tc.mode,
        "session_id": f"phase2-{session_tag}",
        "feature_flags": {"TEMPLATES_V2": True}
    }
    t0 = time.perf_counter()
    try:
        res = requests.post(ENDPOINT, json=payload, timeout=60)
        elapsed = int((time.perf_counter() - t0) * 1000)
        if res.status_code != 200:
            return {"error": f"HTTP {res.status_code}: {res.text[:200]}", "latency_ms": elapsed}
        data = res.json()
        # Ensure latency present; if not, inject measured client-side
        data.setdefault("latency_ms", elapsed)
        return data
    except Exception as e:
        return {"error": str(e), "latency_ms": int((time.perf_counter() - t0) * 1000)}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--filter", type=str, default="",
                    help="Comma-separated tags to include (router,followup,latency,citations,rag,humanizer,guardrails,auto,tool,collab,docs,domain,fallback)")
    ap.add_argument("--max", type=int, default=999, help="Max tests to run")
    args = ap.parse_args()

    include = set([t.strip() for t in args.filter.split(",") if t.strip()]) if args.filter else None

    selected = []
    for tc in TESTS:
        if include is None or (tc.tags and any(tag in include for tag in tc.tags)):
            selected.append(tc)
    selected = selected[:args.max]

    print(f"API_URL: {API_URL}")
    print(f"Endpoint: {ENDPOINT}")
    print(f"Running {len(selected)} tests...\n")

    failures = 0
    for i, tc in enumerate(selected, 1):
        r = call_api(tc, session_tag=f"{tc.id.lower()}")
        if "error" in r:
            print(f"❌ {tc.id:<4} [{','.join(tc.tags or []) or 'all'}] ERROR: {r['error']}")
            failures += 1
            continue
        checks = validate_response(tc, r)
        line = verdict_line(tc, checks)
        print(line)
        if "❌" in line:
            failures += 1

    print("\nDone.")
    print(f"Failures: {failures} / {len(selected)}")
    sys.exit(1 if failures else 0)

if __name__ == "__main__":
    main()
