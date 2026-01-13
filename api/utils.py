import os, json
import threading
import re
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from functools import lru_cache
from pathlib import Path
load_dotenv()

# Import enhanced answer system
try:
    from core.enhanced_answer import answer_question_enhanced
    ENHANCED_AVAILABLE = True
except ImportError:
    ENHANCED_AVAILABLE = False
    print("Enhanced answer system not available, using legacy system")

_client = None
_embeddings = None
_meta = None
_lock = threading.Lock()
_project_root = Path(__file__).resolve().parents[1]  # rag-chatbot/

# ---------- Humanization post-processor ----------
import random

SIMPLE_REPLACEMENTS = {
    "utilize": "use",
    "utilized": "used",
    "utilise": "use",
    "utilised": "used",
    "utilizing": "using",
    "leverage": "use",
    "leveraged": "used",
    "leveraging": "using",
    "holistic": "end-to-end",
    "robust": "solid",
    "myriad": "many",
    "plethora": "many",
    "state-of-the-art": "modern",
    "cutting-edge": "modern",
    "paradigm": "approach",
    "synergy": "fit",
    "facilitate": "help",
    "facilitates": "helps",
    "optimal": "best",
    "enhance": "improve",
    "enhanced": "improved",
    "comprehensive": "complete",
    "integrated": "combined",
    "streamlined": "simplified",
    "employed": "used",
    "pivotal": "key",
    "seamless": "smooth",
}

# Calm senior openers (short, natural, not AI-ish)
CALM_OPENERS = {
    "plsql": [
        "Alright—give me a second.",
        "Okay, one moment.",
        "Yeah—let me think for a sec.",
        "Alright, so here's how I'd approach it.",
        "Okay—here's the clean way to do it.",
        "Yeah—this is a common pattern.",
    ],
    "de": ["Yeah—so…", "Okay—let me think.", "Alright, one sec."],
    "ai": ["Yeah—give me a second.", "Okay—so here's the approach.", "Alright, let's break it down."],
    "general": ["Yeah—give me a second.", "Okay—so…", "Alright, one sec."],
}

AI_PHRASES_TO_REMOVE = [
    r"\b(as an ai|i am an ai|as a language model)\b",
    r"\b(in conclusion|to summarize|overall)\b",
    r"\bsignificantly\b",
    r"\bsubstantial(ly)?\b",
    r"\brobust\b",
]

# Patterns for AI-ish endings to strip (full sentences)
AI_ENDINGS_TO_STRIP = [
    r"moving forward[^.]*\.",
    r"next steps[^.]*\.",
    r"next,? i plan[^.]*\.",
    r"i plan to[^.]*\.",
    r"the next step[^.]*\.",
    r"in my recent work[^.]*\.",
    r"for a client[^.]*\.",
    r"this approach improves[^.]*\.",
    r"the outcome of this[^.]*\.",
    r"the impact of this[^.]*\.",
    r"a recent example[^.]*\.",
    r"this approach not only[^.]*\.",
    r"this will ensure[^.]*\.",
    r"contributes to operational[^.]*\.",
    r"we can expect a[^.]*impact[^.]*\.",
    r"by implementing this[^.]*\.",
]

def _remove_ai_phrases(text: str) -> str:
    out = text
    for pat in AI_PHRASES_TO_REMOVE:
        out = re.sub(pat, "", out, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", out).strip()

def _strip_ai_endings(text: str) -> str:
    """Remove AI-ish ending sentences like 'Moving forward...' or 'Next steps...'"""
    out = text
    for pat in AI_ENDINGS_TO_STRIP:
        out = re.sub(pat, "", out, flags=re.IGNORECASE)
    return re.sub(r"\s{2,}", " ", out).strip()

# Patterns for fake experience / war stories to strip
FAKE_EXPERIENCE_PATTERNS = [
    r"i once[^.]*\.",
    r"i often found[^.]*\.",
    r"i managed to[^.]*\.",
    r"i've seen this[^.]*\.",
    r"we improved[^.]*\.",
    r"we reduced[^.]*\.",
    r"for instance,? i[^.]*\.",
    r"in my experience[^.]*\.",
    r"in previous projects[^.]*\.",
    r"in a recent[^.]*\.",
    r"while working[^.]*\.",
    r"at walgreens[^.]*\.",
    r"at pfizer[^.]*\.",
    r"at central bank[^.]*\.",
    r"for a client[^.]*\.",
]

# Clauses containing fake metrics - split by semicolons and commas too
FAKE_METRICS_KEYWORDS = [
    r'\d+\s*TB',
    r'\d+\s*GB', 
    r'\d+\s*%',
    r'\d+\s*million',
    r'\d+\s*billion',
    r'millions of rows',
    r'billions of rows',
]

def _strip_fake_experience(text: str, qtype: str = None) -> str:
    """Remove sentences/clauses with fabricated experience claims and fake metrics."""
    # Split into sentences
    sentences = re.split(r'(?<=[.!?])\s+', text)
    clean_sentences = []
    
    # Extra keywords to strip for specific qtypes
    exception_only_strip = [r'BULK COLLECT', r'FORALL', r'bulk processing']
    
    for sent in sentences:
        # Check if sentence has fake experience pattern
        has_fake = False
        for pat in FAKE_EXPERIENCE_PATTERNS:
            if re.search(pat, sent, re.IGNORECASE):
                has_fake = True
                break
        
        # Check if sentence has fake metrics
        if not has_fake:
            for kw in FAKE_METRICS_KEYWORDS:
                if re.search(kw, sent, re.IGNORECASE):
                    has_fake = True
                    break
        
        # For exceptions qtype, also strip BULK COLLECT/FORALL mentions
        if not has_fake and qtype == "exceptions":
            for kw in exception_only_strip:
                if re.search(kw, sent, re.IGNORECASE):
                    has_fake = True
                    break
        
        if not has_fake:
            clean_sentences.append(sent)
    
    out = " ".join(clean_sentences)
    # Clean up leftover fragments
    out = re.sub(r"\bfor instance,?\s*", "", out, flags=re.IGNORECASE)
    out = re.sub(r"\bInstead,\s*", "", out, flags=re.IGNORECASE)  # Clean orphaned "Instead,"
    out = re.sub(r"—\s*—", "—", out)
    return re.sub(r"\s{2,}", " ", out).strip()

def _strip_question_echo(answer: str, question: str) -> str:
    """Remove first sentence if it restates the question."""
    if not question or not answer:
        return answer.strip()
    sentences = re.split(r'(?<=[.!?])\s+', answer.strip())
    if len(sentences) <= 1:
        return answer.strip()
    first = sentences[0].lower()
    q = question.strip().lower()[:40]
    looks_like_echo = (
        q in first or
        "you asked" in first or
        "the question" in first or
        "asked about" in first
    )
    return " ".join(sentences[1:]).strip() if looks_like_echo else answer.strip()

def _add_calm_opener(answer: str, domain: str) -> str:
    """Add a short human opener if answer doesn't already start with one."""
    a = answer.strip()
    if not a:
        return a
    # Skip if already starts with opener or code
    if re.match(r"^(alright|okay|yeah|hmm|one sec|give me)\b", a.lower()):
        return a
    if a.lstrip().startswith("```"):
        return a
    openers = CALM_OPENERS.get(domain, CALM_OPENERS["general"])
    return f"{random.choice(openers)} {a}"

def _simplify_vocab(text: str) -> str:
    """Replace formal/buzzword vocabulary with natural language."""
    out = text
    for formal, simple in SIMPLE_REPLACEMENTS.items():
        # Case-insensitive replacement
        out = re.sub(r'\b' + formal + r'\b', simple, out, flags=re.IGNORECASE)
        out = re.sub(r'\b' + formal.title() + r'\b', simple.title(), out)
    return out

def _shorten_sentences(text: str, max_len=20) -> str:
    """Break long sentences into shorter, more natural ones."""
    # Split by sentence boundaries - optimized regex
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    fixed = []
    
    for sent in sentences:
        words = sent.split()
        word_count = len(words)
        if word_count <= max_len:
            fixed.append(sent)
        else:
            # Simplified: just split at max_len without complex logic
            for i in range(0, word_count, max_len):
                chunk = words[i:i+max_len]
                if chunk:
                    fixed.append(" ".join(chunk).rstrip(","))
    
    return " ".join(fixed)

def _enforce_lines(text: str, min_lines=8, max_lines=10) -> str:
    """Ensure response has enough sentences to naturally fill 8-10 lines in UI."""
    # Split into sentences
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
    
    # Clamp to max lines
    if len(sentences) > max_lines:
        sentences = sentences[:max_lines]
    
    # Return as normal paragraph - UI will naturally wrap to 8-10 lines
    return " ".join(sentences)

def _project_rel(*parts: str) -> str:
    """Build absolute path from project root."""
    return str(_project_root.joinpath(*parts))

def humanize(text: str, qtype: str = "general", domain: str = "general", question: str = "") -> str:
    """
    Transform AI response into natural, human-sounding interview answer.
    Domain-aware: PL/SQL keeps formatting, other domains strip bullets.
    Adds calm opener and strips question echoes.
    """
    if not text:
        return ""
    
    # Quick check: if text has code blocks, preserve them
    has_code = '```' in text or '`' in text
    code_blocks = []
    
    if has_code:
        def save_code(match):
            code_blocks.append(match.group(0))
            return f"__CODE_BLOCK_{len(code_blocks)-1}__"
        text = re.sub(r'```[\s\S]*?```', save_code, text)
        text = re.sub(r'`[^`\n]+`', save_code, text)
    
    # Fast vocabulary replacement (only most common buzzwords)
    text = _simplify_vocab(text)
    
    # Remove AI-ish phrases
    text = _remove_ai_phrases(text)
    
    # Strip AI-ish endings and fake experience for PL/SQL mode
    if domain == "plsql":
        text = _strip_ai_endings(text)
        text = _strip_fake_experience(text, qtype=qtype)
        # Convert Oracle % syntax to spoken form for interview readability
        text = re.sub(r'SQL%BULK_EXCEPTIONS', 'SQL percent BULK EXCEPTIONS', text)
        text = re.sub(r'SQL%ROWCOUNT', 'SQL percent ROWCOUNT', text)
        text = re.sub(r'SQL%FOUND', 'SQL percent FOUND', text)
        text = re.sub(r'SQL%NOTFOUND', 'SQL percent NOTFOUND', text)
        text = re.sub(r'%ROWTYPE', 'percent ROWTYPE', text)  # Do ROWTYPE first (longer match)
        text = re.sub(r'%TYPE', 'percent TYPE', text)
        # Catch any remaining Oracle % patterns (e.g., table.column%TYPE in examples)
        text = re.sub(r'(\w+)\.(\w+)%TYPE', r'\1 dot \2 percent TYPE', text)
        text = re.sub(r'(\w+)%TYPE', r'\1 percent TYPE', text)
        # Fix DBMS_OUTPUT framing for exceptions - remove or reframe as debug-only
        if qtype == "exceptions":
            # Remove "DBMS_OUTPUT or" - keep just the logging table part
            text = re.sub(r'\bDBMS_OUTPUT or a (custom )?', 'an ', text, flags=re.IGNORECASE)
            text = re.sub(r'\busing DBMS_OUTPUT\b', 'using an error table with autonomous transaction', text, flags=re.IGNORECASE)
    
    # For PL/SQL: keep formatting, don't clamp lines
    # For other domains: enforce lines and strip bullets
    if domain != "plsql":
        text = _enforce_lines(text, min_lines=8 if qtype != "intro" else 10, max_lines=10 if qtype != "intro" else 14)
        text = text.replace("•", "").replace("**", "")
    
    # Restore code blocks if present
    if has_code:
        for i, block in enumerate(code_blocks):
            text = text.replace(f"__CODE_BLOCK_{i}__", block)
    
    # Strip question echo if detected
    if question:
        text = _strip_question_echo(text, question)
    
    # Add calm opener (but not for code-first answers)
    text = _add_calm_opener(text, domain)
    
    # Collapse stray double spaces (but preserve newlines in code blocks)
    # Only collapse multiple spaces on the same line, not newlines
    text = re.sub(r"[ \t]{2,}", " ", text)  # Multiple spaces/tabs -> single space
    text = re.sub(r"\n{3,}", "\n\n", text)  # 3+ newlines -> 2 newlines
    return text.strip()

# ---------- Prompt templates ----------
PROMPTS = {
    "krishna": {
        # DE Mode System and Prompts
        "system_de": (
            "You are Krishna, a Data Engineer with deep experience in healthcare and retail data ecosystems. "
            "EXPERIENCE SUMMARY: Walgreens (Feb 2022 – Present), CVS Health (Jan 2021 – Jan 2022), McKesson (May 2020 – Dec 2020), Inditek (2017 – 2019). "
            "CURRENT ROLE: Build and optimize large-scale pipelines in Databricks and PySpark, manage cloud integrations, and enforce data governance.\n\n"
            
            "RESPONSE RULES:\n"
            "• Speak only about Walgreens for current work; use CVS, McKesson, or Inditek for past roles.\n"
            "• Don't mix timelines or projects.\n"
            "• Avoid filler like 'real-world' or 'actual'; describe what you did directly.\n"
            "• Replace vague claims with clear actions and results.\n\n"
            
            "STYLE GUIDE:\n"
            "• Conversational and confident — like explaining to a teammate.\n"
            "• 12–18-word sentences with natural contractions (I'm, we've, it's).\n"
            "• Professional but relaxed; no corporate buzzwords.\n"
            "• Add 1–2 measurable outcomes (%, TB, minutes, cost) when possible.\n"
            "• Use active verbs: built, optimized, migrated, tuned, reduced.\n"
            "• Mention small challenges naturally: 'The tricky part was…'.\n"
            "• Keep 8–10 lines, no bullets, no markdown, no restating the question.\n\n"
            
            "AVOID: leveraged synergies, holistic, plethora, pivotal, state-of-the-art, robust solution, significantly improved.\n\n"
            
            "SKILLS: PySpark, Databricks, AWS, Azure, Snowflake, ETL/ELT, streaming data, dbt, data quality, HIPAA compliance."
        ),
        "user_de": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Data Engineer) using only the given context. Provide a detailed explanation in 8–10 lines. "
            "Skip repeating the question; start directly with your explanation. "
            "Include exact tools, data volumes, and measurable outcomes (e.g., 'processed 10TB/month', 'cut job runtime by 40%'). "
            "Expand on your approach, challenges faced, and specific solutions implemented. "
            "Speak naturally, as if explaining to a teammate — clear, confident, and conversational. No bullets or formatting."
        ),
        "user_intro_de": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Data Engineer) giving a comprehensive personal introduction. "
            "You MUST provide 10–14 sentences total (90–120 seconds spoken). "
            "Follow the C-P-A-T framework in detail: Start with your CURRENT role at Walgreens (data pipelines, cloud integration, governance responsibilities), "
            "then expand on PAST roles (CVS, McKesson, Inditek - describe your specific projects and technologies used), "
            "highlight multiple ACHIEVEMENTS with specific metrics (pipeline optimizations, data quality improvements, cost savings, team impact), "
            "and close with what drives your passion for data engineering, future goals, and how you want to make an impact. "
            "Be detailed and expansive - this is your chance to tell your complete story. Speak confidently and warmly, like in an interview introduction. No formatting."
        ),
        "user_interview_de": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Data Engineer) responding in an interview. Limit to 8–10 lines. "
            "Describe the situation, what you built or optimized, and the measurable result. "
            "Include concrete tools (PySpark, Databricks, Airflow, Snowflake) and real performance numbers. "
            "Speak clearly and confidently, as if explaining to a hiring manager. No bullets or markdown."
        ),
        "user_sql_de": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Data Engineer). Keep total length 8–10 lines including SQL code. "
            "Show minimal, working SQL in a code block, then explain what it does in simple terms. "
            "Add one small optimization or performance tip if relevant. Speak naturally, not like a textbook."
        ),
        "user_code_de": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Data Engineer). Keep total response within 8–10 lines including code. "
            "Show short, clear Python or PySpark code in a code block, explain what it does, and mention one practical insight. "
            "Speak like you're walking a colleague through the code in a meeting — natural, confident, and easy to follow."
        ),
        
        # AI Mode System and Prompts
        "system_ai": (
            "You are Krishna, an AI/ML Engineer experienced in healthcare and retail analytics. "
            "EXPERIENCE SUMMARY: Walgreens (Feb 2022 – Present), CVS Health (Jan 2021 – Jan 2022), McKesson (May 2020 – Dec 2020), Inditek (2017 – 2019). "
            "CURRENT ROLE: Design GenAI solutions — RAG pipelines, LangChain / LangGraph workflows, FastAPI microservices, Azure ML deployments.\n\n"
            
            "RESPONSE RULES:\n"
            "• Current = Walgreens only; past = CVS, McKesson, Inditek.\n"
            "• No phrases like 'real-world' — experience is real by default.\n"
            "• Describe what you built, tuned, or shipped; avoid theory.\n\n"
            
            "STYLE GUIDE:\n"
            "• Sound human — like explaining in an interview or code review.\n"
            "• 12–18 word sentences; use contractions naturally.\n"
            "• Keep tone warm, confident, and concise — not academic.\n"
            "• Add concrete metrics (accuracy %, latency reduction %, speedups).\n"
            "• Use active verbs: built, trained, deployed, integrated.\n"
            "• Mention small hurdles naturally: 'The tricky part was…'.\n"
            "• Limit to 8–10 lines, no bullets or markdown.\n"
            "• Keep total under 300 tokens. Prefer 12–18 word sentences.\n\n"
            
            "AVOID: leveraged, holistic, plethora, pivotal, seamless, state-of-the-art, robust solution.\n\n"
            
            "SKILLS: TensorFlow, PyTorch, Hugging Face, OpenAI APIs, LangChain, LangGraph, FastAPI, RAG, MLOps, MLflow, HIPAA compliance."
        ),
        "user_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (AI/ML Engineer) using only the context above. Provide a comprehensive explanation in 8–10 lines. "
            "Skip restating the question — jump straight into the answer. "
            "Include specific tools, models, metrics, and what you actually did. "
            "Expand on your technical approach, implementation details, and results achieved. "
            "Speak naturally, as if explaining to a peer during a technical discussion. No bullets or formatting."
        ),
        "user_intro_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (AI/ML Engineer) giving a comprehensive personal introduction. "
            "You MUST provide 10–14 sentences total (90–120 seconds spoken). "
            "Follow the C-P-A-T framework in detail: Start with your CURRENT role at Walgreens (GenAI, RAG systems, LangChain/LangGraph, specific projects), "
            "then expand on PAST roles (CVS Health, McKesson, Inditek - describe your responsibilities and focus areas), "
            "highlight multiple ACHIEVEMENTS with specific metrics (RAG accuracy improvements, latency reductions, production deployments, team impact), "
            "and close with what drives your passion for AI/ML, future goals, and how you want to make an impact. "
            "Be detailed and expansive - this is your chance to tell your complete story. Speak confidently and naturally, like introducing yourself to a hiring manager. No formatting."
        ),
        "user_interview_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (AI/ML Engineer) responding in an interview. Stay within 8–10 lines. "
            "Describe a clear situation, what you did, and the measurable result. "
            "Mention frameworks, tools, or models where relevant. Speak smoothly — confident and conversational. No bullets or markdown."
        ),
        "user_ml_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (ML Engineer) using only context above. Limit to 8–10 lines. "
            "Skip repeating the question — get straight to your explanation. "
            "Include concrete tools (TensorFlow, PyTorch, MLflow), metrics, and design reasoning. "
            "Keep it natural, technical, and professional — like talking to a senior teammate."
        ),
        "user_deeplearning_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Deep Learning Engineer) using only context above. Limit to 8–10 lines. "
            "Avoid restating the question. Explain directly — mention model architecture, training method, or evaluation metrics. "
            "Speak clearly, in a human conversational tone, no formatting."
        ),
        "user_genai_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Generative AI Engineer). Keep it 8–10 lines. "
            "Do not repeat the question. Go straight into the explanation using LangChain, LangGraph, OpenAI, or vector DBs. "
            "If it's about RAG, briefly mention chunking, embeddings, retrieval, and generation. "
            "Include 1–2 concrete metrics or model parameters (e.g., top_k=5, 40% latency reduction). "
            "Speak naturally like explaining your project to a colleague. No bullets or markdown."
        ),
        "user_code_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (AI/ML Engineer). Keep total length 8–10 lines including code. "
            "Show minimal working Python or PyTorch code in a code block, explain what it does in plain English, and add one brief insight or tip. "
            "Speak clearly, as if walking a teammate through the code."
        ),
        
        # PL/SQL Mode System and Prompts
        "system_plsql": (
            "You are an Oracle PL/SQL Developer with 8+ years of experience writing stored procedures, "
            "functions, packages, and triggers in Oracle Database.\n\n"
            
            "CRITICAL RULE: You write ONLY Oracle PL/SQL code. You do NOT know Python, PySpark, or Spark. "
            "When asked for code, you write Oracle PL/SQL using CREATE OR REPLACE PROCEDURE/FUNCTION syntax.\n\n"

            "GUARDRAILS:\n"
            "- Oracle-first: use ONLY Oracle PL/SQL constructs and Oracle SQL idioms.\n"
            "- NEVER write Python, PySpark, Spark, or any non-Oracle code.\n"
            "- Do NOT invent employer-specific experience, table names, volumes, or metrics.\n"
            "- NEVER mention 'Walgreens', 'Central Bank', or any company name.\n\n"

            "VOICE:\n"
            "- Sound like a calm, senior Oracle developer.\n"
            "- Never repeat the question. End with practical closure.\n\n"

            "STYLE:\n"
            "- For code: write Oracle PL/SQL in ```sql blocks.\n"
            "- For concepts: 6-10 lines, 1 gotcha, 1 tradeoff.\n"

            "NEVER SAY: 'Moving forward', 'Next steps', 'I plan to', 'In summary', 'This approach improves', 'substantial improvement', 'robust', 'leverage', 'seamless'."
        ),
        "user_plsql": (
            "Context:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer as Krishna (senior Oracle PL/SQL developer).\n"
            "CRITICAL RULES:\n"
            "- Do NOT repeat the question.\n"
            "- Do NOT include code unless the question explicitly asks.\n"
            "- NEVER claim personal outcomes (runtime reduced, TB processed, critical report).\n"
            "- NEVER use numbers (TB, GB, %, million) unless user provided them.\n"
            "- NEVER say 'I once', 'I managed to', 'we improved', 'for a client'.\n"
            "- USE: 'Typically…', 'What works well is…', 'In production, you'll usually…'\n"
            "- For exception handling: MUST mention SQL%ROWCOUNT for DML, SQLCODE/SQLERRM, re-raise, never swallow errors.\n"
            "- For DISPLAY_CURSOR: MUST mention SQL_ID, ALLSTATS LAST, estimate vs reality.\n"
            "6-10 lines max. End with practical closure.\n"
        ),
        "user_intro_plsql": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna giving a brief introduction for a PL/SQL Developer role.\n"
            "Do NOT repeat the question.\n"
            "Mention your strong SQL background, comfort with Oracle PL/SQL constructs (packages, bulk processing, exception handling, tuning).\n"
            "Keep it 8–10 sentences. Be honest — don't claim extensive Oracle production experience unless true.\n"
            "Frame it as transferable skills from data engineering. Speak naturally and confidently."
        ),
        "user_code_plsql": (
            "IMPORTANT: This is an Oracle PL/SQL Developer interview. You MUST write Oracle PL/SQL code ONLY.\n"
            "DO NOT write Python. DO NOT write PySpark. DO NOT write Spark code. ONLY Oracle PL/SQL.\n\n"
            "Reference code from context (use this syntax):\n{context}\n\n"
            "Question: {question}\n\n"
            "Write Oracle PL/SQL code similar to the reference above.\n"
            "FORMATTING REQUIREMENTS:\n"
            "- Put code in ```sql block with PROPER INDENTATION and LINE BREAKS\n"
            "- Each SQL statement on its own line\n"
            "- Indent BEGIN/END blocks properly\n"
            "- Use newlines between logical sections\n"
            "Use CREATE OR REPLACE PROCEDURE/FUNCTION syntax.\n"
            "Use Oracle constructs: EXCEPTION, WHEN OTHERS, RAISE_APPLICATION_ERROR.\n"
            "Keep explanation brief (2-3 lines after code)."
        )
    },
    "tejuu": {
        # BI/BA Mode System and Prompts
        "system_bi": (
            "You are Tejuu, a BI Developer and Business Analyst experienced across financial services, healthcare, and retail. "
            "EXPERIENCE SUMMARY: Central Bank of Missouri (Dec 2024 – Present), Stryker (Jan 2022 – Dec 2024), CVS Health (May 2020 – Jan 2022), Colruyt (May 2018 – Dec 2019). "
            "CURRENT ROLE: Design and manage Power BI dashboards, SQL models, and reporting for finance and compliance teams.\n\n"
            
            "RESPONSE RULES:\n"
            "• Speak only about Central Bank for current work; past = Stryker, CVS, Colruyt.\n"
            "• Avoid generic statements — describe concrete actions and impact.\n\n"
            
            "STYLE GUIDE:\n"
            "• Conversational and confident — like explaining to stakeholders.\n"
            "• Short, clear sentences with light contractions.\n"
            "• Add 1–2 measurable results (%, time saved, adoption rate).\n"
            "• Use active verbs: built, automated, simplified, reduced, delivered.\n"
            "• Mention quick challenges when useful.\n"
            "• 8–10 lines max, no markdown or bullets.\n"
            "• Keep total under 300 tokens. Prefer 12–18 word sentences.\n\n"
            
            "AVOID: plethora, holistic, cutting-edge, seamless experience, robust solution.\n\n"
            
            "SKILLS: Power BI, Tableau, SQL, DAX, Power Query, data visualization, requirements gathering, UAT, stakeholder management."
        ),
        "user_bi": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (BI / BA professional) using only the context above. Keep it 8–10 lines. "
            "Skip repeating the question — begin directly with your explanation. "
            "Mention specific tools (Power BI, DAX, Tableau, SQL) and measurable outcomes (e.g., 'load time cut 30 s → 3 s', '85% user adoption'). "
            "Speak clearly and naturally, like discussing your project in a stakeholder meeting. No bullets or formatting."
        ),
        "user_intro_bi": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (BI Developer and Business Analyst) giving a personal introduction. "
            "Keep it conversational — around 10–12 sentences (90 seconds spoken). "
            "Follow the C-P-A-T framework: Start with your CURRENT role at Central Bank of Missouri (BI dashboards, stakeholder reporting), "
            "briefly mention PAST roles (Stryker, CVS, Colruyt), highlight ACHIEVEMENTS with metrics (dashboard adoption, load time improvements, KPI frameworks), "
            "and close with what you enjoy most about solving business problems through data visualization and storytelling. "
            "Speak warmly and professionally. No formatting."
        ),
        "user_interview_bi": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (BI / BA) in an interview. Limit to 8–10 lines. "
            "Tell a short story — situation, what you did, and the measurable result. "
            "Emphasize collaboration, requirements gathering, and business impact. "
            "Speak naturally — like a conversation, not a script. No bullets or formatting."
        ),
        "user_sql_bi": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (BI / BA). Keep total length 8–10 lines including code. "
            "Show concise SQL code in a code block, explain what it returns, and note the business value. "
            "Add one brief optimization tip if relevant. Speak naturally."
        ),
        "user_code_bi": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (BI Developer). Keep it 8–10 lines total including DAX / Power BI / Tableau code. "
            "Explain what the formula or calculation achieves and its business benefit. "
            "Add one practical insight or tip if helpful. Speak conversationally."
        ),
        
        # Analytics Engineer Mode System and Prompts
        "system_ae": (
            "You are Tejuu, an Analytics Engineer experienced in finance, healthcare, and retail data platforms. "
            "EXPERIENCE SUMMARY: Central Bank of Missouri (Dec 2024 – Present), Stryker (Jan 2022 – Dec 2024), CVS Health (May 2020 – Jan 2022), Colruyt (May 2018 – Dec 2019). "
            "CURRENT ROLE: Build dbt models, manage data pipelines, and bridge engineering with analytics teams.\n\n"
            
            "RESPONSE RULES:\n"
            "• Current = Central Bank only; past = Stryker / CVS / Colruyt.\n"
            "• Focus on what you designed, optimized, or automated — avoid theory.\n\n"
            
            "STYLE GUIDE:\n"
            "• Speak clearly and practically — like explaining to a data lead.\n"
            "• Use numbers (45 min → 8 min, 95% test coverage, 60% faster queries).\n"
            "• Active verbs: modeled, tested, automated, deployed.\n"
            "• Keep answers 8–10 lines, no markdown or bullets.\n"
            "• Mention small challenges when relevant ('The tricky part was…').\n"
            "• Keep total under 300 tokens. Prefer 12–18 word sentences.\n\n"
            
            "AVOID: plethora, cutting-edge, robust solution, state-of-the-art.\n\n"
            
            "SKILLS: dbt, SQL, Python, data modeling (star/snowflake), Databricks, Synapse, ADF, data testing, governance."
        ),
        "user_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer) using only the context. Keep it 8–10 lines. "
            "Go straight into your explanation — tools, logic, and impact. "
            "Include metrics (e.g., 'dbt runtime 45 min → 8 min', '95% test coverage'). "
            "Speak naturally and confidently — like describing your workflow in a stand-up. No bullets or formatting."
        ),
        "user_intro_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer) giving a personal introduction. "
            "Keep it natural and flowing — around 10–12 sentences (90 seconds spoken). "
            "Follow the C-P-A-T framework: Start with your CURRENT role at Central Bank of Missouri (dbt models, data pipelines, analytics), "
            "briefly cover PAST roles (Stryker, CVS, Colruyt), highlight ACHIEVEMENTS with metrics (dbt runtime improvements, test coverage, query performance), "
            "and close with what you enjoy about bridging analytics and engineering. "
            "Speak confidently and professionally. No formatting."
        ),
        "user_interview_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer) in interview. Limit to 8–10 lines. "
            "Describe the situation, your technical action, and measurable result. "
            "Include specific tools and any challenge you solved. "
            "Keep it natural and conversational — no bullets or markdown."
        ),
        "user_datamodeling_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Keep it 8–10 lines. "
            "Explain your data-modeling design (star/snowflake) with one quantified benefit (e.g., 'query time 60% faster'). "
            "Speak naturally — clear and confident. No bullets or formatting."
        ),
        "user_dbt_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Keep total 8–10 lines including code. "
            "Show concise dbt code or macro, explain its purpose and improvement metrics (runtime, test coverage). "
            "Speak conversationally — no formal tone."
        ),
        "user_azure_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Keep 8–10 lines. "
            "Describe Azure Synapse / ADF / Databricks usage with concrete metrics and workflow examples. "
            "Speak clearly and naturally. No bullets or markdown."
        ),
        "user_aws_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Keep 8–10 lines. "
            "Explain AWS tools (Redshift, Glue, S3, Athena) experience with real performance gains or efficiency outcomes. "
            "Speak naturally. No bullets or markdown."
        ),
        "user_python_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Keep total 8–10 lines including code. "
            "Show short Python / pandas / PySpark snippet, explain what it automates or cleans, and mention improvement metrics. "
            "Speak conversationally."
        ),
        "user_databricks_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Keep 8–10 lines. "
            "Describe Databricks workflows (dbt, PySpark, Delta Lake) and one measurable improvement (speed, cost, stability). "
            "Speak naturally and confidently. No bullets or markdown."
        ),
        "user_code_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Keep total 8–10 lines including code. "
            "Show minimal code (SQL, dbt, Python), explain its purpose, and add one practical insight or tip. "
            "Use a calm, conversational tone."
        )
    }
}

def _get_client():
    global _client
    if _client is not None:
        return _client
    
    with _lock:
        # Double-check after acquiring lock
        if _client is not None:
            return _client

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")

        # Optional proxy bypass (opt-in via env flag)
        bypass_proxy = os.getenv("BYPASS_HTTP_PROXY_FOR_OPENAI", "0") == "1"
        old_env = {}
        if bypass_proxy:
            for k in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
                if k in os.environ:
                    old_env[k] = os.environ.pop(k)

        try:
            # Keep constructor minimal; use per-request options for timeout/retries
            _client = OpenAI(api_key=api_key)
            print("OpenAI client initialized successfully")
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {e}")
        finally:
            # Restore proxies
            os.environ.update(old_env)

        return _client

def _load_data():
    """
    Loads embeddings and metadata, normalizes schema, and guarantees
    1:1 alignment between _embeddings rows and _meta docs.
    Expected meta item schema:
      {
        "id": "...",
        "text": "...",
        "metadata": {"file_name": "...", "file_path": "...", "persona": "ai"|"de"}
      }
    """
    global _embeddings, _meta

    with _lock:
        if _embeddings is not None and _meta is not None:
            return

        print("Loading embeddings and metadata...")

        metadata_paths = list(filter(None, [
            _project_rel("api/meta.json"),
            _project_rel("store/meta.json"),
            _project_rel("meta.json"),
            _project_rel("kb_metadata.json"),
        ]))
        embeddings_paths = list(filter(None, [
            _project_rel("api/embeddings.npy"),
            _project_rel("store/embeddings.npy"),
            _project_rel("embeddings.npy"),
            _project_rel("kb_embeddings.npy"),
        ]))

        meta_path = next((p for p in metadata_paths if os.path.exists(p)), None)
        emb_path = next((p for p in embeddings_paths if os.path.exists(p)), None)

        if not meta_path or not emb_path:
            # Fallback dummy store (10 docs, 1536 dims)
            print("No embeddings/meta found; creating dummy data for testing...")
            _embeddings = np.random.random((10, 1536)).astype(np.float32)
            _meta = [
                {
                    "id": f"dummy-{i+1}",
                    "text": f"Sample document {i+1} about data engineering and AI.",
                    "metadata": {
                        "file_name": f"test{i%2+1}.md",
                        "file_path": f"/kb/test{i%2+1}.md",
                        "persona": "de" if i % 2 == 0 else "ai",
                    },
                }
                for i in range(10)
            ]
        else:
            print(f"Loaded metadata from {meta_path}")
            with open(meta_path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            if not isinstance(raw, list):
                raise ValueError(
                    "meta.json must be a list of items with keys: text, metadata.{file_name,file_path,persona}"
                )

            # Normalize each item to ensure consistent structure (and avoid KeyError)
            norm = []
            for d in raw:
                md = d.get("metadata") or {}
                persona = md.get("persona")
                if persona is not None:
                    persona = str(persona).lower().strip() or None
                norm.append({
                    "id": d.get("id"),
                    "text": d.get("text") or d.get("content") or "",
                    "metadata": {
                        "file_name": md.get("file_name") or md.get("filename") or "unknown",
                        "file_path": md.get("file_path") or md.get("path") or "unknown",
                        "persona": persona,
                    },
                })
            _meta = norm

            print(f"Loaded embeddings from {emb_path}")
            _embeddings = np.load(emb_path)

        # Hard alignment check - embeddings and metadata must match exactly
        if _embeddings.shape[0] != len(_meta):
            raise ValueError(
                f"Embeddings count ({_embeddings.shape[0]}) != meta docs ({len(_meta)}). "
                "Rebuild your store to keep them aligned."
            )

        # Pre-normalize for cosine via dot product (safe even if already unit-length)
        denom = np.linalg.norm(_embeddings, axis=1, keepdims=True) + 1e-12
        _embeddings = _embeddings / denom

def _normalize_for_cache(s: str) -> str:
    """Whitespace and case normalization to increase cache hits for embeddings."""
    return re.sub(r"\s+", " ", s.strip()).lower()

@lru_cache(maxsize=512)  # Increased cache size
def _cached_embedding(norm_text: str) -> tuple:
    """LRU-cached embedding. Returns tuple (hashable)."""
    client = _get_client()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=norm_text,
        timeout=5.0,  # Add timeout for faster failure
        # if your SDK doesn't support timeout here, call: client.with_options(timeout=3.0).embeddings.create(...)
    )
    # tuple for cache-ability
    return tuple(response.data[0].embedding)

def _get_embedding(text: str):
    # Truncate text to avoid long embedding times (max ~8000 tokens ≈ 32k chars)
    if len(text) > 32000:
        text = text[:32000]
    norm = _normalize_for_cache(text)
    return np.array(_cached_embedding(norm), dtype=np.float32)

# Oracle PL/SQL keyword expansion map for hybrid retrieval
ORACLE_KEYWORD_EXPANSION = {
    # DISPLAY_CURSOR family
    "display_cursor": ["dbms_xplan", "sql_id", "child_number", "v$sql", "allstats", "execution_plan", "actual_plan"],
    "dbms_xplan": ["display_cursor", "display_awr", "sql_id", "allstats", "execution_plan"],
    "execution plan": ["dbms_xplan", "display_cursor", "sql_id", "allstats", "explain_plan"],
    "sql_id": ["dbms_xplan", "display_cursor", "v$sql", "child_number"],
    "allstats": ["dbms_xplan", "display_cursor", "row_source_statistics", "a-rows"],
    # Exception handling
    "exception": ["sqlcode", "sqlerrm", "raise_application_error", "when_others", "autonomous_transaction"],
    "error handling": ["exception", "sqlcode", "sqlerrm", "raise_application_error"],
    # Bulk operations
    "bulk collect": ["forall", "limit", "save_exceptions", "bulk_exceptions"],
    "forall": ["bulk_collect", "save_exceptions", "indices_of"],
}

def _search_similar(query_embedding, top_k=5, profile="krishna", mode="auto", query_text="", qtype="technical"):
    """
    Returns top-k KB chunks for the given query embedding,
    filtered by profile+mode with quality-based reranking.
    
    For PL/SQL mode:
    - qtype="code" or "sql" → include plsql_code persona (code snippets)
    - otherwise → prefer plsql persona only (no code chunks)
    - Uses hybrid retrieval with keyword boosting for Oracle terms
    """
    _load_data()

    # Ensure query is unit length (cosine) - optimized
    q = query_embedding.astype(np.float32)
    q_norm = np.linalg.norm(q)
    if q_norm > 1e-12:
        q = q / q_norm
    else:
        q = q  # Avoid division by zero

    # Fast cosine since both are normalized - vectorized operation
    sims = _embeddings @ q  # shape: (num_docs,)

    # Mode-aware filtering with strict profile+mode matching
    wanted_profile_modes = {
        "krishna": {"ai", "de", "plsql", "plsql_code"},
        "tejuu": {"analytics", "business"},
    }

    # Mode mapping for API compatibility
    mode_mapping = {
        "ae": "analytics",
        "bi": "business",
    }

    # Map mode if needed
    if mode in mode_mapping:
        mode = mode_mapping[mode]

    indices = list(range(len(_meta)))
    if profile and profile in wanted_profile_modes:
        wanted_modes = wanted_profile_modes[profile]
        if mode != "auto" and mode in wanted_modes:
            # Strict mode filtering
            wanted_modes = {mode}
        
        # PL/SQL mode: filter code chunks based on qtype
        if mode == "plsql":
            if qtype in ("code", "sql"):
                # Include both plsql and plsql_code for code questions
                wanted_modes = {"plsql", "plsql_code"}
            else:
                # Concept questions: only plsql (no code chunks)
                wanted_modes = {"plsql"}

        def get_mode(i):
            meta = (_meta[i].get("metadata", {}) or {})
            return meta.get("persona") or meta.get("mode")

        def matches_profile(i):
            meta = (_meta[i].get("metadata", {}) or {})
            file_path = meta.get("file_path", "").lower()
            return profile.lower() in file_path

        # Filter by both persona/mode AND profile name in file path
        filtered = [i for i in indices if get_mode(i) in wanted_modes and matches_profile(i)]
        if filtered:
            indices = filtered
        else:
            print(f"Warning: No content for profile '{profile}' with modes {wanted_modes}; using all content")

    # Rank within selected indices
    if not indices:
        return []

    # Quality-based reranking with improved project file prioritization
    # Build expanded query keywords for Oracle hybrid retrieval (normalize underscores to spaces)
    query_lower = query_text.lower().replace("_", " ").replace("-", " ")
    # Only use Oracle-specific terms for keyword boosting (not common words)
    oracle_stop_words = {"how", "do", "you", "the", "a", "an", "to", "for", "in", "on", "is", "what", "when", "where", "why", "using", "use", "with"}
    query_keywords = set()
    # Add expanded keywords for Oracle terms (also normalize expansions)
    for term, expansions in ORACLE_KEYWORD_EXPANSION.items():
        if term in query_lower:
            for exp in expansions:
                # Add both underscore and space versions
                query_keywords.add(exp.replace("_", " "))
                query_keywords.add(exp)
    # Also add significant Oracle terms from query (not stop words)
    for word in query_lower.split():
        if word not in oracle_stop_words and len(word) > 3:
            query_keywords.add(word)
    
    def boost_score(i):
        meta = (_meta[i].get("metadata", {}) or {})
        boost = 0.0
        # Quality boost (0.15 max)
        quality = float(meta.get("quality", 0.7))
        boost += 0.15 * quality
        
        file_path = meta.get("file_path", "").lower()
        chunk_text = _meta[i].get("text", "").lower().replace("_", " ").replace("-", " ")
        
        # Oracle keyword boost (hybrid retrieval) - tiered boost for keyword matches
        if mode == "plsql":
            oracle_matches = sum(1 for kw in query_keywords if kw in chunk_text)
            if oracle_matches >= 6:
                boost += 0.6  # Very strong boost for 6+ keyword matches (specific topic)
            elif oracle_matches >= 4:
                boost += 0.45  # Strong boost for 4-5 matches
            elif oracle_matches >= 3:
                boost += 0.3  # Medium-strong boost for 3 matches
            elif oracle_matches >= 2:
                boost += 0.15  # Medium boost for 2 matches
            elif oracle_matches >= 1:
                boost += 0.05  # Small boost for 1 match
        
        # Detect if this is a project-specific query
        is_project_query = any(company in query_text.lower() for company in ["central bank", "cbank", "stryker", "walgreens", "cvs", "mckesson"])
        
        # Project-specific boosts (higher priority when query mentions specific companies/projects)
        if is_project_query:
            # Boost project files when query is about specific projects
            if any(project in file_path for project in ["cbank_", "stryker_", "walgreens_", "cvs_", "mckesson_"]):
                boost += 0.25  # Higher boost for project files
            # Reduced boost for experience files when query is project-specific
            elif "experience" in file_path:
                boost += 0.05  # Much lower boost for experience files
        else:
            # General queries - balanced approach
            if "experience" in file_path:
                boost += 0.1  # Reduced from 0.2 to 0.1
            # Small boost for project files in general queries
            elif any(project in file_path for project in ["cbank_", "stryker_", "walgreens_", "cvs_", "mckesson_"]):
                boost += 0.05
        
        # Section relevance boost (if question contains section keywords)
        section = meta.get("section", "").lower()
        if section and any(word in section for word in query_text.split()):
            boost += 0.1
        
        return boost

    # Apply boosts to similarity scores
    local_scores = sims[indices] + np.array([boost_score(i) for i in indices], dtype=np.float32)
    top_local = np.argsort(local_scores)[::-1][:top_k]
    top_indices = [indices[i] for i in top_local]

    results = []
    for idx in top_indices:
        doc = _meta[idx]
        meta = doc.get("metadata", {}) or {}
        # Extract a better title from the source file
        source_file = meta.get("source_file") or meta.get("file_name") or meta.get("file_path") or f"source_{idx}"
        
        # Create a human-readable title from the filename
        if source_file and source_file != f"source_{idx}":
            # Remove path and extension, convert underscores to spaces, title case
            title = source_file.split('/')[-1]  # Get filename only
            title = title.replace('.md', '').replace('_', ' ').replace('-', ' ')
            title = ' '.join(word.capitalize() for word in title.split())
        else:
            title = f"Source {idx + 1}"
        
        results.append({
            "index": int(idx),
            "score": float(sims[idx]),
            "content": doc.get("text", ""),
            "source": title,
            "source_file": source_file,
            "metadata": meta
        })
    return results

def detect_question_type(question):
    """Intelligently detect the type of question to choose the best mode"""
    question_lower = question.lower().strip()
    
    # Intro/Self-introduction indicators (highest priority - be very specific)
    intro_phrases = ['tell me about yourself', 'about yourself', 'introduce yourself', 'who are you', 'what do you do', 'your background', 'your skills']
    if any(phrase in question_lower for phrase in intro_phrases):
        return 'intro'
    
    # Explicit code requests (very specific - matches "write", "show", "example", etc.)
    explicit_code_phrases = [
        'write code', 'show code', 'write a function', 'write a script', 'code example',
        'implement code', 'write python code', 'write sql code', 'write pyspark code',
        'write a procedure', 'write procedure', 'write a package', 'write package',
        'write pl/sql', 'write plsql', 'show me', 'give me an example', 'sample code',
        'snippet', 'demo', 'implement a', 'code pattern', 'show a', 'write a bulk',
        'write a forall', 'write a trigger'
    ]
    if any(phrase in question_lower for phrase in explicit_code_phrases):
        return 'code'

    # Explicit SQL requests
    explicit_sql_phrases = ['write sql', 'sql query', 'write a query', 'sql code', 'select statement', 'write a merge']
    if any(phrase in question_lower for phrase in explicit_sql_phrases):
        return 'sql'
    
    # Interview/Behavioral indicators (but not intro)
    interview_phrases = ['describe a time', 'tell me about a time', 'give me an example', 'situation where', 'challenge you faced', 'difficult project', 'team conflict', 'leadership experience', 'mistake you made', 'how did you handle', 'star method', 'situation task action result']
    if any(phrase in question_lower for phrase in interview_phrases):
        return 'interview'
    
    # Exception handling questions (PL/SQL specific)
    exception_keywords = ['exception', 'error handling', 'rollback', 'logging', 'when others', 'raise', 'sqlerrm', 'sqlcode', 'error log']
    if any(keyword in question_lower for keyword in exception_keywords):
        return 'exceptions'

    # Experience/Skills discussion (check this BEFORE technical)
    experience_keywords = ['experience with', 'worked with', 'used', 'familiar with', 'expertise in', 'knowledge of', 'proficient in', 'what is your experience']
    if any(keyword in question_lower for keyword in experience_keywords):
        return 'experience'

    # Technical discussion indicators (but not asking for code)
    tech_keywords = ['explain', 'how does', 'what is', 'difference between', 'compare', 'advantages', 'disadvantages', 'best practices', 'approach', 'strategy']
    if any(keyword in question_lower for keyword in tech_keywords):
        return 'technical'
    
    # Add these to match your routing branches
    if any(p in question_lower for p in ['hyperparameter', 'feature engineering', 'model training', 'ml pipeline', 'machine learning model', 'ml model']):
        return 'ml'
    if any(p in question_lower for p in ['transformer', 'cnn', 'rnn', 'lstm', 'attention', 'deep learning', 'neural network']):
        return 'deeplearning'
    if any(p in question_lower for p in ['rag', 'prompt', 'generative ai', 'llm', 'fine-tune', 'genai', 'gpt', 'openai']):
        return 'genai'
    
    # Default to general discussion
    return 'general'

def detect_domain(question, profile):
    """Detect the domain (de/ai/plsql/analytics/business) based on question content and profile."""
    q = question.lower()
    
    # Domain-specific signals
    plsql_signals = ["plsql", "pl/sql", "oracle", "bulk collect", "forall", "cursor", "ref cursor",
                     "package", "stored procedure", "trigger", "dbms_", "exception handling",
                     "raise_application_error", "pragma", "execute immediate", "rowtype", "type",
                     "nvl", "decode", "rownum", "merge into", "sql%rowcount"]
    ai_signals = ["llm", "langchain", "langgraph", "rag", "embedding", "prompt", "openai", "gpt",
                  "pytorch", "tensorflow", "mlflow", "fine-tune", "transformer", "agent",
                  "vector database", "pinecone", "weaviate", "hugging face", "model training"]
    de_signals = ["spark", "pyspark", "databricks", "etl", "elt", "delta lake", "kafka", "adf", 
                  "glue", "airflow", "data pipeline", "data lake", "streaming", "event hub",
                  "snowflake", "medallion", "bronze", "silver", "gold"]
    analytics_signals = ["dbt", "data modeling", "star schema", "fact table", "dimension table", "scd",
                         "slowly changing dimension", "dimensional model", "analytics engineer"]
    business_signals = ["power bi", "tableau", "dax", "dashboard", "visualization", "stakeholder",
                        "report", "kpi", "business intelligence", "looker", "qlik", "business analyst"]
    
    def any_in(words):
        return any(w in q for w in words)
    
    if profile == "krishna":
        # Check PL/SQL first (highest priority for Oracle interviews)
        if any_in(plsql_signals):
            return "plsql"
        if any_in(ai_signals):
            return "ai"
        if any_in(de_signals):
            return "de"
        # Default bias for Krishna is AI/ML
        return "ai"
    else:  # tejuu
        if any_in(analytics_signals):
            return "analytics"
        if any_in(business_signals):
            return "business"
        # Default bias for Tejuu is business
        return "business"

def detect_profile(question):
    """Auto-detect which profile (krishna or tejuu) is most relevant for the question."""
    question_lower = question.lower()
    
    # Tejuu-specific keywords (BI/BA/Analytics Engineering)
    tejuu_keywords = [
        'power bi', 'tableau', 'dax', 'dashboard', 'visualization', 'report', 'bi developer',
        'business analyst', 'stakeholder', 'kpi', 'analytics engineer', 'dbt',
        'data modeling', 'dimensional model', 'star schema', 'snowflake schema',
        'fact table', 'dimension table', 'slowly changing dimension', 'scd',
        'looker', 'qlik', 'sisense', 'metabase', 'superset',
        'business intelligence', 'self-service analytics', 'data visualization'
    ]
    
    # Krishna-specific keywords (DE/AI/ML/GenAI)
    krishna_keywords = [
        'pyspark', 'databricks', 'spark', 'etl', 'elt', 'data pipeline', 'data lake',
        'delta lake', 'azure data factory', 'adf', 'aws glue', 'airflow',
        'machine learning', 'deep learning', 'neural network', 'model training',
        'mlflow', 'llm', 'large language model', 'rag', 'langchain', 'langgraph',
        'transformer', 'fine-tune', 'embedding', 'vector database', 'pinecone',
        'tensorflow', 'pytorch', 'hugging face', 'openai', 'gpt',
        'data engineering', 'streaming', 'kafka', 'real-time data'
    ]
    
    # Count keyword matches
    tejuu_score = sum(1 for keyword in tejuu_keywords if keyword in question_lower)
    krishna_score = sum(1 for keyword in krishna_keywords if keyword in question_lower)
    
    # Return profile based on keyword matches
    if tejuu_score > krishna_score:
        return "tejuu"
    elif krishna_score > tejuu_score:
        return "krishna"
    else:
        # Default to Krishna for ambiguous questions
        return "krishna"

def answer_question(question, mode="auto", profile="auto", session_id="default", **kwargs):
    """Main answer_question function with enhanced template system integration."""
    
    # Use enhanced system if available
    if ENHANCED_AVAILABLE:
        return answer_question_enhanced(question, mode, profile, session_id, **kwargs)
    
    # Fallback to legacy system
    try:
        # Auto-detect profile if not specified
        profile_auto_detected = False
        if profile == "auto":
            profile = detect_profile(question)
            profile_auto_detected = True
            print(f"Auto-detected profile: {profile}")
        
        print(f"Processing question for profile '{profile}': {question[:50]}...")
        
        # Separate domain detection from question type
        qtype = detect_question_type(question)  # intro, code, sql, interview, genai, ml, etc.
        
        if mode in ("de", "ai", "analytics", "business"):
            # Explicit mode provided
            domain = mode
            auto_detected = False
        else:
            # Auto-detect domain
            domain = detect_domain(question, profile)
            auto_detected = True
        
        print(f"Routing → domain={domain}, qtype={qtype}")
        
        # Get query embedding
        print("Generating query embedding...")
        query_embedding = _get_embedding(question)
        print("Query embedding generated successfully")
        
        # Search for similar content (optimized for speed)
        # Pass qtype so PL/SQL mode can filter code chunks appropriately
        print(f"Searching for similar content for profile '{profile}' mode '{domain}' qtype '{qtype}'...")
        results = _search_similar(query_embedding, top_k=6, profile=profile, mode=domain, query_text=question, qtype=qtype)
        print(f"Found {len(results)} relevant chunks for profile '{profile}' mode '{domain}'")
        
        # Debug: Print the sources of the results (reduced for performance)
        if len(results) > 0:
            print(f"Found {len(results)} results, top source: {results[0].get('source', 'Unknown')}")
        
        # Build context efficiently with optimized length limits
        if not results:
            context = ""
        else:
            parts = []
            total = 0
            max_context = 1500  # Reduced for faster processing
            max_chunk = 500     # Reduced chunk size
            
            for r in results:
                chunk = r["content"]
                # Truncate chunk more aggressively
                if len(chunk) > max_chunk: 
                    chunk = chunk[:max_chunk] + "..."
                
                # Create fragment more efficiently
                frag = f"[{r['source']}] {chunk}"
                
                # Check if adding this fragment would exceed limit
                if total + len(frag) > max_context: 
                    break
                    
                parts.append(frag)
                total += len(frag)
            
            context = "\n\n".join(parts)
        
        # Debug: Print context preview (reduced for performance)
        print(f"Context length: {len(context)} chars")
        
        # Get prompts for the selected profile
        profile_prompts = PROMPTS.get(profile, PROMPTS["krishna"])
        print(f"Using: Profile='{profile}', Domain='{domain}', QType='{qtype}'")
        
        # Select system and user prompt based on domain and question type
        if profile == "krishna":
            if domain == "plsql":
                system_prompt = profile_prompts["system_plsql"]
            elif domain == "ai":
                system_prompt = profile_prompts["system_ai"]
            else:
                system_prompt = profile_prompts["system_de"]
            
            if domain == "plsql":
                # PL/SQL Mode
                if qtype == "intro":
                    user_prompt = profile_prompts["user_intro_plsql"]
                elif qtype == "code":
                    user_prompt = profile_prompts["user_code_plsql"]
                else:
                    user_prompt = profile_prompts["user_plsql"]
            elif domain == "ai":
                # AI/ML/GenAI Mode
                if qtype == "intro":
                    user_prompt = profile_prompts["user_intro_ai"]
                elif qtype == "interview":
                    user_prompt = profile_prompts["user_interview_ai"]
                elif qtype == "ml":
                    user_prompt = profile_prompts["user_ml_ai"]
                elif qtype == "deeplearning":
                    user_prompt = profile_prompts["user_deeplearning_ai"]
                elif qtype == "genai":
                    user_prompt = profile_prompts["user_genai_ai"]
                elif qtype == "code":
                    user_prompt = profile_prompts["user_code_ai"]
                else:
                    user_prompt = profile_prompts["user_ai"]
            else:  # de
                # Data Engineering Mode
                if qtype == "intro":
                    user_prompt = profile_prompts["user_intro_de"]
                elif qtype == "interview":
                    user_prompt = profile_prompts["user_interview_de"]
                elif qtype == "sql":
                    user_prompt = profile_prompts["user_sql_de"]
                elif qtype == "code":
                    user_prompt = profile_prompts["user_code_de"]
                else:
                    user_prompt = profile_prompts["user_de"]
        else:  # tejuu
            if domain == "analytics":
                # Analytics Engineer Mode
                system_prompt = profile_prompts["system_ae"]
                
                if qtype == "intro":
                    user_prompt = profile_prompts["user_intro_ae"]
                elif qtype == "interview":
                    user_prompt = profile_prompts["user_interview_ae"]
                elif 'dbt' in question.lower():
                    user_prompt = profile_prompts["user_dbt_ae"]
                elif any(x in question.lower() for x in ['data model', 'dimensional', 'star schema', 'fact', 'dimension']):
                    user_prompt = profile_prompts["user_datamodeling_ae"]
                elif any(x in question.lower() for x in ['azure', 'synapse', 'adf', 'data factory']):
                    user_prompt = profile_prompts["user_azure_ae"]
                elif any(x in question.lower() for x in ['aws', 'redshift', 'glue', 'athena']):
                    user_prompt = profile_prompts["user_aws_ae"]
                elif any(x in question.lower() for x in ['python', 'pandas', 'pyspark']):
                    user_prompt = profile_prompts["user_python_ae"]
                elif 'databricks' in question.lower():
                    user_prompt = profile_prompts["user_databricks_ae"]
                elif qtype == "code":
                    user_prompt = profile_prompts["user_code_ae"]
                else:
                    user_prompt = profile_prompts["user_ae"]
            else:  # business
                # BI/BA Mode
                system_prompt = profile_prompts["system_bi"]
                
                if qtype == "intro":
                    user_prompt = profile_prompts["user_intro_bi"]
                elif qtype == "interview":
                    user_prompt = profile_prompts["user_interview_bi"]
                elif qtype == "sql":
                    user_prompt = profile_prompts["user_sql_bi"]
                elif qtype == "code":
                    user_prompt = profile_prompts["user_code_bi"]
                else:
                    user_prompt = profile_prompts["user_bi"]
        
        user_prompt = user_prompt.format(context=context, question=question)
        
        # Get response from OpenAI (optimized for speed)
        print("Generating response with OpenAI...")
        client = _get_client()
        # Optimized token limits for faster responses
        max_tokens = 600 if qtype == "intro" else 500  # Reduced for speed
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Fastest model
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.2,        # Lower for more focused responses
            top_p=0.9,              # Tighter sampling for consistency
            frequency_penalty=0.2,  # Reduced for faster generation
            presence_penalty=0.0,
            max_tokens=max_tokens,  # Optimized for speed
            stream=False,
            timeout=10.0  # Add timeout for faster failure
        )
        # If your SDK version needs timeouts per-request:
        # response = client.with_options(timeout=15.0).chat.completions.create(...)
        print("Response generated successfully")
        
        # Apply humanization post-processor (domain-aware for PL/SQL)
        raw_answer = response.choices[0].message.content
        final_answer = humanize(raw_answer, qtype=qtype, domain=domain, question=question)
        
        # Code-stripping guard: if qtype is not code/sql, strip any accidental code blocks
        if qtype not in ("code", "sql") and domain == "plsql":
            # Strip code fences if model emitted them for a concept question
            if "```" in final_answer:
                # Remove code blocks but keep explanatory text
                final_answer = re.sub(r'```[\s\S]*?```', '', final_answer)
                final_answer = re.sub(r'\s{2,}', ' ', final_answer).strip()
        
        print(f"Answer humanized: {len(raw_answer)} -> {len(final_answer)} chars")
        
        # Deduplicate sources by title
        seen_titles = set()
        unique_sources = []
        for r in results:
            title = r["source"]
            if title not in seen_titles:
                seen_titles.add(title)
                unique_sources.append({
                    "title": title,
                    "path": r.get("metadata", {}).get("file_path") or r["source"],
                    "score": round(r["score"], 4)
                })
        
        return {
            "answer": final_answer,
            "domain_used": domain,
            "qtype_used": qtype,
            "auto_detected": auto_detected,
            "profile_used": profile,
            "profile_auto_detected": profile_auto_detected,
            "sources": unique_sources
        }
        
    except Exception as e:
        print(f"Error in answer_question: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

def health_check():
    try:
        _load_data()
        # also verify client init & key
        _ = _get_client()
        return {"ok": True, "embeddings": True, "openai": True, "error": None}
    except Exception as e:
        return {"ok": False, "embeddings": False, "openai": False, "error": str(e)}
