# /core/templates/ingest_patch.py (drop-in snippet for your ingest logic)

from pathlib import Path
import json, re, tiktoken
from datetime import datetime

ENC = tiktoken.get_encoding("cl100k_base")

def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore")

def _chunk(text: str, target=900, overlap=100):
    toks = ENC.encode(text)
    n = len(toks)
    i = 0
    while i < n:
        j = min(i + target, n)
        piece = ENC.decode(toks[i:j])
        yield piece.strip()
        if j == n: break
        i = max(j - overlap, 0)

def _infer_mode_from_path(p: Path):
    s = p.name.lower()
    # hard mapping to avoid wrong routing
    if s.startswith("de_") or "pyspark" in s or "databricks" in s: return ("krishna", "de")
    if "krishna_ai" in s or "rag" in s or "llm" in s or "mlops" in s: return ("krishna", "ai")
    if s.startswith("ae_") or "dbt" in s or "data_model" in s: return ("tejuu", "ae")
    if s.startswith("bi_") or "power_bi" in s or "tableau" in s or "ba_" in s: return ("tejuu", "bi")
    # default fallbacks (safe)
    return ("krishna", "de")

def build_docs(kb_dir: Path):
    docs = []
    for p in kb_dir.glob("*.md"):
        raw = _read(p)
        # light cleanup
        raw = re.sub(r"\n{3,}", "\n\n", raw).strip()
        prof, mode = _infer_mode_from_path(p)
        now = datetime.utcnow().date().isoformat()

        # section hints from headings (H2/H3)
        sections = [m.group(1).strip() for m in re.finditer(r"^##+\s+(.*)$", raw, re.M)]
        section_hint = sections[0] if sections else "General"

        for i, chunk in enumerate(_chunk(raw, target=950, overlap=100), start=1):
            docs.append({
                "id": f"{p.stem}-{i}",
                "text": chunk,
                "metadata": {
                    "profile": prof,
                    "mode": mode,
                    "persona": mode,
                    "source_file": p.name,
                    "path": f"/kb/{p.name}",
                    "section": section_hint,
                    "date": now,
                    "tags": _tags_from_text(chunk),
                    "quality": _quality_heuristic(p.name, chunk)
                }
            })
    return docs

def _tags_from_text(t: str):
    tags = []
    keyz = {
        "RAG":["rag","retrieval","embedding","rerank","langchain","langgraph","pinecone","weaviate"],
        "PowerBI":["power bi","dax","rls","dataset","certified"],
        "dbt":["dbt","model","macro","test","seed","exposure"],
        "DE":["pyspark","delta","databricks","kafka","etl","elt","airflow","adf"],
        "Cloud":["azure","aws","synapse","snowflake"]
    }
    lt = t.lower()
    for k, kws in keyz.items():
        if any(kw in lt for kw in kws): tags.append(k)
    return tags[:6]

def _quality_heuristic(fname: str, t: str):
    # prefer experience/source files over generic guides
    score = 0.7
    if "experience" in fname.lower(): score += 0.2
    if "interview" in fname.lower(): score -= 0.05
    if len(t) > 800: score += 0.05
    return min(1.0, max(0.4, score))
