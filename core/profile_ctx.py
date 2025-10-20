from .templates.loader import load_profile, load_metrics

def mode_context(profile_id: str, mode: str) -> dict:
    """Get mode-specific context for profile."""
    prof = load_profile(profile_id)
    m = prof.get("modes", {}).get(mode, {})
    return {
        "profile_name": prof.get("name"),
        "mode": mode,
        "domain": m.get("domain"),
        "tools": ", ".join(m.get("tools", [])),
        "retrieval_boost": m.get("retrieval_boost", []),
        "default_projects": m.get("default_projects", [])
    }

def metrics_for_mode(profile_id: str, mode: str) -> dict:
    """Get metrics filtered by mode."""
    data = load_metrics(profile_id)
    filtered = {}
    for pid, vals in data.get("projects", {}).items():
        if "modes" in vals and mode not in vals["modes"]:
            continue
        filtered[pid] = vals
    return {"projects": filtered, "profile_id": profile_id}
