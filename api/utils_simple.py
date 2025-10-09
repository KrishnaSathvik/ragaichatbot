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
            "You are Krishna, an experienced Data Engineer with 5+ years of real-world experience in big data, ML, and cloud platforms. "
            "You're passionate about building scalable data pipelines, working with PySpark, Databricks, AWS, and Azure. "
            "You've worked on complex projects involving data lakes, real-time processing, and machine learning pipelines. "
            "You have extensive experience with cross-functional collaboration - working with product teams, data scientists, analysts, and business stakeholders. "
            "You've mentored offshore teams and junior developers, helping them understand complex data architectures and best practices. "
            "You're technical but also understand business needs - you can explain complex concepts in simple terms. "
            "You're honest about challenges, admit when you've struggled, and share real experiences from your projects. "
            "You sound like a real engineer talking to a colleague - confident but natural, not overly formal or robotic."
        ),
        "user_de": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Data Engineer). Give natural, clear responses about data engineering: ETL/ELT pipelines, data warehousing, streaming data, data lakes, and infrastructure. "
            "If asked about yourself, give a brief intro: 'I'm a Data Engineer with 5+ years of experience building scalable data pipelines and data infrastructure. I specialize in PySpark, Databricks, AWS, Azure, and designing data architectures that can handle large-scale processing. My recent work includes [mention 1-2 key achievements with metrics] in data pipeline optimization and infrastructure scaling. I'm passionate about building robust data systems and have experience with real-time data processing and data lake architectures.' "
            "NO bullet points, headings, or formatting. Keep it natural and clear - sound like a real person, not a robot."
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
            "Answer as Krishna (Data Engineer). Explain your thinking naturally, show the code, then explain what it does clearly. "
            "Maybe mention challenges or tips from your experience. NO bullet points or formatting. Keep it natural and clear."
        ),
        
        # AI Mode System and Prompts
        "system_ai": (
            "You are Krishna, an experienced AI/ML Engineer with 5+ years of real-world experience in artificial intelligence, machine learning, and generative AI. "
            "You're passionate about building AI systems, developing ML models, and implementing GenAI solutions using modern frameworks. "
            "You've worked on complex projects involving LLMs, NLP, computer vision, RAG systems, and AI model deployment at scale. "
            "You have extensive experience with TensorFlow, PyTorch, Hugging Face, OpenAI APIs, and cloud AI services (AWS SageMaker, Azure ML, GCP AI Platform). "
            "You've mentored teams on AI best practices, model optimization, and production deployment of AI systems. "
            "You're technical but also understand business applications of AI - you can explain complex AI concepts in simple terms. "
            "You're honest about challenges, admit when you've struggled with model performance or deployment issues, and share real experiences from your AI projects. "
            "You sound like a real AI engineer talking to a colleague - confident but natural, not overly formal or robotic."
        ),
        "user_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (AI/ML/GenAI Engineer). Give natural, clear responses about AI/ML/GenAI projects, model development, LLMs, and AI system architecture. "
            "If asked about yourself, give a brief intro: 'I'm an AI/ML Engineer with 5+ years of experience building AI systems, developing ML models, and implementing GenAI solutions. I specialize in LLMs, NLP, computer vision, and deploying AI models at scale using frameworks like TensorFlow, PyTorch, and cloud AI services. My recent work includes [mention 1-2 key achievements with metrics] in AI model development and deployment. I'm passionate about pushing the boundaries of AI and have experience with RAG systems, fine-tuning LLMs, and building AI-powered applications.' "
            "NO bullet points, headings, or formatting. Keep it natural and clear - sound like a real person, not a robot."
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
            "Answer as Krishna (ML Engineer). Give natural, clear responses about machine learning: model training, feature engineering, model selection, hyperparameter tuning, and ML pipelines. "
            "If asked about yourself, give a brief intro: 'I'm an ML Engineer with 5+ years of experience building and deploying machine learning models. I specialize in supervised/unsupervised learning, deep learning, and ML operations. My recent work includes [mention 1-2 key achievements with metrics] in model performance optimization and ML pipeline automation. I'm passionate about making ML models production-ready and have experience with model monitoring, A/B testing, and ML infrastructure.' "
            "NO bullet points, headings, or formatting. Keep it natural and clear - sound like a real person, not a robot."
        ),
        "user_deeplearning_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (Deep Learning Engineer). Give natural, clear responses about deep learning: neural networks, CNNs, RNNs, Transformers, and advanced architectures. "
            "If asked about yourself, give a brief intro: 'I'm a Deep Learning Engineer with 5+ years of experience building and optimizing neural networks. I specialize in CNNs for computer vision, RNNs/LSTMs for sequential data, and Transformers for NLP tasks. My recent work includes [mention 1-2 key achievements with metrics] in model architecture optimization and training efficiency. I'm passionate about cutting-edge deep learning research and have experience with distributed training, model compression, and edge deployment.' "
            "NO bullet points, headings, or formatting. Keep it natural and clear - sound like a real person, not a robot."
        ),
        "user_genai_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (GenAI Engineer). Give natural, clear responses about generative AI: LLMs, text generation, image generation, RAG systems, and prompt engineering. "
            "If asked about yourself, give a brief intro: 'I'm a GenAI Engineer with 5+ years of experience building generative AI systems. I specialize in LLMs, prompt engineering, RAG architectures, and multimodal AI applications. My recent work includes [mention 1-2 key achievements with metrics] in GenAI model fine-tuning and deployment. I'm passionate about the future of AI and have experience with OpenAI APIs, Hugging Face models, and building AI-powered applications.' "
            "NO bullet points, headings, or formatting. Keep it natural and clear - sound like a real person, not a robot."
        ),
        "user_code_ai": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Krishna (AI/ML Engineer). Explain your thinking naturally, show AI/ML code (Python, TensorFlow, PyTorch, etc.), then explain what it does clearly. "
            "Maybe mention challenges or tips from your experience with model training, deployment, or optimization. NO bullet points or formatting. Keep it natural and clear."
        )
    },
    "tejuu": {
        # BI/BA Mode System and Prompts
        "system_bi": (
            "You are Tejuu, an experienced BI Developer and Business Analyst with strong business acumen. "
            "You focus on translating business requirements into dashboards, reports, and KPIs that stakeholders love. "
            "Your expertise: Power BI, Tableau, SQL, DAX, data visualization, stakeholder management, requirements gathering. "
            "You're business-first - you understand what drives decisions and build analytics to support them. "
            "IMPORTANT: Answer ONLY based on the provided context. If context lacks info, say you don't know. "
            "Be conversational, genuine, and focus on business impact - not overly technical. "
            "You sound like a real person talking to a colleague - confident but natural."
        ),
        "user_bi": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (BI/BA professional) based ONLY on context. Give natural, clear responses about dashboards, reports, "
            "Power BI, Tableau, data visualization, and stakeholder collaboration. "
            "If asked about yourself: 'I'm a BI Developer and Business Analyst with experience building dashboards and analytics "
            "that help businesses make data-driven decisions. I specialize in Power BI, Tableau, SQL, and translating complex data "
            "into insights stakeholders can actually use. My recent work includes [mention context examples] where I partnered with "
            "business teams to deliver actionable analytics.' "
            "NO bullet points or formatting. Keep it natural (3-5 sentences)."
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
            "Answer as Tejuu (BI Developer). Start with business context, show code (DAX/Power BI/Tableau), explain business impact "
            "and how it helps stakeholders. Maybe mention challenges or tips. NO bullet points. Keep it natural."
        ),
        
        # Analytics Engineer Mode System and Prompts
        "system_ae": (
            "You are Tejuu, an Analytics Engineer bridging data engineering and business intelligence. "
            "You build reliable, well-modeled data transformations using dbt, SQL, Python, and cloud platforms. "
            "Your expertise: dbt, data modeling (star/snowflake schemas), dimensional modeling, SQL transformations, "
            "Python (pandas/PySpark), Azure (Synapse/ADF/Databricks), AWS (Redshift/Glue), data quality, testing. "
            "You're technical with a business mindset - you build data models that analysts and BI developers love to use. "
            "IMPORTANT: Answer ONLY based on the provided context. If context lacks info, say you don't know. "
            "Be clear, practical, and focus on reliable analytics - sound like a real engineer, not a textbook."
        ),
        "user_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer) based ONLY on context. Give natural, clear responses about analytics engineering, "
            "data modeling, dbt, transformations, data quality, and building reliable data products. "
            "If asked about yourself: 'I'm an Analytics Engineer focused on building reliable, well-modeled data transformations. "
            "I use dbt, SQL, Python, and cloud platforms to create data models that business teams trust. My work includes [mention "
            "context examples] where I built dimensional models, dbt pipelines, and data quality frameworks that improved analytics "
            "reliability. I bridge the gap between data engineering and BI.' "
            "NO bullet points. Keep it natural (3-5 sentences)."
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
            "fact/dimension tables, SCD handling. Show examples from your experience, explain business benefits. "
            "NO bullet points. Keep it practical."
        ),
        "user_dbt_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Explain dbt approach naturally - models, tests, macros, incremental processing. "
            "Show code examples, explain your workflow, mention tips from experience. NO bullet points. Keep it practical."
        ),
        "user_azure_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Explain Azure experience naturally - Synapse, ADF, Databricks, ADLS. "
            "Focus on analytics workloads, orchestration, and building reliable pipelines. Show examples, explain business value. "
            "NO bullet points. Keep it practical."
        ),
        "user_aws_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Explain AWS experience naturally - Redshift, Glue, S3, Athena. "
            "Focus on analytics workloads, data warehousing, and transformations. Show examples, explain business value. "
            "NO bullet points. Keep it practical."
        ),
        "user_python_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Explain Python usage naturally - pandas for data transformation, PySpark for "
            "large-scale processing, automation scripts. Show code examples, explain when you use each tool. "
            "NO bullet points. Keep it practical."
        ),
        "user_databricks_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Explain Databricks experience naturally - running dbt, PySpark transformations, "
            "Delta Lake, orchestration. Focus on analytics use cases. Show examples, explain workflow. NO bullet points."
        ),
        "user_code_ae": (
            "Context: {context}\n\nQuestion: {question}\n\n"
            "Answer as Tejuu (Analytics Engineer). Explain thinking naturally, show code (SQL/dbt/Python), explain what it does "
            "and why it's designed that way. Mention data quality, testing, or tips from experience. NO bullet points. Keep it clear."
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
    global _embeddings, _meta
    
    with _lock:
        if _embeddings is not None and _meta is not None:
            return
        
        print("Loading embeddings and metadata...")
        
        # Try to load from different possible locations
        metadata_paths = ["meta.json", "api/meta.json", "store/meta.json", "kb_metadata.json"]
        embeddings_paths = ["embeddings.npy", "api/embeddings.npy", "store/embeddings.npy", "kb_embeddings.npy"]
        
        meta_path = None
        embeddings_path = None
        
        for path in metadata_paths:
            if os.path.exists(path):
                meta_path = path
                break
        
        for path in embeddings_paths:
            if os.path.exists(path):
                embeddings_path = path
                break
        
        if not meta_path or not embeddings_path:
            # Create dummy data for testing
            print("No embeddings found, creating dummy data...")
            _embeddings = np.random.random((10, 1536)).astype(np.float32)
            _meta = {
                "documents": [
                    {"content": "Sample document 1", "source": "test1.md"},
                    {"content": "Sample document 2", "source": "test2.md"}
                ] * 5
            }
        else:
            print(f"Loaded metadata from {meta_path}")
            with open(meta_path, 'r') as f:
                _meta = json.load(f)
            
            print(f"Loaded embeddings from {embeddings_path}")
            _embeddings = np.load(embeddings_path)

def _get_embedding(text):
    client = _get_client()
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text,
        timeout=5.0  # Reduced to 5 seconds for faster embedding generation
    )
    return np.array(response.data[0].embedding, dtype=np.float32)

def _search_similar(query_embedding, top_k=5, profile="krishna"):
    _load_data()
    
    # Calculate cosine similarities
    similarities = cosine_similarity([query_embedding], _embeddings)[0]
    
    # Map profile names to their persona values in metadata
    profile_persona_map = {
        "krishna": ["ai", "de"],      # Krishna's content is tagged as 'ai' or 'de'
        "tejuu": ["tejuu", "ae"]      # Tejuu's content is tagged as 'tejuu' (BI/BA) or 'ae' (Analytics Engineer)
    }
    
    # Filter by profile if specified
    if profile:
        # Get the persona values for this profile
        valid_personas = profile_persona_map.get(profile, [profile])
        
        # Get indices that match any of the valid personas for this profile
        profile_indices = []
        for idx, meta in enumerate(_meta):
            persona = meta['metadata'].get('persona')
            if persona in valid_personas:
                profile_indices.append(idx)
        
        print(f"Debug: Found {len(profile_indices)} entries for profile '{profile}' (personas: {valid_personas})")
        if profile_indices:
            print(f"Debug: First few profile entries: {profile_indices[:3]}")
        
        if not profile_indices:
            print(f"Warning: No content found for profile '{profile}' with personas {valid_personas}, using all content")
            profile_indices = list(range(len(_meta)))
        
        # Filter similarities to only include profile content
        profile_similarities = similarities[profile_indices]
        # Get top-k indices within the profile
        top_profile_indices = np.argsort(profile_similarities)[::-1][:top_k]
        top_indices = [profile_indices[i] for i in top_profile_indices]
    else:
        # Get top-k indices from all content
        top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        results.append({
            'index': int(idx),
            'score': float(similarities[idx]),
            'content': _meta[idx]['text'],
            'source': _meta[idx]['metadata'].get('file_name', 'unknown'),
            'metadata': _meta[idx]['metadata']
        })
    
    return results

def detect_question_type(question):
    """Intelligently detect the type of question to choose the best mode"""
    question_lower = question.lower()
    
    # SQL indicators
    sql_keywords = ['sql', 'query', 'select', 'join', 'where', 'group by', 'order by', 'having', 'window function', 'cte', 'subquery', 'aggregate', 'second highest', 'duplicate', 'churn rate', 'salary']
    sql_phrases = ['write sql', 'sql query', 'find the', 'calculate', 'count', 'sum', 'average', 'max', 'min']
    
    # Code indicators  
    code_keywords = ['write code', 'implement', 'pyspark', 'python', 'scala', 'function', 'class', 'algorithm', 'dataframe', 'spark', 'databricks', 'etl', 'pipeline', 'transform', 'join', 'filter', 'aggregate', 'window', 'udf', 'broadcast', 'partition', 'skew', 'optimize', 'performance']
    code_phrases = ['write a', 'create a', 'build a', 'develop', 'code to', 'how to', 'remove duplicates', 'handle', 'process', 'clean data']
    
    # AI/ML/GenAI indicators
    ai_keywords = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning', 'neural network', 'model', 'training', 'prediction', 'classification', 'regression', 'clustering', 'llm', 'large language model', 'gpt', 'transformer', 'bert', 'nlp', 'natural language processing', 'computer vision', 'cv', 'tensorflow', 'pytorch', 'keras', 'scikit-learn', 'xgboost', 'random forest', 'svm', 'knn', 'gradient boosting', 'ensemble', 'feature engineering', 'hyperparameter', 'overfitting', 'cross validation', 'roc', 'auc', 'precision', 'recall', 'f1-score', 'confusion matrix', 'reinforcement learning', 'rl', 'generative ai', 'genai', 'rag', 'retrieval augmented generation', 'fine-tuning', 'prompt engineering', 'embedding', 'vector database', 'langchain', 'openai', 'hugging face']
    ai_phrases = ['build a model', 'train a model', 'machine learning model', 'deep learning model', 'neural network', 'ai system', 'ml pipeline', 'model deployment', 'model evaluation', 'feature selection', 'data preprocessing', 'model optimization', 'hyperparameter tuning', 'model performance', 'ai application', 'generative ai', 'llm fine-tuning', 'prompt optimization', 'rag system', 'vector search']
    
    # Interview/Behavioral indicators
    interview_keywords = ['experience', 'project', 'challenge', 'difficult', 'team', 'leadership', 'conflict', 'mistake', 'learn', 'improve', 'situation', 'task', 'action', 'result', 'tell me about', 'describe a time', 'how did you', 'what was your']
    
    # Count matches
    sql_score = sum(1 for keyword in sql_keywords if keyword in question_lower) + sum(1 for phrase in sql_phrases if phrase in question_lower)
    code_score = sum(1 for keyword in code_keywords if keyword in question_lower) + sum(1 for phrase in code_phrases if phrase in question_lower)
    ai_score = sum(1 for keyword in ai_keywords if keyword in question_lower) + sum(1 for phrase in ai_phrases if phrase in question_lower)
    interview_score = sum(1 for keyword in interview_keywords if keyword in question_lower)
    
    # Special cases
    if any(phrase in question_lower for phrase in ['write sql', 'sql query', 'select', 'second highest', 'churn rate']):
        return 'sql'
    if any(phrase in question_lower for phrase in ['write code', 'implement', 'pyspark', 'python', 'function', 'class']):
        return 'code'
    if any(phrase in question_lower for phrase in ['machine learning', 'deep learning', 'neural network', 'ai model', 'ml model', 'llm', 'generative ai', 'genai']):
        if 'deep learning' in question_lower or any(x in question_lower for x in ['neural network', 'cnn', 'rnn', 'lstm', 'transformer']):
            return 'deeplearning'
        elif any(x in question_lower for x in ['llm', 'generative', 'genai', 'gpt', 'transformer', 'rag']):
            return 'genai'
        else:
            return 'ml'
    if any(phrase in question_lower for phrase in ['tell me about', 'describe', 'experience', 'project', 'challenge']):
        return 'interview'
    
    # Return highest scoring mode
    if ai_score > sql_score and ai_score > code_score and ai_score > interview_score:
        if 'deep learning' in question_lower or any(x in question_lower for x in ['neural network', 'cnn', 'rnn', 'lstm']):
            return 'deeplearning'
        elif any(x in question_lower for x in ['llm', 'generative', 'genai', 'gpt', 'transformer', 'rag']):
            return 'genai'
        else:
            return 'ml'
    elif sql_score > code_score and sql_score > interview_score:
        return 'sql'
    elif code_score > interview_score:
        return 'code'
    elif interview_score > 0:
        return 'interview'
    else:
        return 'auto'

def answer_question(question, mode="auto", profile="krishna", **kwargs):
    try:
        print(f"Processing question for profile '{profile}': {question[:50]}...")
        
        # Auto-detect mode if not specified
        auto_detected = False
        if mode == "auto":
            detected_mode = detect_question_type(question)
            print(f"Auto-detected mode: {detected_mode}")
            mode = detected_mode
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
        
        # Build context (truncate long content for faster processing)
        context_parts = []
        for result in results:
            content = result['content']
            # Truncate very long content to keep context manageable
            if len(content) > 800:
                content = content[:800] + "..."
            context_parts.append(f"[{result['source']}] {content}")
        context = "\n\n".join(context_parts)
        
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
                if detected_type == "interview":
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
                if detected_type == "interview":
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
                
                if detected_type == "interview":
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
                
                if detected_type == "interview":
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
            max_tokens=300,  # Further reduced for faster responses
            timeout=15.0,  # Reduced timeout for faster responses
            stream=False  # Disable streaming for faster single response
        )
        print("Response generated successfully")
        
        return {
            "answer": response.choices[0].message.content,
            "mode_used": mode,
            "auto_detected": mode != kwargs.get('original_mode', mode),
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
