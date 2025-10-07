import os, json
import threading
import numpy as np
import faiss
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

_client = None
_index = None
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
        "Question: {question}\n"
    ),

    "user_eli5": (
        "Context:\n{context}\n\n"
        "Explain the answer simply, as if to a smart 12-year-old. "
        "Use short sentences, a friendly tone, and a tiny example. If not in context, say you don't know.\n\n"
        "Question: {question}\n"
    ),
}

# ---- Singletons ------------------------------------------------------------

def _client_once():
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _client


def _store_once():
    global _index, _meta
    if _index is not None and _meta is not None:
        return _index, _meta
    with _lock:
        if _index is not None and _meta is not None:
            return _index, _meta
        
        # Try multiple possible locations for FAISS files
        index_paths = ["faiss.index", "api/faiss.index", "store/faiss.index", "kb_index.faiss"]
        metadata_paths = ["meta.json", "api/meta.json", "store/meta.json", "kb_metadata.json"]
        
        _index = None
        _meta = None
        
        for index_path in index_paths:
            try:
                _index = faiss.read_index(index_path)
                print(f"Loaded FAISS index from {index_path}")
                break
            except:
                continue
                
        for metadata_path in metadata_paths:
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    _meta = json.load(f)
                print(f"Loaded metadata from {metadata_path}")
                break
            except:
                continue
        
        if not _index or not _meta:
            raise FileNotFoundError("Could not find FAISS index or metadata files")
            
    return _index, _meta

# ---- Embeddings ------------------------------------------------------------

def get_embedding(text: str) -> np.ndarray:
    cli = _client_once()
    r = cli.embeddings.create(model="text-embedding-3-small", input=text)
    return np.array(r.data[0].embedding, dtype="float32")

# ---- Retrieval + Generation ------------------------------------------------

def answer_question(message: str, mode: str | None = None) -> dict:
    """
    Core RAG pipeline used by both FastAPI (local) and Vercel handler.
    Returns a dict: {answer, sources, chunks, usage}
    """
    if not (message or "").strip():
        return {"error": "message is required"}

    idx, meta = _store_once()

    # 1) Embed query
    q = get_embedding(message).reshape(1, -1)

    # 2) Vector search
    top_k = 5
    scores, ids = idx.search(q, top_k)

    # 3) Gather chunks + build context
    selected = []
    best_score = 0.0
    for i, score in zip(ids[0], scores[0]):
        key = str(i)
        if key in meta:
            item = dict(meta[key])
            item["_score"] = float(score)
            selected.append(item)
            best_score = max(best_score, float(score))

    # 3b) Confidence threshold → "I don't know"
    min_ok = 0.15  # tune as needed
    if not selected or best_score < min_ok:
        return {
            "answer": "I don't know from the provided context.",
            "sources": [],
            "chunks": [],
            "usage": {}
        }

    context = "\n\n".join([c.get("text", "") for c in selected])

    # 4) Choose prompt by mode
    mode = (mode or "default").lower()
    sys_prompt = PROMPTS["system_default"]
    if mode == "interview":
        user_prompt = PROMPTS["user_interview"].format(context=context, question=message)
        temperature = 0.2
    elif mode == "sql":
        user_prompt = PROMPTS["user_sql"].format(context=context, question=message)
        temperature = 0.2
    elif mode in ("eli5", "explain_like_5", "simple"):
        user_prompt = PROMPTS["user_eli5"].format(context=context, question=message)
        temperature = 0.3
    else:
        user_prompt = PROMPTS["user_default"].format(context=context, question=message)
        temperature = 0.3

    # 5) Generate
    cli = _client_once()
    resp = cli.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=temperature
    )
    answer = resp.choices[0].message.content.strip()

    # 6) Sources for UI chips + optional inline tags
    sources = [{
        "title": c.get("source") or c.get("title") or "source",
        "path": c.get("path"),
        "score": c.get("_score")
    } for c in selected]
    tags = []
    for s in sources[:3]:
        base = s.get("title") or s.get("path") or "source"
        tags.append(f"[{base}]")
    if tags and mode != "sql":  # keep SQL output clean
        answer = f"{answer}\n\nSources: " + " ".join(tags)

    return {
        "answer": answer,
        "sources": sources,
        "chunks": selected,
        "usage": getattr(resp, "usage", None).model_dump() if hasattr(resp, "usage") else {}
    }


def health_check() -> dict:
    ok, err = True, None
    try:
        _store_once()
    except Exception as e:
        ok, err = False, str(e)
    return {"ok": ok, "faiss": ok, "error": err}
