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
    # --- emergency & operational scenarios (highest priority) ---
    ("emergency_scenarios", re.compile(r"\b(critical.*failed.*am|pipeline.*failed.*am|failed.*at.*am|2\s*am|3\s*am|4\s*am|5\s*am|midnight|late night|after hours|off hours|weekend|holiday|emergency|urgent|immediate|asap|right now|immediately)\b", re.I)),
    ("operational_issues", re.compile(r"\b(business.*complaining|stakeholder.*upset|customer.*impact|revenue.*impact|production.*down|system.*down|service.*outage|data.*breach|security.*incident|compliance.*issue|reduce.*costs|infrastructure.*costs|regulation.*requires)\b", re.I)),
    
    # --- case study & design questions (high priority) ---
    ("case_study_design", re.compile(r"\b(how would you design|design.*architecture|create.*system|build.*solution|architect.*solution|design.*pipeline|design.*data.*platform|design.*analytics.*system|design.*data.*architecture|design.*for.*company|design.*for.*retail|design.*for.*healthcare)\b", re.I)),
    ("case_study_optimization", re.compile(r"\b(our.*is slow|optimize.*system|improve.*performance|fix.*issue|our.*data.*warehouse.*slow|our.*pipeline.*slow|our.*system.*slow|performance.*problem|bottleneck.*issue)\b", re.I)),
    ("case_study_migration", re.compile(r"\b(migrate.*from|migration.*from|move.*from.*to|transition.*from|upgrade.*from|modernize.*from|cloud.*migration|data.*migration|system.*migration)\b", re.I)),
    
    # --- follow-up & clarification questions (high priority) ---
    ("followup_clarification", re.compile(r"\b(can you elaborate|more details|what happened next|explain further|tell me more|go deeper|expand on|clarify|elaborate|drill down|dive deeper)\b", re.I)),
    ("followup_measurement", re.compile(r"\b(how did you measure|measure.*success|success.*metrics|kpi|roi|business.*impact|results.*achieved|outcome.*measured|quantify.*results|measure.*outcome|measure.*results|success.*measurement)\b", re.I)),
    ("followup_alternatives", re.compile(r"\b(what would you do differently|do differently|alternative.*approach|other.*options|different.*way|better.*approach|improve.*next.*time|would.*do.*differently|alternative.*way|different.*approach)\b", re.I)),
    
    # --- coding first (ask-first category) ---
    ("coding_dax", re.compile(r"\b(dax|measure\s|power\s+bi\s+measure|rolling.*dax|dax\s+measure)\b", re.I)),
    ("coding_python", re.compile(r"\b(python\s+code|write\s+python|show\s+python|pandas\s+code|numpy\s+code|dataframe\s+code)\b", re.I)),
    ("coding_sql", re.compile(r"\b(write\s+sql|sql\s+query|window\s+function|cte|top\s+\d+\s+per|write.*query)\b", re.I)),
    
    # --- intros / behaviorals ---
    ("intro_role", re.compile(r"\b(introduce\s+yourself|intro(duction)?|about\s+yourself|current\s+role|what\s+do\s+you\s+do|tell\s+me\s+about\s+yourself|quick\s+intro)\b", re.I)),
    ("behavioral_star", re.compile(r"\b(tell\s+me\s+about\s+a\s+time|star|situation\s+task\s+action\s+result|conflict|stakeholder|challenge|difficult|deadline)\b", re.I)),
    
    # --- project & architecture ---
    ("architecture_system", re.compile(r"\b(end[-\s]?to[-\s]?end|system\s+architecture|components\s+overview|components\s+of\s+the\s+system|ingestion[→>]|retriever[→>]|bronze/silver/gold|architecture|overall\s+design|why\s+.*\s+architecture|implement.*architecture)\b", re.I)),
    ("project_how", re.compile(r"\b(walk\s+me\s+through|how\s+did\s+you\s+build|how\s+did\s+you\s+design|how\s+did\s+you\s+implement|steps\s+you\s+took|cut.*runtime|walk\s+the\s+steps|how\s+did\s+you\s+optimize|how\s+did\s+you\s+improve|explain\s+how\s+you\s+built|how\s+you\s+built)\b", re.I)),
    ("project_overview", re.compile(r"\b(explain\s+your\s+project|what\s+did\s+you\s+build|project\s+you\s+shipped|who\s+used\s+it|what\s+problem\s+did\s+it\s+solve|overview|high[-\s]?level|business\s+problem|problem\s+and\s+outcome|outcome\s+in\s+your|what\s+project|project\s+did\s+you|project\s+are\s+you|project\s+you\s+work|project\s+you\s+worked|explain.*project|your\s+project)\b", re.I)),
    ("project_why_tradeoffs", re.compile(r"\b(why\s+.*\s+over\s+.*|trade[-\s]?off|tradeoffs|trade[-\s]?offs\s+in\s+your\s+approach|compare|versus|pros\s+and\s+cons|why\s+.*\s+instead\s+of|alternatives|why\s+did\s+you\s+choose|why\s+is.*better|why\s+.*\s+over)\b", re.I)),
    
    # --- tech stack & experience ---
    ("tech_stack_experience", re.compile(r"\b(what\s+is\s+your\s+tech\s+stack|tech\s+stack\s+experience|what\s+tools\s+do\s+you\s+use\s+for\s+(data\s+processing|development|analytics)|tools\s+you\s+use\s+for\s+(data\s+processing|development|analytics)|your\s+tech\s+stack|explain\s+your\s+experience|your\s+experience\s+with|experience\s+with)\b", re.I)),
    ("approach_methodology", re.compile(r"\b(what\s+is\s+your\s+approach|your\s+approach|explain\s+your\s+approach|methodology|how\s+do\s+you\s+approach|your\s+methodology)\b", re.I)),
    ("challenges_learnings", re.compile(r"\b(what\s+challenges|challenges\s+did\s+you\s+face|challenges\s+you\s+face|what\s+problems|problems\s+you\s+face|difficulties|obstacles|lessons\s+learned|what\s+did\s+you\s+learn)\b", re.I)),
    
    # --- scenarios & debugging ---
    ("scenario_runbook", re.compile(r"\b(on[-\s]?call|runbook|incident|scenario|outage|plan\s+of\s+attack|what\s+would\s+you\s+do|what\s+should\s+I\s+do|how\s+do\s+I\s+fix|troubleshoot|handle\s+this\s+issue|what\s+steps\s+would\s+you\s+take|my\s+.*\s+is\s+(slow|failing|down|broken)|fix\s+.*\s+issue|resolve\s+.*\s+problem|solve\s+.*\s+issue|.*\s+is\s+taking\s+too\s+long.*impacting.*business|.*\s+is\s+impacting.*business.*operations|.*\s+is\s+causing.*delays.*in.*reporting)\b", re.I)),
    ("scenario_troubleshooting", re.compile(r"\b(troubleshoot|debug|fix|resolve|handle|solve)\b.*\b(issue|problem|error|failure|slow|down|broken|not\s+working)\b", re.I)),
    ("scenario_optimization", re.compile(r"\b(optimize|improve|speed\s+up|make\s+faster|reduce\s+time|performance\s+issue|slow\s+.*\s+job|bottleneck)\b", re.I)),
    ("scenario_data_quality", re.compile(r"\b(data\s+quality.*error|quality.*error|data\s+quality.*issue|quality.*issue|data\s+quality.*problem|quality.*problem|failing.*with.*data\s+quality|data\s+quality.*failing|poor.*data\s+quality|data\s+quality.*poor)\b", re.I)),
    
    ("monitoring_tools", re.compile(r"\b(what\s+tools.*monitor|monitoring\s+tools|tools\s+for\s+monitoring|monitor.*performance|monitoring.*pipeline|monitoring.*system|what\s+tools\s+do\s+you\s+use\s+for\s+monitoring)\b", re.I)),
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
