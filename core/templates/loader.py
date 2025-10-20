from pathlib import Path
import yaml
import json
import functools

ROOT = Path(__file__).resolve().parents[2]  # project root
PROMPTS = ROOT / "prompts" / "v1" / "templates.yaml"
PROFILES = ROOT / "content" / "profiles"
METRICS = ROOT / "content" / "metrics"

@functools.lru_cache(maxsize=8)
def load_templates():
    """Load and cache templates from YAML file."""
    with open(PROMPTS, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    by_id = {t["id"]: t for t in data["templates"]}
    return {"raw": data, "by_id": by_id}

@functools.lru_cache(maxsize=8)
def load_profile(profile_id: str):
    """Load and cache profile configuration."""
    with open(PROFILES / f"{profile_id}.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

@functools.lru_cache(maxsize=8)
def load_metrics(profile_id: str):
    """Load and cache metrics data."""
    with open(METRICS / f"{profile_id}.json", "r", encoding="utf-8") as f:
        return json.load(f)
