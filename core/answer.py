from .router import route_intent
from .templates.registry import get_template, target_len
from .templates.prompter import fill_template, enforce_length
from .profile_ctx import mode_context, metrics_for_mode
from .memory import ShortMemory
import json

# Global memory instance
memory = ShortMemory()

def retrieve_evidence(q: str, intent: str, profile_id: str, mode: str, boost: list[str]) -> str:
    """Retrieve evidence for question (placeholder - integrate with existing RAG)."""
    # This is a placeholder - integrate with your existing _search_similar function
    # For now, return a generic response
    return f"Key components: {', '.join(boost[:3])} based on {intent} approach"

def compose_with_template(intent_id: str, q: str, session_id: str, profile_id: str, mode: str) -> str:
    """Compose answer using template system."""
    ctx = mode_context(profile_id, mode)
    metrics = metrics_for_mode(profile_id, mode)
    tpl = get_template(intent_id)
    
    # Get prior context for follow-ups
    prior_point = memory.get_prior_point(session_id) if intent_id == "followup_drilldown" else ""
    
    # Prepare template variables
    vars_ = {
        "role": mode,  # simple alias
        "domain": ctx["domain"],
        "project_name": ", ".join(ctx["default_projects"]) or "current project",
        "retrieved_facts": retrieve_evidence(q, intent_id, profile_id, mode, ctx["retrieval_boost"]),
        "constraints": "",
        "tools": ctx["tools"],
        "metrics": json.dumps(metrics, indent=2),
        "prior_point": prior_point,
        "target_tool": "",
        "source_tool": "",
        "profile_name": ctx["profile_name"],
        "mode": ctx["mode"]
    }
    
    # Fill template and enforce length
    draft = fill_template(tpl["prompt"], vars_)
    lo, hi = target_len(intent_id)
    final = enforce_length(draft, lo, hi)
    
    # Store in memory
    memory.add(session_id, {"q": q, "a": final})
    
    return final

def answer_question_template(q: str, session_id: str, profile_id: str, mode: str) -> dict:
    """Main entry point for template-based answering."""
    # Route intent
    intent, confidence = route_intent(q, session_id)
    
    # Compose answer
    answer = compose_with_template(intent, q, session_id, profile_id, mode)
    
    return {
        "answer": answer,
        "intent": intent,
        "confidence": confidence,
        "mode": mode,
        "profile": profile_id
    }
