import os, json
import threading
import re
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
load_dotenv()

_client = None
_embeddings = None
_meta = None
_lock = threading.Lock()

# ---------- Humanization post-processor ----------
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

def humanize(text: str, qtype: str = "general") -> str:
    """
    Transform AI response into natural, human-sounding interview answer.
    Fast version with minimal overhead (~1-2ms).
    Allows longer responses for intro questions.
    """
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
    
    # Enforce proper line breaks for visual formatting
    text = _enforce_lines(text, min_lines=8 if qtype != "intro" else 10, max_lines=10 if qtype != "intro" else 14)
    
    # Remove markdown formatting
    text = text.replace("•", "").replace("*", "").replace("**", "")
    
    # Restore code blocks if present
    if has_code:
        for i, block in enumerate(code_blocks):
            text = text.replace(f"__CODE_BLOCK_{i}__", block)
    
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
            _client = OpenAI(api_key=api_key, timeout=30.0, max_retries=2)
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

        metadata_paths = [
            "meta.json", "api/meta.json", "store/meta.json", "kb_metadata.json"
        ]
        embeddings_paths = [
            "embeddings.npy", "api/embeddings.npy", "store/embeddings.npy", "kb_embeddings.npy"
        ]

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

            # Normalize each item to ensure consistent structure
            norm = []
            for d in raw:
                md = d.get("metadata") or {}
                norm.append({
                    "id": d.get("id"),
                    "text": d.get("text") or d.get("content") or "",
                    "metadata": {
                        "file_name": md.get("file_name") or md.get("filename") or "unknown",
                        "file_path": md.get("file_path") or md.get("path") or "unknown",
                        "persona": md.get("persona"),
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

def _get_embedding(text):
    client = _get_client()
    # Truncate text to avoid long embedding times (max ~8000 tokens)
    if len(text) > 32000:  # ~8000 tokens * 4 chars/token
        text = text[:32000]
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        timeout=3.0  # Reduced to 3 seconds for faster embedding generation
    )
    return np.array(response.data[0].embedding, dtype=np.float32)

def _search_similar(query_embedding, top_k=5, profile="krishna"):
    """
    Returns top-k KB chunks for the given query embedding,
    filtered by persona (if available), ranked by cosine similarity (dot product).
    """
    _load_data()

    # Ensure query is unit length (cosine)
    q = query_embedding.astype(np.float32)
    q = q / (np.linalg.norm(q) + 1e-12)

    # Fast cosine since both are normalized
    sims = _embeddings @ q  # shape: (num_docs,)

    # Allow None persona; broaden coverage for actual KB content
    profile_persona_map = {
        "krishna": {"ai", "de", None},
        "tejuu": {"bi", "ae", None},  # Fixed: include "bi" for BI content
    }

    indices = list(range(len(_meta)))
    if profile:
        wanted = profile_persona_map.get(profile, {None})
        filtered = [i for i in indices if _meta[i].get("metadata", {}).get("persona") in wanted]
        if filtered:
            indices = filtered
        else:
            print(f"Warning: No content for profile '{profile}' with personas {wanted}; using all content")

    # Rank within selected indices
    if not indices:
        return []

    local_scores = sims[indices]
    top_local = np.argsort(local_scores)[::-1][:top_k]
    top_indices = [indices[i] for i in top_local]

    results = []
    for idx in top_indices:
        doc = _meta[idx]
        meta = doc.get("metadata", {}) or {}
        results.append({
            "index": int(idx),
            "score": float(sims[idx]),
            "content": doc.get("text", ""),
            "source": meta.get("file_name") or meta.get("file_path") or "unknown",
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
    
    # Explicit code requests (very specific)
    explicit_code_phrases = ['write code', 'show code', 'write a function', 'write a script', 'code example', 'implement code', 'write python code', 'write sql code', 'write pyspark code']
    if any(phrase in question_lower for phrase in explicit_code_phrases):
        return 'code'
    
    # Explicit SQL requests
    explicit_sql_phrases = ['write sql', 'sql query', 'write a query', 'sql code', 'select statement']
    if any(phrase in question_lower for phrase in explicit_sql_phrases):
        return 'sql'
    
    # Interview/Behavioral indicators (but not intro)
    interview_phrases = ['describe a time', 'tell me about a time', 'give me an example', 'situation where', 'challenge you faced', 'difficult project', 'team conflict', 'leadership experience', 'mistake you made', 'how did you handle', 'star method', 'situation task action result']
    if any(phrase in question_lower for phrase in interview_phrases):
        return 'interview'
    
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
    """Detect the domain (de/ai/bi/ae) based on question content and profile."""
    q = question.lower()
    
    # Domain-specific signals
    ai_signals = ["llm", "langchain", "langgraph", "rag", "embedding", "prompt", "openai", "gpt",
                  "pytorch", "tensorflow", "mlflow", "fine-tune", "transformer", "agent",
                  "vector database", "pinecone", "weaviate", "hugging face", "model training"]
    de_signals = ["spark", "pyspark", "databricks", "etl", "elt", "delta lake", "kafka", "adf", 
                  "glue", "airflow", "data pipeline", "data lake", "streaming", "event hub"]
    ae_signals = ["dbt", "data modeling", "star schema", "fact table", "dimension table", "scd",
                  "slowly changing dimension", "dimensional model", "analytics engineer"]
    bi_signals = ["power bi", "tableau", "dax", "dashboard", "visualization", "stakeholder",
                  "report", "kpi", "business intelligence", "looker", "qlik"]
    
    def any_in(words):
        return any(w in q for w in words)
    
    if profile == "krishna":
        if any_in(ai_signals):
            return "ai"
        if any_in(de_signals):
            return "de"
        # Default bias for Krishna is AI/ML
        return "ai"
    else:  # tejuu
        if any_in(ae_signals):
            return "ae"
        if any_in(bi_signals):
            return "bi"
        # Default bias for Tejuu is BI
        return "bi"

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

def answer_question(question, mode="auto", profile="auto", **kwargs):
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
        
        if mode in ("de", "ai", "bi", "ae"):
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
        print(f"Searching for similar content for profile '{profile}'...")
        results = _search_similar(query_embedding, top_k=2, profile=profile)  # Reduced to 2 for speed
        print(f"Found {len(results)} relevant chunks for profile '{profile}'")
        
        # Debug: Print the sources of the results
        for i, result in enumerate(results):
            print(f"Result {i+1}: Source={result.get('source', 'Unknown')}, Persona={result.get('metadata', {}).get('persona', 'Unknown')}")
        
        # Build context safely with tighter length limits for speed
        if not results:
            context = ""
        else:
            parts = []
            total = 0
            for r in results:
                chunk = r["content"]
                # Reduced chunk size for faster processing
                if len(chunk) > 600: 
                    chunk = chunk[:600] + "..."
                frag = f"[{r['source']}] {chunk}"
                # Reduced total context to 1800 chars (was 2400)
                if total + len(frag) > 1800: 
                    break
                parts.append(frag)
                total += len(frag)
            context = "\n\n".join(parts)
        
        # Debug: Print context preview
        print(f"Context preview (first 500 chars): {context[:500]}...")
        
        # Get prompts for the selected profile
        profile_prompts = PROMPTS.get(profile, PROMPTS["krishna"])
        print(f"Debug: Profile='{profile}', Domain='{domain}', QType='{qtype}'")
        
        # Select system and user prompt based on domain and question type
        if profile == "krishna":
            system_prompt = profile_prompts["system_ai"] if domain == "ai" else profile_prompts["system_de"]
            
            if domain == "ai":
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
            if domain == "ae":
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
            else:  # bi
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
        
        # Get response from OpenAI (using faster model for better response time)
        print("Generating response with OpenAI...")
        client = _get_client()
        # Use more tokens for intro questions to allow 10-14 sentences
        max_tokens = 1000 if qtype == "intro" else 800
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Faster and cheaper than gpt-4o
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,        # Sweet spot for natural but focused
            top_p=0.92,             # Slightly tighter sampling
            frequency_penalty=0.3,  # Reduces buzzword repetition
            presence_penalty=0.0,
            max_tokens=max_tokens,  # 1000 for intros (10-14 sentences), 800 for regular (8-10 lines)
            timeout=15.0,           # Reduced from 30s to 15s for faster response
            stream=False
        )
        print("Response generated successfully")
        
        # Apply humanization post-processor
        raw_answer = response.choices[0].message.content
        final_answer = humanize(raw_answer, qtype=qtype)
        print(f"Answer humanized: {len(raw_answer)} -> {len(final_answer)} chars")
        
        return {
            "answer": final_answer,
            "domain_used": domain,
            "qtype_used": qtype,
            "auto_detected": auto_detected,
            "profile_used": profile,
            "profile_auto_detected": profile_auto_detected,
            "sources": [
                {
                    "title": r["source"],
                    "path": r.get("metadata", {}).get("file_path") or r["source"],
                    "score": round(r["score"], 4)
                } for r in results
            ]
        }
        
    except Exception as e:
        print(f"Error in answer_question: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}

def health_check():
    try:
        _load_data()
        return {"ok": True, "embeddings": True, "error": None}
    except Exception as e:
        return {"ok": False, "embeddings": False, "error": str(e)}
