# Intent routing for interview questions
import re
from .templates.registry import list_intent_keywords

# Follow-up detection
FOLLOWUP_REGEX = re.compile(
    r"\b(you\s+mentioned|as\s+you\s+said|earlier|follow[-\s]?up|building\s+on|can\s+you\s+elaborate|drill\s*down|revisit)\b",
    re.I
)
FOLLOWUP_HINT_KEYWORDS = {"chunk overlap","chunk-overlap","hybrid retrieval","semantic model","bronze/silver/gold"}

# Stronger intent routing - ordered by specificity (first match wins)
INTENT_RULES = [
    # --- coding first (ask-first category) ---
    ("coding_dax", re.compile(r"\b(dax|measure\s|power\s+bi\s+measure|rolling.*dax|dax\s+measure)\b", re.I)),
    ("coding_python", re.compile(r"\b(python\s+code|write\s+python|show\s+python|pandas\s+code|numpy\s+code|dataframe\s+code)\b", re.I)),
    ("coding_sql", re.compile(r"\b(write\s+sql|sql\s+query|window\s+function|cte|top\s+\d+\s+per|write.*query)\b", re.I)),
    
    # --- intros / behaviorals ---
    ("intro_role", re.compile(r"\b(introduce\s+yourself|intro(duction)?|about\s+yourself|current\s+role|what\s+do\s+you\s+do|tell\s+me\s+about\s+yourself|quick\s+intro)\b", re.I)),
    ("behavioral_star", re.compile(r"\b(tell\s+me\s+about\s+a\s+time|star|situation\s+task\s+action\s+result|conflict|stakeholder|challenge|difficult|deadline)\b", re.I)),
    
    # --- project & architecture ---
    ("project_how", re.compile(r"\b(walk\s+me\s+through|how\s+did\s+you\s+build|how\s+did\s+you\s+design|how\s+did\s+you\s+implement|steps\s+you\s+took|cut.*runtime|walk\s+the\s+steps|how\s+did\s+you\s+optimize|how\s+did\s+you\s+improve)\b", re.I)),
    ("project_overview", re.compile(r"\b(explain\s+your\s+project|what\s+did\s+you\s+build|project\s+you\s+shipped|who\s+used\s+it|what\s+problem\s+did\s+it\s+solve|overview|high[-\s]?level|business\s+problem|problem\s+and\s+outcome|outcome\s+in\s+your|what\s+project|project\s+did\s+you|project\s+are\s+you|project\s+you\s+work|project\s+you\s+worked)\b", re.I)),
    ("project_why_tradeoffs", re.compile(r"\b(why\s+.*\s+over\s+.*|trade[-\s]?off|tradeoffs|compare|versus|pros\s+and\s+cons|why\s+.*\s+instead\s+of|alternatives)\b", re.I)),
    ("architecture_system", re.compile(r"\b(end[-\s]?to[-\s]?end|system\s+architecture|components|ingestion[→>]|retriever[→>]|bronze/silver/gold|architecture|overall\s+design)\b", re.I)),
    
    # --- scenarios & debugging ---
    ("scenario_runbook", re.compile(r"\b(on[-\s]?call|runbook|incident|scenario|outage|plan\s+of\s+attack|what\s+would\s+you\s+do)\b", re.I)),
    ("monitoring_tools", re.compile(r"\b(what\s+tools.*monitor|monitoring\s+tools|tools\s+for\s+monitoring|monitor.*performance|monitoring.*pipeline|monitoring.*system)\b", re.I)),
    ("debug_perf", re.compile(r"\b(p95|latency\s+spike|skew|shuffle|slow\s+model|slow\s+job|optimize|debug|bottleneck|performance|troubleshoot)\b", re.I)),
    
    # --- governance / lineage (BI/AE) ---
    ("governance_lineage", re.compile(r"\b(rls|row[-\s]?level\s+security|certified\s+dataset|governance|lineage|exposures?|contracts?|enforce.*data)\b", re.I)),
    
    # --- tool migration ---
    ("tool_migration", re.compile(r"\b(migrate|migration|port\s+from|move\s+from|switch\s+from|llamaindex|langgraph|dataform|replatform)\b", re.I)),
    
    # --- follow-up questions ---
    ("followup_drilldown", re.compile(r"\b(you\s+mentioned|as\s+you\s+said|earlier|follow[-\s]?up|building\s+on|can\s+you\s+elaborate|drill\s*down|revisit)\b", re.I)),
    
    # Fallback
    ("general", re.compile(r".*", re.I)),
]

# Legacy intent rules for backward compatibility (keeping for fallback)
LEGACY_INTENT_RULES = {
    "general": [
        "what is","who are","tell me about yourself","introduce","role","current","position",
        "background","experience","overview","summary","yourself"
    ],
    "technical_architecture": [
        "architecture","design","pipeline","rag","langgraph","langchain",
        "fastapi","databricks","dbt","fabric","ingestion","embedding",
        "retriever","reranker","generator","guardrails","orchestration",
        "system","component","flow","structure","build","create","develop",
        "optimize","models","maintainability","stryker","incremental","semantic",
        "layer","consistency","departments","exposures","freshness","testing"
    ],
    "metrics_performance": [
        "metric","accuracy","latency","throughput","p95","runtime","cost",
        "chunk","overlap","top-k","top_k","rerank","speed","benchmark","profiling",
        "improve","optimize","tune","performance","measure","track","monitor",
        "45%","40%","reduction","increase","decrease","improvement","optimization",
        "delta","zorder","caching","adoption","engagement","kpis","dashboards"
    ],
    "documentation_process": [
        "documentation","document","design doc","runbook","readme","confluence",
        "ci","ci/cd","pipeline checks","pr checklist","code review","standards",
        "incident","postmortem","playbook","sop","process","template","acceptance criteria",
        "sources","point me to","show me","optimization steps","coverage practices","test coverage practices"
    ],
    "tool_adaptation": [
        "dataiku","migrate","replatform","switch tools","snowflake","airflow",
        "adf","synapse","glue","athena","redshift","sf to databricks","dbt to fabric",
        "adapt","different","instead","alternative","replace","convert","transition"
    ],
    "collaboration_leadership": [
        "offshore","onshore","stakeholder","hand-off","handoff","standups",
        "jira","slack","cadence","alignment","communication","visibility",
        "team","manage","lead","coordinate","work with","collaborate"
    ],
    "domain_understanding": [
        "hipaa","phi","pii","compliance","governance","lineage","audit","auditable",
        "sox","gdpr","hipaa-safe","security","rls","row-level security","dax security",
        "anonymize","masking","hashing","approval","policy","controls","risk",
        "summarize","key lessons","complaint-handling","docs","lessons learned"
    ],
    "followup_drilldown": [],  # set via regex/keywords elsewhere
    "behavioral_star": [
        "tell me about a time","challenge","conflict","mistake","learned","deadline",
        "leadership","difficult","tough","hard","problem","issue","situation"
    ]
}

# Bigram mapping (weight 2x if found)
NGRAM2 = {
    "design doc": "documentation_process",
    "runbook": "documentation_process",
    "pr checklist": "documentation_process",
    "test coverage practices": "documentation_process",
    "row-level security": "domain_understanding",
    "data lineage": "domain_understanding",
    "hipaa compliance": "domain_understanding",
    "audit trail": "domain_understanding",
    "semantic model": "technical_architecture",  # BI-side arch
}

def route_intent(q: str, session_id: str = None) -> tuple[str, float]:
    """Route question to intent using new 10-question-type taxonomy."""
    s = (q or "").lower()

    # normalize Unicode dashes so follow-up regex hits
    s = s.replace("\u2014", "-").replace("\u2013", "-")

    # 1. Check for follow-up questions first - but only if there's conversation history
    if session_id:
        from .answer_v2 import memory
        session_memory = memory.get(session_id)
        if session_memory and len(session_memory) >= 2:
            # Only consider follow-up if there's actual conversation history
            if bool(FOLLOWUP_REGEX.search(s)) or sum(kw in s for kw in FOLLOWUP_HINT_KEYWORDS) >= 2:
                return ("followup_drilldown", 0.9)
    else:
        # No session_id provided, skip follow-up detection
        pass

    # 2. Use new intent rules (most specific first)
    for intent, pattern in INTENT_RULES:
        if pattern.search(s):
            return (intent, 0.85)

    # 3. Fallback to legacy keyword scoring
    scores = {
        "technical_architecture": 0.10,
        "metrics_performance":   0.05,
        "documentation_process": 0.05,
        "domain_understanding":  0.05,
        "followup_drilldown":    0.00,
        "project_storytelling":  0.05,
        "behavioral_star":       0.05,
        "learning_reflection":   0.05,
        "tool_adaptation":       0.05,
        "collaboration_leadership": 0.05,
        "general":               0.08
    }
    
    for intent, words in LEGACY_INTENT_RULES.items():
        for w in words:
            if w in s:
                scores[intent] += 1

    # bigram boost
    for ngram, intent in NGRAM2.items():
        if ngram in s:
            scores[intent] = scores.get(intent, 0) + 2

    # tie-breaker: explicit latency/perf words → metrics_performance
    if any(w in s for w in ["latency","runtime","p95","throughput","speed"]):
        scores["metrics_performance"] += 1

    # pick best
    intent, raw = max(scores.items(), key=lambda x: x[1]) if scores else ("general", 0)

    # confidence mapping
    conf = 0.34 if raw == 0 else (0.5 if raw == 1 else (0.66 if raw == 2 else 0.85))
    return intent, conf
