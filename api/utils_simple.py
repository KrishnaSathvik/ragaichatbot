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
    "system_default": (
        "You are a precise assistant for Data Engineering, AI/ML, RAG, and MLOps. "
        "Answer ONLY with facts supported by the provided context. "
        "If the answer is not in the context, say you don't know."
    ),

    "user_default": (
        "Context (verbatim snippets with source):\n{context}\n\n"
        "Task: Answer the user's question grounded ONLY in the context. "
        "If context lacks the answer, say you don't know.\n\n"
        "Question: {question}\n\n"
        "Answer requirements:\n"
        "• Be concise (5–8 sentences max)\n"
        "• No speculation or made-up details\n"
        "• If useful, include 1–3 short citations like: [source]\n"
    ),

    "user_interview": (
        "Context:\n{context}\n\n"
        "You are an experienced candidate answering an interview question. "
        "Use a short STAR pattern (Situation, Task, Action, Result) in 6–10 lines. "
        "Emphasize practical steps, tools, and metrics. If the context is insufficient, say you don't know.\n\n"
        "Question: {question}\n\n"
        "Answer format:\n"
        "• 1–2 lines Situation/Task\n"
        "• 3–5 lines Action (tools/commands/configs)\n"
        "• 1–2 lines Result (metrics)\n"
        "• End with a quick pitfall or best practice (1 line)\n"
    ),

    "user_sql": (
        "Context:\n{context}\n\n"
        "Provide the SQL solution FIRST in a single code block. Then add a brief 2–4 line explanation. "
        "If multiple correct solutions exist, show the most standard one. If unknown from context, say you don't know.\n\n"
        "Question: {question}\n\n"
        "Format:\n"
        "```sql\n-- Your SQL here\n```\n\n"
        "Explanation: [2-4 lines]\n"
    ),

    "user_eli5": (
        "Context:\n{context}\n\n"
        "Explain like I'm 5: Use simple words, analogies, and short sentences. "
        "Break down complex concepts into basic building blocks. If the context is insufficient, say you don't know.\n\n"
        "Question: {question}\n\n"
        "Structure:\n"
        "• Start with a simple analogy\n"
        "• Explain the main concept in 2-3 simple sentences\n"
        "• Give a real-world example\n"
        "• End with why it matters\n"
    )
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
            # Initialize with minimal parameters
            _client = OpenAI(api_key=api_key)
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
        input=text
    )
    return np.array(response.data[0].embedding, dtype=np.float32)

def _search_similar(query_embedding, top_k=5):
    _load_data()
    
    # Calculate cosine similarities
    similarities = cosine_similarity([query_embedding], _embeddings)[0]
    
    # Get top-k indices
    top_indices = np.argsort(similarities)[::-1][:top_k]
    
    results = []
    for idx in top_indices:
        results.append({
            'index': int(idx),
            'score': float(similarities[idx]),
            'content': _meta['documents'][idx]['content'],
            'source': _meta['documents'][idx].get('source', 'unknown')
        })
    
    return results

def answer_question(question, mode="auto", **kwargs):
    try:
        # Get query embedding
        query_embedding = _get_embedding(question)
        
        # Search for similar content
        results = _search_similar(query_embedding, top_k=3)
        
        # Build context
        context_parts = []
        for result in results:
            context_parts.append(f"[{result['source']}] {result['content']}")
        context = "\n\n".join(context_parts)
        
        # Select prompt based on mode
        if mode == "interview":
            user_prompt = PROMPTS["user_interview"].format(context=context, question=question)
            system_prompt = PROMPTS["system_default"]
        elif mode == "sql":
            user_prompt = PROMPTS["user_sql"].format(context=context, question=question)
            system_prompt = PROMPTS["system_default"]
        elif mode == "eli5":
            user_prompt = PROMPTS["user_eli5"].format(context=context, question=question)
            system_prompt = PROMPTS["system_default"]
        else:  # auto or default
            user_prompt = PROMPTS["user_default"].format(context=context, question=question)
            system_prompt = PROMPTS["system_default"]
        
        # Get response from OpenAI
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=1000
        )
        
        return {
            "answer": response.choices[0].message.content,
            "mode_used": mode,
            "sources": [{"title": r["source"], "path": r["source"]} for r in results]
        }
        
    except Exception as e:
        return {"error": str(e)}

def health_check():
    try:
        _load_data()
        return {"ok": True, "embeddings": True, "error": None}
    except Exception as e:
        return {"ok": False, "embeddings": False, "error": str(e)}
