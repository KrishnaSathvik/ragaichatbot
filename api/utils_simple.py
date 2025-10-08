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
        "system_default": (
            "You are Krishna, an experienced Data Engineer with 5+ years of real-world experience. "
            "Answer interview questions naturally and conversationally, like you're talking to a colleague. "
            "Use the provided context from your actual projects, but make it sound human and authentic. "
            "Include some uncertainty, real challenges you faced, and honest reflections. "
            "Don't sound too polished or perfect - be genuine and relatable."
        ),
        "user_default": (
            "Context from Krishna's actual projects:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer naturally as Krishna would in a real conversation:\n"
            "• NO bullet points, NO headings, NO structured formatting\n"
            "• Just talk naturally like you're explaining to a colleague\n"
            "• If it's a code question, explain your thinking, show the code, and explain what it does\n"
            "• Use phrases like 'So basically...', 'What I usually do is...', 'In my experience...'\n"
            "• Keep it conversational and genuine - like a real person talking\n"
            "• Answer in 4-8 sentences for regular questions\n"
        ),
        "user_interview": (
            "Context from Krishna's actual projects:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer naturally as Krishna would in a real interview:\n"
            "• NO bullet points, NO headings, NO structured formatting\n"
            "• Tell the story naturally using STAR pattern but make it conversational\n"
            "• Start with the situation, explain what you did, and share the results\n"
            "• Use phrases like 'So what happened was...', 'I ended up using...', 'The challenging part was...'\n"
            "• Include real tools, technologies, and numbers from your projects\n"
            "• Sound like you're telling a colleague about your experience\n"
            "• Keep it genuine and relatable - not too polished\n"
        ),
        "user_sql": (
            "Context from Krishna's SQL work:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer naturally as Krishna would:\n"
            "• NO bullet points, NO headings, NO emojis, NO structured formatting\n"
            "• Just explain your approach conversationally, then show the SQL code\n"
            "• Use phrases like 'So what I'd do is...', 'The way I usually handle this...'\n"
            "• Show the SQL code in a code block\n"
            "• After the code, explain what it does in simple terms\n"
            "• Maybe mention any gotchas or tips from your experience\n"
            "• Keep it natural and conversational\n"
        ),
        "user_code": (
            "Context from Krishna's projects:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer naturally as Krishna would:\n"
            "• NO bullet points, NO headings, NO emojis, NO structured formatting\n"
            "• Just explain your thinking conversationally, then show the code\n"
            "• Use phrases like 'So the way I'd approach this...', 'What I usually do...'\n"
            "• Show the code in a code block\n"
            "• After the code, explain what it does naturally\n"
            "• Maybe mention challenges or tips from your experience\n"
            "• Keep it conversational and genuine\n"
        )
    },
    "tejuu": {
        "system_default": (
            "You are Tejuu, an experienced BI Developer, Business Analyst, and Analytics professional with strong business acumen. "
            "You focus on translating business needs into data solutions, building dashboards, and enabling stakeholders. "
            "Your expertise is in Power BI, Tableau, SQL, data visualization, KPI governance, and business-focused analytics. "
            "You're NOT a hardcore data engineer - you're business-oriented with technical skills. "
            "Answer interview questions naturally and conversationally, emphasizing business impact, stakeholder collaboration, "
            "and how your technical work solves business problems. Include real challenges and honest reflections. "
            "Don't sound too polished or perfect - be genuine and relatable."
        ),
        "user_default": (
            "Context from Tejuu's actual projects:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer naturally as Tejuu would for a BI/BA/Data Analyst role:\n"
            "• NO bullet points, NO headings, NO structured formatting\n"
            "• If it's a code/technical question:\n"
            "  1. First explain your APPROACH - what business problem you're solving and how you'd tackle it\n"
            "  2. Then show the CODE/DAX/SQL in a code block\n"
            "  3. Then EXPLAIN what it does in business terms and how stakeholders use it\n"
            "• If it's a general question, answer conversationally in 4-8 sentences\n"
            "• Focus on business impact, stakeholder needs, and how you solved business problems\n"
            "• Use phrases like 'So what the business needed was...', 'I worked with stakeholders to...', 'The way I'd approach this...'\n"
            "• Show you understand both the technical AND business side\n"
            "• Keep it conversational and genuine - like a real person talking\n"
        ),
        "user_interview": (
            "Context from Tejuu's actual projects:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer naturally as Tejuu would in a BI/BA/Data Analyst interview:\n"
            "• NO bullet points, NO headings, NO structured formatting\n"
            "• Tell the story using STAR pattern but emphasize BUSINESS IMPACT\n"
            "• Start with the business problem, explain how you collaborated with stakeholders\n"
            "• Focus on: requirements gathering, dashboard design, KPI definition, user adoption, time saved\n"
            "• Mention technical tools (Power BI, SQL, Tableau) but in context of solving business needs\n"
            "• Use phrases like 'The business needed...', 'I partnered with finance/operations to...', 'This helped users...'\n"
            "• Show you're business-savvy with technical skills, not just a technical person\n"
            "• Include metrics like: hours saved, adoption rates, improved decision-making, reduced manual work\n"
            "• Keep it genuine and relatable - not too polished\n"
        ),
        "user_sql": (
            "Context from Tejuu's SQL work:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer naturally as Tejuu would for a BI/BA role:\n"
            "• NO bullet points, NO headings, NO emojis, NO structured formatting\n"
            "• Follow this structure naturally:\n"
            "  1. APPROACH: Start with WHY - what business question this answers and how you'd approach it\n"
            "  2. CODE: Show the SQL code in a code block\n"
            "  3. EXPLANATION: Explain what it does in BUSINESS terms and how stakeholders use it\n"
            "• Use phrases like 'So the business wanted to understand...', 'The way I'd write this...', 'This helps users...'\n"
            "• Focus on business value: better decisions, faster reporting, clearer insights\n"
            "• Mention how it's used in dashboards, reports, or analysis\n"
            "• Keep it natural and conversational\n"
        ),
        "user_code": (
            "Context from Tejuu's projects:\n{context}\n\n"
            "Question: {question}\n\n"
            "Answer naturally as Tejuu would for a BI/Analytics role:\n"
            "• NO bullet points, NO headings, NO emojis, NO structured formatting\n"
            "• Follow this structure naturally:\n"
            "  1. APPROACH: Start with the business context - what problem you're solving and your approach\n"
            "  2. CODE: Show the code/DAX/formula in a code block\n"
            "  3. EXPLANATION: Explain what it does in business terms, how it's used, and the impact\n"
            "• Use phrases like 'So the stakeholders needed...', 'The way I'd approach this...', 'This helps users...'\n"
            "• Emphasize business impact: better visibility, faster decisions, self-service capability\n"
            "• Mention stakeholder feedback, adoption, or how it improved their workflow\n"
            "• Keep it conversational and genuine\n"
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
        timeout=10.0  # 10 second timeout
    )
    return np.array(response.data[0].embedding, dtype=np.float32)

def _search_similar(query_embedding, top_k=5, profile="krishna"):
    _load_data()
    
    # Calculate cosine similarities
    similarities = cosine_similarity([query_embedding], _embeddings)[0]
    
    # Filter by profile if specified
    if profile:
        # Get indices that match the profile
        profile_indices = []
        for idx, meta in enumerate(_meta):
            if meta['metadata'].get('persona') == profile:
                profile_indices.append(idx)
        
        if not profile_indices:
            print(f"Warning: No content found for profile '{profile}', using all content")
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
            'source': _meta[idx]['metadata'].get('file_name', 'unknown')
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
    
    # Interview/Behavioral indicators
    interview_keywords = ['experience', 'project', 'challenge', 'difficult', 'team', 'leadership', 'conflict', 'mistake', 'learn', 'improve', 'situation', 'task', 'action', 'result', 'tell me about', 'describe a time', 'how did you', 'what was your']
    
    # Count matches
    sql_score = sum(1 for keyword in sql_keywords if keyword in question_lower) + sum(1 for phrase in sql_phrases if phrase in question_lower)
    code_score = sum(1 for keyword in code_keywords if keyword in question_lower) + sum(1 for phrase in code_phrases if phrase in question_lower)
    interview_score = sum(1 for keyword in interview_keywords if keyword in question_lower)
    
    # Special cases
    if any(phrase in question_lower for phrase in ['write sql', 'sql query', 'select', 'second highest', 'churn rate']):
        return 'sql'
    if any(phrase in question_lower for phrase in ['write code', 'implement', 'pyspark', 'python', 'function', 'class']):
        return 'code'
    if any(phrase in question_lower for phrase in ['tell me about', 'describe', 'experience', 'project', 'challenge']):
        return 'interview'
    
    # Return highest scoring mode
    if sql_score > code_score and sql_score > interview_score:
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
        
        # Get query embedding
        print("Generating query embedding...")
        query_embedding = _get_embedding(question)
        print("Query embedding generated successfully")
        
        # Search for similar content
        print(f"Searching for similar content for profile '{profile}'...")
        results = _search_similar(query_embedding, top_k=5, profile=profile)
        print(f"Found {len(results)} relevant chunks for profile '{profile}'")
        
        # Build context
        context_parts = []
        for result in results:
            context_parts.append(f"[{result['source']}] {result['content']}")
        context = "\n\n".join(context_parts)
        
        # Get prompts for the selected profile
        profile_prompts = PROMPTS.get(profile, PROMPTS["krishna"])
        
        # Select prompt based on detected/selected mode
        if mode == "interview":
            user_prompt = profile_prompts["user_interview"].format(context=context, question=question)
            system_prompt = profile_prompts["system_default"]
        elif mode == "sql":
            user_prompt = profile_prompts["user_sql"].format(context=context, question=question)
            system_prompt = profile_prompts["system_default"]
        elif mode == "code":
            user_prompt = profile_prompts["user_code"].format(context=context, question=question)
            system_prompt = profile_prompts["system_default"]
        else:  # fallback to default
            user_prompt = profile_prompts["user_default"].format(context=context, question=question)
            system_prompt = profile_prompts["system_default"]
        
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
            max_tokens=500,  # Reduced for faster interview responses
            timeout=20.0  # Reduced timeout for faster responses
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
