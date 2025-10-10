import os, json
import threading
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI
from sklearn.metrics.pairwise import cosine_similarity

load_dotenv()

_client = None
_embeddings = None
_meta = None
_lock = threading.Lock()

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
            "6. Be specific about which company when telling stories - don't mix current and past in same story\n"
            "Your expertise: PySpark, Databricks, AWS, Azure, ETL/ELT pipelines, data warehousing, streaming data, data quality, HIPAA compliance. "
            "Answer ONLY based on provided context. If context lacks info, say you don't know. "
            "Be conversational and natural - like talking to a colleague, not rehearsing a script."
        ),
        "user_de": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Data Engineer) based ONLY on context. Give comprehensive, detailed responses about data engineering: ETL/ELT pipelines, data warehousing, streaming data, data lakes, and infrastructure. "
            "CRITICAL: Include specific quantifiable metrics such as: processing time reductions (e.g., '6 hours to 45 minutes'), performance improvements (e.g., '40% faster'), data volume handled (e.g., '10TB monthly'), cost savings (e.g., '$3K/month reduction'), latency improvements, throughput increases, or resource optimization percentages. "
            "Provide thorough explanations with specific tools/technologies, implementation details, concrete metrics, and measurable business impact. NO bullet points or formatting. Keep it natural and conversational like in a professional interview."
        ),
        "user_intro_de": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Data Engineer) giving a comprehensive personal introduction. "
            "Provide a detailed intro covering: your role as a Data Engineer, key technologies you work with (PySpark, Databricks, AWS, Azure), your experience level, and what you're passionate about. "
            "Include specific recent achievements, projects, and quantifiable results. "
            "NO bullet points, headings, formatting, or code examples. Keep it conversational and genuine - like introducing yourself to a colleague."
        ),
        "user_interview_de": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Data Engineer) in an interview. Tell a real story from your data engineering experience using STAR pattern. "
            "Include specific tools, technologies, metrics, and challenges you faced. "
            "If the question is about teamwork, leadership, or collaboration, then mention those aspects. Otherwise, focus on the technical story. "
            "Be honest about what went wrong and how you fixed it. NO bullet points or formatting. Keep it natural and conversational."
        ),
        "user_sql_de": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Data Engineer). Explain your approach naturally, show the SQL code, then explain what it does in simple terms. "
            "Mention any gotchas or tips from your experience. NO bullet points or formatting. Keep it clear and natural."
        ),
        "user_code_de": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Data Engineer). The user is explicitly asking for code, so provide a practical code example. "
            "Explain your approach naturally, show the code in a code block, then explain what it does clearly. "
            "Mention any gotchas or tips from your experience. Keep it natural and conversational."
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
            "6. Be specific about which company when telling stories - don't mix current and past in same story\n"
            "Your expertise: TensorFlow, PyTorch, Hugging Face, OpenAI APIs, LLMs, NLP, computer vision, RAG systems, model deployment, MLOps, HIPAA compliance. "
            "Answer ONLY based on provided context. If context lacks info, say you don't know. "
            "Be conversational and natural - like talking to a colleague, not rehearsing a script."
        ),
        "user_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (AI/ML/GenAI Engineer) based ONLY on context. Give comprehensive, detailed technical responses about AI/ML/GenAI projects, model development, LLMs, RAG systems, and AI system architecture. "
            "CRITICAL: NO generic intros - dive STRAIGHT into answering the technical question with specific implementation details. "
            "Include: exact technologies/frameworks used, specific implementation approaches, concrete metrics and results from Walgreens/CVS/McKesson projects, technical challenges and solutions, architecture decisions and trade-offs. "
            "For RAG/LangChain questions: explain complete pipeline with all components, tools, and configurations. "
            "For MLOps questions: explain deployment strategy, CI/CD setup, monitoring approach, versioning system. "
            "For optimization questions: provide specific techniques used, before/after metrics, implementation details. "
            "NO bullet points or formatting. Keep it natural and conversational like in a professional interview."
        ),
        "user_intro_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (AI/ML/GenAI Engineer) giving a comprehensive personal introduction. "
            "Provide a detailed intro covering: your role as an AI/ML Engineer, key technologies you work with (TensorFlow, PyTorch, LLMs, cloud AI services), your experience level, and what you're passionate about. "
            "Include specific recent achievements, projects, and quantifiable results. "
            "NO bullet points, headings, formatting, or code examples. Keep it conversational and genuine - like introducing yourself to a colleague."
        ),
        "user_interview_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (AI/ML Engineer) in an interview. Tell a real story from your AI/ML experience using STAR pattern. "
            "Include specific models, frameworks, metrics, and challenges you faced. "
            "Focus on AI model development, deployment, performance optimization, or GenAI implementation. Mention collaboration with data scientists and product teams. "
            "Be honest about what went wrong and how you fixed it. NO bullet points or formatting. Keep it natural and conversational."
        ),
        "user_ml_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (ML Engineer) based ONLY on context. Give comprehensive, detailed technical responses about machine learning: model training, feature engineering, model selection, hyperparameter tuning, and ML pipelines. "
            "CRITICAL: NO generic intros like 'I'm an ML Engineer with X years...' - dive STRAIGHT into answering the technical question. "
            "Include: specific implementation details, concrete examples from Walgreens/CVS/McKesson projects, exact metrics and results, specific tools/frameworks used (TensorFlow, PyTorch, MLflow, etc.), technical challenges faced and how you solved them. "
            "For MLflow questions: explain experiment tracking setup, model registry usage, versioning strategy, CI/CD integration with Azure DevOps/AKS. "
            "For model questions: mention specific architectures, training approaches, validation strategies, deployment patterns. "
            "NO bullet points, headings, or formatting. Keep it natural like explaining to a senior engineer in an interview."
        ),
        "user_deeplearning_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Deep Learning Engineer) based ONLY on context. Give comprehensive, detailed technical responses about deep learning: neural networks, CNNs, RNNs, Transformers, and advanced architectures. "
            "CRITICAL: NO generic intros - dive STRAIGHT into answering the technical question. "
            "Include: specific architectures used, layer configurations, training techniques (batch normalization, dropout, learning rate schedules), optimization strategies, performance metrics and improvements. "
            "For implementation questions: explain the exact approach, frameworks used (TensorFlow/PyTorch), training infrastructure (GPUs/distributed training), and production deployment. "
            "NO bullet points, headings, or formatting. Keep it natural like explaining to a senior engineer in an interview."
        ),
        "user_genai_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (GenAI Engineer) based ONLY on context. Give comprehensive, detailed technical responses about generative AI: LLMs, RAG systems, LangChain, LangGraph, embeddings, vector databases, and prompt engineering. "
            "CRITICAL: NO generic intros - dive STRAIGHT into answering the technical question. "
            "Include: specific implementation details for RAG pipelines (chunking strategy with exact token sizes and overlap, embedding models used, vector DB configuration), LangChain/LangGraph components and workflow design, prompt templates and optimization techniques, retrieval strategies (top_k, similarity thresholds, hybrid search), generation parameters (temperature, max_tokens), specific metrics (accuracy improvements, latency reductions, hallucination rates). "
            "For LangGraph questions: explain graph structure, node definitions, conditional routing logic, state management, error handling patterns. "
            "For FastAPI questions: explain project structure (routers, services, models), async implementation, Pydantic validation, error handling patterns, Docker/K8s deployment. "
            "For RAG pipeline questions: walk through complete flow from ingestion → chunking → embedding → storage → retrieval → generation, including all tools and technologies at each step. "
            "NO bullet points, headings, or formatting. Keep it natural like explaining to a senior engineer in an interview."
        ),
        "user_code_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (AI/ML Engineer). The user is explicitly asking for code, so provide a practical AI/ML code example. "
            "Explain your approach naturally, show the code in a code block (Python, TensorFlow, PyTorch, etc.), then explain what it does clearly. "
            "Mention any challenges or tips from your experience with model training, deployment, or optimization. Keep it natural and conversational."
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
            "Answer as Tejuu (BI/BA professional) based ONLY on context. Give comprehensive, detailed responses about dashboards, reports, "
            "Power BI, Tableau, data visualization, and stakeholder collaboration. "
            "CRITICAL: Include specific quantifiable metrics such as: dashboard adoption rates (e.g., '85% user adoption'), performance improvements (e.g., 'load time reduced from 30s to 3s'), user engagement increases (e.g., '40% more daily active users'), time-to-insight reductions (e.g., 'from 2 days to 2 hours'), report usage statistics, stakeholder satisfaction scores, or decision-making speed improvements. "
            "Provide thorough explanations with specific tools (Power BI, DAX, Tableau), implementation details, concrete metrics, and measurable business impact. NO bullet points or formatting. Keep it natural and conversational like in a professional interview."
        ),
        "user_intro_bi": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (BI/BA professional) giving a comprehensive personal introduction. "
            "CRITICAL: Introduce yourself as a 'BI Developer and Business Analyst' at Central Bank of Missouri, NOT 'Analytics Engineer'. "
            "Provide a detailed intro covering: your role as a BI Developer and Business Analyst, key technologies you work with (Power BI, Tableau, SQL), your experience level, and what you're passionate about. "
            "Include specific recent achievements, projects, and quantifiable results. "
            "NO bullet points, headings, formatting, or code examples. Keep it conversational and genuine - like introducing yourself to a colleague."
        ),
        "user_interview_bi": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (BI/BA) in interview using STAR pattern. Tell a real story emphasizing business impact, stakeholder "
            "collaboration, dashboard adoption, and how your work drove decisions. Include challenges, what you learned, and results "
            "with metrics. NO bullet points. Keep it genuine and conversational."
        ),
        "user_sql_bi": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (BI/BA). Explain your approach naturally, show the SQL code, then explain the business value and "
            "how stakeholders use it in dashboards. Mention any tips from your experience. NO bullet points. Keep it clear."
        ),
        "user_code_bi": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (BI Developer). The user is explicitly asking for code, so provide a practical BI/analytics code example. "
            "Start with business context, show the code in a code block (DAX/Power BI/Tableau), explain business impact "
            "and how it helps stakeholders. Mention any challenges or tips from your experience. Keep it natural and conversational."
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
            "Answer as Tejuu (Analytics Engineer) based ONLY on context. Give comprehensive, detailed responses about analytics engineering, "
            "data modeling, dbt, transformations, data quality, and building reliable data products. "
            "CRITICAL: Include specific quantifiable metrics such as: model build time improvements (e.g., 'dbt run time reduced from 45 min to 8 min'), data quality test coverage (e.g., '95% test coverage'), data freshness improvements (e.g., 'from daily to hourly updates'), transformation performance gains (e.g., '60% faster queries'), lineage coverage percentages, data accuracy improvements, pipeline reliability metrics (e.g., '99.5% uptime'), or downstream analytics adoption rates. "
            "Provide thorough explanations with specific tools (dbt, SQL, Python, Azure/AWS), implementation details, concrete metrics, and measurable business impact. NO bullet points or formatting. Keep it natural and conversational like in a professional interview."
        ),
        "user_intro_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer) giving a comprehensive personal introduction. "
            "CRITICAL: Introduce yourself as an 'Analytics Engineer' at Central Bank of Missouri. "
            "Provide a detailed intro covering: your role as an Analytics Engineer, key technologies you work with (dbt, SQL, Python, cloud platforms), your experience level, and what you're passionate about. "
            "Include specific recent achievements, projects, and quantifiable results. "
            "NO bullet points, headings, formatting, or code examples. Keep it conversational and genuine - like introducing yourself to a colleague."
        ),
        "user_interview_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer) in interview using STAR pattern. Tell a real story about building data models, "
            "dbt transformations, or improving data quality. Include technical details (tools, approaches), collaboration with data "
            "engineers and analysts, challenges faced, and business impact. NO bullet points. Keep it genuine."
        ),
        "user_datamodeling_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Explain data modeling approach naturally - dimensional modeling, star schemas, "
            "fact/dimension tables, SCD handling. "
            "CRITICAL: Include specific quantifiable metrics such as: query performance improvements (e.g., '60% faster queries'), model complexity reductions, data accuracy improvements, storage optimization percentages, or downstream report performance gains. "
            "Show examples from your experience with concrete metrics, explain measurable business benefits. "
            "NO bullet points. Keep it practical."
        ),
        "user_dbt_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Explain dbt approach naturally - models, tests, macros, incremental processing. "
            "CRITICAL: Include specific metrics like: build time improvements, test coverage percentages, data freshness gains, transformation performance. "
            "Show code examples, explain your workflow with concrete metrics, mention tips from experience. NO bullet points. Keep it practical."
        ),
        "user_azure_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Explain Azure experience naturally - Synapse, ADF, Databricks, ADLS. "
            "CRITICAL: Include specific metrics like: pipeline performance improvements, cost optimizations, processing time reductions, reliability percentages. "
            "Focus on analytics workloads, orchestration, and building reliable pipelines. Show examples with concrete metrics, explain measurable business value. "
            "NO bullet points. Keep it practical."
        ),
        "user_aws_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Explain AWS experience naturally - Redshift, Glue, S3, Athena. "
            "CRITICAL: Include specific metrics like: query performance gains, cost savings, data processing improvements, transformation efficiency. "
            "Focus on analytics workloads, data warehousing, and transformations. Show examples with concrete metrics, explain measurable business value. "
            "NO bullet points. Keep it practical."
        ),
        "user_python_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Explain Python usage naturally - pandas for data transformation, PySpark for "
            "large-scale processing, automation scripts. "
            "CRITICAL: Include specific metrics like: processing time improvements, automation efficiency gains, performance optimizations. "
            "Show code examples with concrete metrics, explain when you use each tool. "
            "NO bullet points. Keep it practical."
        ),
        "user_databricks_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Explain Databricks experience naturally - running dbt, PySpark transformations, "
            "Delta Lake, orchestration. "
            "CRITICAL: Include specific metrics like: runtime improvements, cluster optimization results, transformation performance gains. "
            "Focus on analytics use cases. Show examples with concrete metrics, explain workflow. NO bullet points."
        ),
        "user_code_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). The user is explicitly asking for code, so provide a practical analytics engineering code example. "
            "Explain your thinking naturally, show the code in a code block (SQL/dbt/Python), explain what it does "
            "and why it's designed that way. Mention data quality, testing, or tips from your experience. Keep it natural and conversational."
        )
    }
}

def _get_client():
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        # Temporarily unset proxy environment variables that might interfere
        old_http_proxy = os.environ.pop('HTTP_PROXY', None)
        old_https_proxy = os.environ.pop('HTTPS_PROXY', None)
        old_http_proxy_lower = os.environ.pop('http_proxy', None)
        old_https_proxy_lower = os.environ.pop('https_proxy', None)
        
        try:
            # Initialize with minimal parameters and default timeout
            _client = OpenAI(api_key=api_key, timeout=30.0, max_retries=2)
            print("OpenAI client initialized successfully")
        except Exception as e:
            print(f"Error initializing OpenAI client: {e}")
            raise ValueError(f"Failed to initialize OpenAI client: {e}")
        finally:
            # Restore proxy environment variables if they were set
            if old_http_proxy:
                os.environ['HTTP_PROXY'] = old_http_proxy
            if old_https_proxy:
                os.environ['HTTPS_PROXY'] = old_https_proxy
            if old_http_proxy_lower:
                os.environ['http_proxy'] = old_http_proxy_lower
            if old_https_proxy_lower:
                os.environ['https_proxy'] = old_https_proxy_lower
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
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        timeout=5.0  # Reduced to 5 seconds for faster embedding generation
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

    # Personas present in your KB: "ai", "de"
    profile_persona_map = {
        "krishna": {"ai", "de"},
        # Keep these for future BI/AE content; will fall back if none present
        "tejuu": {"ae", "tejuu"},
    }

    indices = list(range(len(_meta)))
    if profile:
        wanted = profile_persona_map.get(profile, {profile})
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
        meta = doc.get("metadata", {})
        results.append({
            "index": int(idx),
            "score": float(sims[idx]),
            "content": doc.get("text", ""),
            "source": meta.get("file_name") or meta.get("file_path", "unknown"),
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

def answer_question(question, mode="auto", profile="krishna", **kwargs):
    try:
        print(f"Processing question for profile '{profile}': {question[:50]}...")
        
        # Auto-detect mode if not specified
        auto_detected = False
        if mode == "auto":
            mode = detect_question_type(question)
            auto_detected = True
        
        # Detect question type for sub-mode selection
        detected_type = detect_question_type(question)
        
        # Get query embedding
        print("Generating query embedding...")
        query_embedding = _get_embedding(question)
        print("Query embedding generated successfully")
        
        # Search for similar content (reduced top_k for faster processing)
        print(f"Searching for similar content for profile '{profile}'...")
        results = _search_similar(query_embedding, top_k=3, profile=profile)  # Reduced from 5 to 3
        print(f"Found {len(results)} relevant chunks for profile '{profile}'")
        
        # Debug: Print the sources of the results
        for i, result in enumerate(results):
            print(f"Result {i+1}: Source={result.get('source', 'Unknown')}, Persona={result.get('metadata', {}).get('persona', 'Unknown')}")
        
        # Build context safely with length limits
        if not results:
            context = ""
        else:
            parts = []
            total = 0
            for r in results:
                chunk = r["content"]
                if len(chunk) > 800: 
                    chunk = chunk[:800] + "..."
                frag = f"[{r['source']}] {chunk}"
                # Cap total context ~2400 chars
                if total + len(frag) > 2400: 
                    break
                parts.append(frag)
                total += len(frag)
            context = "\n\n".join(parts)
        
        # Debug: Print context preview
        print(f"Context preview (first 500 chars): {context[:500]}...")
        
        # Get prompts for the selected profile
        profile_prompts = PROMPTS.get(profile, PROMPTS["krishna"])
        print(f"Debug: Profile='{profile}', Mode='{mode}', Detected type='{detected_type}'")
        print(f"Debug: Available profiles in PROMPTS: {list(PROMPTS.keys())}")
        
        # Select prompt based on main mode and detected question type
        if profile == "krishna":
            if mode == "de":
                # DE Mode - check detected type for sub-mode
                if detected_type == "intro":
                    user_prompt = profile_prompts["user_intro_de"].format(context=context, question=question)
                    system_prompt = profile_prompts["system_de"]
                elif detected_type == "interview":
                    user_prompt = profile_prompts["user_interview_de"].format(context=context, question=question)
                    system_prompt = profile_prompts["system_de"]
                elif detected_type == "sql":
                    user_prompt = profile_prompts["user_sql_de"].format(context=context, question=question)
                    system_prompt = profile_prompts["system_de"]
                elif detected_type == "code":
                    user_prompt = profile_prompts["user_code_de"].format(context=context, question=question)
                    system_prompt = profile_prompts["system_de"]
                else:  # default DE
                    user_prompt = profile_prompts["user_de"].format(context=context, question=question)
                    system_prompt = profile_prompts["system_de"]
            elif mode == "ai":
                # AI/ML/GenAI Mode - check detected type for sub-mode
                if detected_type == "intro":
                    user_prompt = profile_prompts["user_intro_ai"].format(context=context, question=question)
                    system_prompt = profile_prompts["system_ai"]
                elif detected_type == "interview":
                    user_prompt = profile_prompts["user_interview_ai"].format(context=context, question=question)
                    system_prompt = profile_prompts["system_ai"]
                elif detected_type == "ml":
                    user_prompt = profile_prompts["user_ml_ai"].format(context=context, question=question)
                    system_prompt = profile_prompts["system_ai"]
                elif detected_type == "deeplearning":
                    user_prompt = profile_prompts["user_deeplearning_ai"].format(context=context, question=question)
                    system_prompt = profile_prompts["system_ai"]
                elif detected_type == "genai":
                    user_prompt = profile_prompts["user_genai_ai"].format(context=context, question=question)
                    system_prompt = profile_prompts["system_ai"]
                elif detected_type == "code":
                    user_prompt = profile_prompts["user_code_ai"].format(context=context, question=question)
                    system_prompt = profile_prompts["system_ai"]
                else:  # default AI
                    user_prompt = profile_prompts["user_ai"].format(context=context, question=question)
                    system_prompt = profile_prompts["system_ai"]
            else:  # fallback to DE mode
                user_prompt = profile_prompts["user_de"].format(context=context, question=question)
                system_prompt = profile_prompts["system_de"]
        else:  # Tejuu profile - handle BI/BA and Analytics Engineer modes
            question_lower = question.lower()
            
            # Detect if question is about Analytics Engineering topics
            ae_keywords = ['dbt', 'data modeling', 'dimensional model', 'star schema', 'fact table', 'dimension table',
                          'analytics engineer', 'data transformation', 'incremental model', 'slowly changing dimension',
                          'scd', 'data quality', 'databricks', 'synapse', 'redshift', 'glue', 's3', 'pyspark', 'delta lake']
            is_ae_question = any(keyword in question_lower for keyword in ae_keywords)
            
            # Check if mode is explicitly set to ae, or auto-detect
            if mode == "ae" or is_ae_question:
                # Analytics Engineer Mode
                system_prompt = profile_prompts["system_ae"]
                
                if detected_type == "intro":
                    user_prompt = profile_prompts["user_intro_ae"].format(context=context, question=question)
                elif detected_type == "interview":
                    user_prompt = profile_prompts["user_interview_ae"].format(context=context, question=question)
                elif 'dbt' in question_lower:
                    user_prompt = profile_prompts["user_dbt_ae"].format(context=context, question=question)
                elif any(x in question_lower for x in ['data model', 'dimensional', 'star schema', 'fact', 'dimension']):
                    user_prompt = profile_prompts["user_datamodeling_ae"].format(context=context, question=question)
                elif any(x in question_lower for x in ['azure', 'synapse', 'adf', 'data factory']):
                    user_prompt = profile_prompts["user_azure_ae"].format(context=context, question=question)
                elif any(x in question_lower for x in ['aws', 'redshift', 'glue', 'athena']):
                    user_prompt = profile_prompts["user_aws_ae"].format(context=context, question=question)
                elif any(x in question_lower for x in ['python', 'pandas', 'pyspark']):
                    user_prompt = profile_prompts["user_python_ae"].format(context=context, question=question)
                elif 'databricks' in question_lower:
                    user_prompt = profile_prompts["user_databricks_ae"].format(context=context, question=question)
                elif detected_type == "code":
                    user_prompt = profile_prompts["user_code_ae"].format(context=context, question=question)
                else:  # default AE
                    user_prompt = profile_prompts["user_ae"].format(context=context, question=question)
            else:
                # BI/BA Mode (default for Tejuu)
                system_prompt = profile_prompts["system_bi"]
                
                if detected_type == "intro":
                    user_prompt = profile_prompts["user_intro_bi"].format(context=context, question=question)
                elif detected_type == "interview":
                    user_prompt = profile_prompts["user_interview_bi"].format(context=context, question=question)
                elif detected_type == "sql":
                    user_prompt = profile_prompts["user_sql_bi"].format(context=context, question=question)
                elif detected_type == "code":
                    user_prompt = profile_prompts["user_code_bi"].format(context=context, question=question)
                else:  # default BI
                    user_prompt = profile_prompts["user_bi"].format(context=context, question=question)
        
        # Get response from OpenAI (using faster model for better response time)
        print("Generating response with OpenAI...")
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Faster and cheaper than gpt-4o
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=2000,  # Increased significantly for comprehensive STAR-method style answers
            timeout=30.0,  # Increased timeout for complete responses
            stream=False  # Disable streaming for faster single response
        )
        print("Response generated successfully")
        
        return {
            "answer": response.choices[0].message.content,
            "mode_used": detected_type,
            "auto_detected": auto_detected,
            "sources": [{"title": r["source"], "path": r["source"]} for r in results]
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
