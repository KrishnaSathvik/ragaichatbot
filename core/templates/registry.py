from pathlib import Path
import yaml

_TEMPLATE_ROOT = Path(__file__).resolve().parent
_CACHE_TEXT = {}
_CACHE_IDX = None

def _load_index():
    global _CACHE_IDX
    if _CACHE_IDX is not None:
        return _CACHE_IDX
    idx_path = Path(__file__).resolve().parents[2] / "prompts" / "v1" / "templates.yaml"
    data = yaml.safe_load(idx_path.read_text(encoding="utf-8"))
    _CACHE_IDX = data
    return _CACHE_IDX

def get_template(intent_id: str) -> dict:
    idx = _load_index()
    items = idx["templates"]
    # find by id or alias
    for it in items:
        if it["id"] == intent_id or intent_id in it.get("aliases", []):
            return it
    # fallback
    fb = next(x for x in items if x["id"] == idx["defaults"]["fallback_intent"])
    return fb

def load_template_text(tpl: dict) -> str:
    idx = _load_index()
    base = Path(__file__).resolve().parents[0] / "fragments"
    path = base / tpl["file"]
    if path not in _CACHE_TEXT:
        _CACHE_TEXT[path] = path.read_text(encoding="utf-8").strip()
    return _CACHE_TEXT[path]

def target_len(intent_id: str) -> tuple[int, int]:
    idx = _load_index()
    tpl = get_template(intent_id)
    lo = tpl.get("target_words_low", idx["defaults"]["target_words_low"])
    hi = tpl.get("target_words_high", idx["defaults"]["target_words_high"])
    return lo, hi

def list_intent_keywords():
    """Get all intent keywords for routing."""
    idx = _load_index()
    return {t["id"]: t.get("aliases", []) for t in idx["templates"]}
