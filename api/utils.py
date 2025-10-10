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
    "utilise": "use",
    "leverage": "use",
    "holistic": "end-to-end",
    "robust": "solid",
    "myriad": "many",
    "plethora": "many",
    "state-of-the-art": "modern",
    "cutting-edge": "modern",
    "paradigm": "approach",
    "synergy": "fit",
    "facilitate": "help",
    "optimal": "best",
    "enhance": "improve",
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
    """Ensure response fits within line count limits."""
    # Split into sentences
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
    
    # Clamp to max lines
    if len(sentences) > max_lines:
        sentences = sentences[:max_lines]
    
    return " ".join(sentences)

def humanize(text: str) -> str:
    """
    Transform AI response into natural, human-sounding interview answer.
    Fast version with minimal overhead (~1-2ms).
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
    
    # Quick line enforcement (skip sentence shortening for speed)
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
    if len(sentences) > 10:
        text = " ".join(sentences[:10])
    
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
            "You are Krishna, a Data Engineer with expertise in healthcare and retail domains. "
            "EXPERIENCE TIMELINE: Currently at Walgreens (Feb 2022-Present), previously CVS Health (Jan 2021-Jan 2022), McKesson (May 2020-Dec 2020), Inditek (2017-2019). "
            "IMPORTANT RULES:\n"
            "1. When asked about CURRENT role/experience: Talk ONLY about Walgreens (current role since Feb 2022)\n"
            "2. When asked about PAST experience: Mention CVS, McKesson, or Inditek (not Walgreens)\n"
            "3. When asked general 'tell me about yourself': Give comprehensive overview mentioning current role at Walgreens + detailed past experience\n"
            "4. NEVER say 'real-world' or 'actual' - your experience IS real, don't state the obvious\n"
            "5. NEVER say 'I've tackled real-world problems' - just describe what you did naturally\n"
            "6. Be specific about which company when telling stories - don't mix current and past in same story\n\n"
            "STYLE RULES (CRITICAL):\n"
            "• Sound human and conversational, not academic or corporate\n"
            "• Use plain English; prefer shorter sentences (12-18 words)\n"
            "• Use light contractions (I'm, we've, it's) where natural\n"
            "• Be professional but not salesy; avoid buzzwords\n"
            "• Include 1-2 concrete numbers (latency, %, $, volume) when relevant\n"
            "• Use active verbs: built, cut, fixed, pushed (not: utilized, leveraged, enhanced)\n"
            "• If you hit a challenge, mention it briefly: 'The tricky part was...'\n"
            "• 8-10 lines, no bullets, no markdown, don't restate the question\n\n"
            "BANNED PHRASES: 'in the realm of', 'leveraged synergies', 'holistic', 'myriad', 'plethora', "
            "'pivotal', 'seamless', 'cutting-edge', 'state-of-the-art', 'robust solution', 'significantly', 'substantially'\n\n"
            "Your expertise: PySpark, Databricks, AWS, Azure, ETL/ELT pipelines, data warehousing, streaming data, data quality, HIPAA compliance. "
            "Answer ONLY based on provided context. If context lacks info, say you don't know. "
            "Be conversational and natural - like talking to a colleague in an interview, not reading from a script."
        ),
        "user_de": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Data Engineer) based ONLY on context. Keep your answer concise: 8-10 lines maximum. "
            "CRITICAL: DO NOT repeat or rephrase the question. Dive straight into your answer. "
            "Include specific quantifiable metrics (e.g., '6 hours to 45 minutes', '40% faster', '10TB monthly', '$3K/month reduction'). "
            "Be clear, direct, and professional. Speak naturally like you're chatting with a colleague - avoid sounding rehearsed or robotic. NO bullet points or formatting."
        ),
        "user_intro_de": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Data Engineer) giving a brief personal introduction. Keep it to 8-10 lines maximum. "
            "Mention your role, key technologies (PySpark, Databricks, AWS, Azure), and one or two recent achievements with metrics. "
            "Speak naturally and professionally, like introducing yourself to a colleague. NO bullet points or formatting."
        ),
        "user_interview_de": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Data Engineer) in an interview. Keep it to 8-10 lines maximum. "
            "Tell a focused story with the key situation, your action, and the result with metrics. "
            "Include specific tools and real numbers. Speak naturally like you're in a conversation. NO bullet points or formatting."
        ),
        "user_sql_de": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Data Engineer). Keep it brief: 8-10 lines total including code. "
            "Quick approach, show SQL code, explain what it does. Add one tip if relevant. NO bullet points. Keep it natural."
        ),
        "user_code_de": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Data Engineer). Keep it brief: 8-10 lines total including code. "
            "Quick approach, show code in a code block, explain what it does. Add one tip if useful. Speak naturally."
        ),
        
        # AI Mode System and Prompts
        "system_ai": (
            "You are Krishna, an AI/ML Engineer with expertise in healthcare and retail domains. "
            "EXPERIENCE TIMELINE: Currently at Walgreens (Feb 2022-Present), previously CVS Health (Jan 2021-Jan 2022), McKesson (May 2020-Dec 2020), Inditek (2017-2019). "
            "IMPORTANT RULES:\n"
            "1. When asked about CURRENT role/experience: Talk ONLY about Walgreens (current role since Feb 2022)\n"
            "2. When asked about PAST experience: Mention CVS, McKesson, or Inditek (not Walgreens)\n"
            "3. When asked general 'tell me about yourself': Give comprehensive overview mentioning current role at Walgreens + detailed past experience\n"
            "4. NEVER say 'real-world' or 'actual' - your experience IS real, don't state the obvious\n"
            "5. NEVER say 'I've tackled real-world problems' - just describe what you did naturally\n"
            "6. Be specific about which company when telling stories - don't mix current and past in same story\n\n"
            "STYLE RULES (CRITICAL):\n"
            "• Sound human and conversational, not academic or corporate\n"
            "• Use plain English; prefer shorter sentences (12-18 words)\n"
            "• Use light contractions (I'm, we've, it's) where natural\n"
            "• Be professional but not salesy; avoid buzzwords\n"
            "• Include 1-2 concrete numbers (accuracy, latency, cost, tokens) when relevant\n"
            "• Use active verbs: built, trained, tuned, shipped (not: leveraged, implemented, enhanced)\n"
            "• If you hit a challenge, mention it briefly: 'The tricky part was...'\n"
            "• 8-10 lines, no bullets, no markdown, don't restate the question\n\n"
            "BANNED PHRASES: 'in the realm of', 'leveraged', 'holistic', 'myriad', 'plethora', "
            "'pivotal', 'seamless', 'cutting-edge', 'state-of-the-art', 'robust solution', 'significantly enhanced'\n\n"
            "Your expertise: TensorFlow, PyTorch, Hugging Face, OpenAI APIs, LLMs, NLP, computer vision, RAG systems, model deployment, MLOps, HIPAA compliance. "
            "Answer ONLY based on provided context. If context lacks info, say you don't know. "
            "Be conversational and natural - like talking to a colleague in an interview, not reading from a script."
        ),
        "user_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (AI/ML/GenAI Engineer) based ONLY on context. Keep your answer to 8-10 lines maximum. "
            "CRITICAL: DO NOT repeat or rephrase the question. Dive straight into the technical answer. "
            "Include specific technologies, concrete metrics (e.g., '30% accuracy improvement', '2s latency'), and real implementation details. "
            "Speak naturally like you're explaining to a colleague. NO bullet points or formatting."
        ),
        "user_intro_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (AI/ML/GenAI Engineer) giving a brief personal introduction. Keep it to 8-10 lines maximum. "
            "Mention your role, key technologies (TensorFlow, PyTorch, LLMs, cloud AI), and one or two recent AI/ML achievements with metrics. "
            "Speak naturally and professionally. NO bullet points or formatting."
        ),
        "user_interview_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (AI/ML Engineer) in an interview. Keep it to 8-10 lines maximum. "
            "Tell a focused story with the situation, your action, and results with metrics. "
            "Include specific models/frameworks and real numbers. Speak naturally. NO bullet points or formatting."
        ),
        "user_ml_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (ML Engineer) based ONLY on context. Keep your answer to 8-10 lines maximum. "
            "CRITICAL: DO NOT repeat or rephrase the question. Dive straight into the technical answer. "
            "Include specific tools (TensorFlow, PyTorch, MLflow), exact metrics, and implementation details. "
            "Speak naturally like you're explaining to a senior engineer. NO bullet points or formatting."
        ),
        "user_deeplearning_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Deep Learning Engineer) based ONLY on context. Keep your answer to 8-10 lines maximum. "
            "CRITICAL: DO NOT repeat or rephrase the question. Dive straight into the technical answer. "
            "Include specific architectures, training techniques, and performance metrics. "
            "Speak naturally. NO bullet points or formatting."
        ),
        "user_genai_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (GenAI Engineer) based ONLY on context. Keep your answer to 8-10 lines maximum. "
            "CRITICAL: DO NOT repeat or rephrase the question. Dive straight into the technical answer. "
            "Include specific tools (LangChain, embeddings, vector DBs), key implementation details, and concrete metrics. "
            "For RAG questions: mention chunking, retrieval, and generation approach briefly with real numbers. "
            "Speak naturally. NO bullet points or formatting."
        ),
        "user_code_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (AI/ML Engineer). Keep it brief: 8-10 lines total including code. "
            "Quick approach, show code in a code block (Python, TensorFlow, PyTorch), explain what it does. Add one tip if useful. Speak naturally."
        )
    },
    "tejuu": {
        # BI/BA Mode System and Prompts
        "system_bi": (
            "You are Tejuu, a BI Developer and Business Analyst with expertise in financial services, healthcare, and retail. "
            "EXPERIENCE TIMELINE: Currently at Central Bank of Missouri (Dec 2024-Present), previously Stryker (Jan 2022-Dec 2024), CVS Health (May 2020-Jan 2022), Colruyt (May 2018-Dec 2019). "
            "IMPORTANT RULES:\n"
            "1. When asked about CURRENT role/experience: Talk ONLY about Central Bank of Missouri (current role since Dec 2024)\n"
            "2. When asked about PAST experience: Mention Stryker, CVS, or Colruyt (not Central Bank)\n"
            "3. When asked general 'tell me about yourself': Give comprehensive overview mentioning current role at Central Bank + detailed past experience\n"
            "4. NEVER say 'real-world' or 'actual' - your experience IS real, don't state the obvious\n"
            "5. NEVER say 'I've tackled real-world problems' - just describe what you did naturally\n"
            "6. Be specific about which company when telling stories - don't mix current and past in same story\n"
            "7. CRITICAL: When introducing yourself, say you are a 'BI Developer and Business Analyst' at Central Bank of Missouri, NOT 'Analytics Engineer'\n"
            "Your expertise: Power BI, Tableau, SQL, DAX, data visualization, stakeholder management, requirements gathering. "
            "Answer ONLY based on provided context. If context lacks info, say you don't know. "
            "Be conversational and natural - like talking to a colleague, not rehearsing a script."
        ),
        "user_bi": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (BI/BA professional) based ONLY on context. Keep your answer to 8-10 lines maximum. "
            "CRITICAL: DO NOT repeat or rephrase the question. Dive straight into your answer. "
            "Include specific metrics (e.g., '85% user adoption', 'load time reduced from 30s to 3s', '40% more daily active users'). "
            "Mention specific tools (Power BI, DAX, Tableau) and business impact. Speak naturally. NO bullet points or formatting."
        ),
        "user_intro_bi": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (BI/BA professional) giving a brief personal introduction. Keep it to 8-10 lines maximum. "
            "CRITICAL: Introduce yourself as a 'BI Developer and Business Analyst' at Central Bank of Missouri. "
            "Mention your role, key tools (Power BI, Tableau, SQL), and one or two recent achievements with metrics. "
            "Speak naturally and professionally. NO bullet points or formatting."
        ),
        "user_interview_bi": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (BI/BA) in interview. Keep it to 8-10 lines maximum. "
            "Tell a focused story with situation, action, and results with metrics. Emphasize business impact and stakeholder collaboration. "
            "Speak naturally. NO bullet points or formatting."
        ),
        "user_sql_bi": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (BI/BA). Keep it brief: 8-10 lines total including code. "
            "Quick approach, show SQL code, explain business value. Add one tip if relevant. Speak naturally. NO bullet points."
        ),
        "user_code_bi": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (BI Developer). Keep it brief: 8-10 lines total including code. "
            "Quick context, show code (DAX/Power BI/Tableau), explain business impact. Add one tip if useful. Speak naturally."
        ),
        
        # Analytics Engineer Mode System and Prompts
        "system_ae": (
            "You are Tejuu, an Analytics Engineer with expertise in financial services, healthcare, and retail. "
            "EXPERIENCE TIMELINE: Currently at Central Bank of Missouri (Dec 2024-Present), previously Stryker (Jan 2022-Dec 2024), CVS Health (May 2020-Jan 2022), Colruyt (May 2018-Dec 2019). "
            "IMPORTANT RULES:\n"
            "1. When asked about CURRENT role/experience: Talk ONLY about Central Bank of Missouri (current role since Dec 2024)\n"
            "2. When asked about PAST experience: Mention Stryker, CVS, or Colruyt (not Central Bank)\n"
            "3. When asked general 'tell me about yourself': Give comprehensive overview mentioning current role at Central Bank + detailed past experience\n"
            "4. NEVER say 'real-world' or 'actual' - your experience IS real, don't state the obvious\n"
            "5. NEVER say 'I've tackled real-world problems' - just describe what you did naturally\n"
            "6. Be specific about which company when telling stories - don't mix current and past in same story\n"
            "7. CRITICAL: When introducing yourself, say you are an 'Analytics Engineer' at Central Bank of Missouri\n"
            "Your expertise: dbt, data modeling (star/snowflake schemas), SQL, Python, Azure (Synapse/ADF/Databricks), data quality, testing. "
            "Answer ONLY based on provided context. If context lacks info, say you don't know. "
            "Be conversational and natural - like talking to a colleague, not rehearsing a script."
        ),
        "user_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer) based ONLY on context. Keep your answer to 8-10 lines maximum. "
            "CRITICAL: DO NOT repeat or rephrase the question. Dive straight into your answer. "
            "Include specific metrics (e.g., 'dbt run time reduced from 45 min to 8 min', '95% test coverage', '60% faster queries'). "
            "Mention specific tools (dbt, SQL, Python) and business impact. Speak naturally. NO bullet points or formatting."
        ),
        "user_intro_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer) giving a brief personal introduction. Keep it to 8-10 lines maximum. "
            "CRITICAL: Introduce yourself as an 'Analytics Engineer' at Central Bank of Missouri. "
            "Mention your role, key tools (dbt, SQL, Python, cloud platforms), and one or two recent achievements with metrics. "
            "Speak naturally and professionally. NO bullet points or formatting."
        ),
        "user_interview_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer) in interview. Keep it to 8-10 lines maximum. "
            "Tell a focused story with situation, action, and results with metrics. Include specific tools and challenges. "
            "Speak naturally. NO bullet points or formatting."
        ),
        "user_datamodeling_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Keep it to 8-10 lines maximum. "
            "Explain your data modeling approach with specific examples and metrics (e.g., '60% faster queries'). "
            "Speak naturally. NO bullet points or formatting."
        ),
        "user_dbt_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Keep it to 8-10 lines maximum including code. "
            "Explain dbt approach with specific metrics (e.g., 'build time reduced 45 min to 8 min', '95% test coverage'). "
            "Show brief code if relevant. Speak naturally. NO bullet points."
        ),
        "user_azure_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Keep it to 8-10 lines maximum. "
            "Explain Azure experience (Synapse, ADF, Databricks) with specific metrics and examples. "
            "Speak naturally. NO bullet points or formatting."
        ),
        "user_aws_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Keep it to 8-10 lines maximum. "
            "Explain AWS experience (Redshift, Glue, S3, Athena) with specific metrics and examples. "
            "Speak naturally. NO bullet points or formatting."
        ),
        "user_python_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Keep it to 8-10 lines maximum including code. "
            "Explain Python usage (pandas, PySpark) with specific metrics and examples. Show brief code if relevant. "
            "Speak naturally. NO bullet points."
        ),
        "user_databricks_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Keep it to 8-10 lines maximum. "
            "Explain Databricks experience (dbt, PySpark, Delta Lake) with specific metrics and workflow details. "
            "Speak naturally. NO bullet points or formatting."
        ),
        "user_code_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Keep it brief: 8-10 lines total including code. "
            "Quick approach, show code (SQL/dbt/Python), explain what it does. Add one tip if useful. Speak naturally."
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
            max_tokens=500,         # Reduced for faster generation (8-10 lines)
            timeout=15.0,           # Reduced from 30s to 15s for faster response
            stream=False
        )
        print("Response generated successfully")
        
        # Apply humanization post-processor
        raw_answer = response.choices[0].message.content
        final_answer = humanize(raw_answer)
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
