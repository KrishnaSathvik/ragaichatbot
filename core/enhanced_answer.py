import os
import sys
import json
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).resolve().parents[1]
sys.path.append(str(project_root))

# Import moved inside functions to avoid circular import
from .answer import answer_question_template
from .answer_v2 import answer_question_template_v2
from .router import route_intent
# ✅ Reuse optimized, cached embedding + persona-aware search
# Import moved inside functions to avoid circular import

# --- Normalization helpers ---
PROFILE_ALIASES = {
    "krishna": "krishna",
    "tejuu": "tejuu",
    # accidental misroutes:
    "ai": "krishna", "de": "krishna",
    "ae": "tejuu", "bi": "tejuu",
}

MODE_ALIASES = {
    # krishna
    "ai": "ai",
    "de": "de",
    "plsql": "plsql",
    # tejuu
    "ae": "ae",
    "bi": "bi",
    # fallbacks
    "auto": "auto",
}

def normalize_profile_id(profile_id: str, mode: str) -> tuple[str, str]:
    p = PROFILE_ALIASES.get(str(profile_id).lower(), "krishna")
    m = MODE_ALIASES.get(str(mode).lower(), "ai" if p == "krishna" else "ae")
    return p, m

def profile_path(root: str, profile_id: str) -> str:
    # maps -> content/profiles/{krishna|tejuu}.yaml
    return os.path.join(root, "content", "profiles", f"{profile_id}.yaml")

def metrics_path(root: str, profile_id: str) -> str:
    # maps -> content/metrics/{krishna|tejuu}.json
    return os.path.join(root, "content", "metrics", f"{profile_id}.json")

# Feature flags for template system
TEMPLATES_V1 = os.getenv("TEMPLATES_V1", "true").lower() == "true"
TEMPLATES_V2 = os.getenv("TEMPLATES_V2", "true").lower() == "true"

def answer_question_enhanced(question, mode="auto", profile="auto", session_id="default", **kwargs):
    """Enhanced answer_question with template system integration."""
    try:
        # Import here to avoid circular import
        from api.utils import detect_profile, detect_question_type, detect_domain
        
        # Auto-detect profile if not specified
        profile_auto_detected = False
        if profile == "auto":
            profile = detect_profile(question)
            profile_auto_detected = True
            print(f"Auto-detected profile: {profile}")
        
        print(f"Processing question for profile '{profile}': {question[:50]}...")
        
        # Auto-detect mode if not specified
        if mode == "auto":
            if profile == "krishna":
                # Default to AI mode for Krishna
                mode = "ai"
            elif profile == "tejuu":
                # Default to AE mode for Tejuu
                mode = "ae"
            else:
                mode = "ai"  # fallback
        
        # Normalize profile and mode
        profile, mode = normalize_profile_id(profile, mode)
        
        print(f"Using mode: {mode}")
        
        # Check if we should use template system
        # Skip template system for PL/SQL mode - use legacy system with custom prompts
        if TEMPLATES_V2 and mode != "plsql":
            print("Using Phase 2 template system (TEMPLATES_V2 enabled)")
            
            # Route intent for template system
            intent, confidence = route_intent(question, session_id)
            print(f"Intent: {intent}, Confidence: {confidence:.2f}")
            
            # Use Phase 2 template system if confidence is high enough
            if confidence >= 0.30:  # Threshold for template system
                try:
                    t0 = time.perf_counter()
                    result = answer_question_template_v2(question, session_id, profile, mode)
                    result.setdefault("latency_ms", int((time.perf_counter() - t0) * 1000))
                    result.setdefault("intent", intent)
                    result.setdefault("confidence", round(confidence, 2))
                    print("Phase 2 template system response generated successfully")
                    
                    # Add legacy compatibility fields
                    result.update({
                        "domain_used": mode,
                        "qtype_used": "template_v2",
                        "auto_detected": False,
                        "profile_used": profile,
                        "profile_auto_detected": profile_auto_detected,
                        "template_used": result.get("template", "template_v2")
                    })
                    
                    return result
                    
                except Exception as e:
                    print(f"Phase 2 template system failed, trying Phase 1: {e}")
                    # Fall through to Phase 1
            else:
                print(f"Low confidence ({confidence:.2f}), trying Phase 1")
        
        # Check if we should use Phase 1 template system
        # Skip template system for PL/SQL mode - use legacy system with custom prompts
        if TEMPLATES_V1 and mode != "plsql":
            print("Using Phase 1 template system (TEMPLATES_V1 enabled)")
            
            # Route intent for template system
            intent, confidence = route_intent(question, session_id)
            print(f"Intent: {intent}, Confidence: {confidence:.2f}")
            
            # Use template system if confidence is high enough
            if confidence >= 0.30:  # Threshold for template system
                try:
                    result = answer_question_template(question, session_id, profile, mode)
                    print("Phase 1 template system response generated successfully")
                    
                    # Add metadata
                    result.update({
                        "domain_used": mode,
                        "qtype_used": "template_v1",
                        "auto_detected": False,
                        "profile_used": profile,
                        "profile_auto_detected": profile_auto_detected,
                        "template_used": intent,
                        "intent": intent,
                        "confidence": confidence,
                        "template": intent,  # template used
                        "latency_ms": 0,  # TODO: measure actual latency
                        "sources": [],  # Template system doesn't provide sources yet
                        "citations": []
                    })
                    
                    return result
                    
                except Exception as e:
                    print(f"Phase 1 template system failed, falling back to legacy: {e}")
                    # Fall through to legacy system
            else:
                print(f"Low confidence ({confidence:.2f}), using legacy system")
        
        # Legacy system (existing implementation)
        print("Using legacy system")
        
        # Import legacy functions
        from api.utils import _get_embedding, _search_similar, humanize
        
        # Separate domain detection from question type
        qtype = detect_question_type(question)
        
        if mode in ("de", "ai", "bi", "ae", "plsql"):
            # Explicit mode provided
            domain = mode
            auto_detected = False
        else:
            # Auto-detect domain
            domain = detect_domain(question, profile)
            auto_detected = True
        
        print(f"Routing → domain={domain}, qtype={qtype}")
        
        # Get query embedding
        print("Generating query embedding...")
        query_embedding = _get_embedding(question)
        print("Query embedding generated successfully")
        
        # Search for similar content (pass mode and qtype for PL/SQL code filtering)
        print(f"Searching for similar content for profile '{profile}' mode '{domain}' qtype '{qtype}'...")
        results = _search_similar(query_embedding, top_k=6, profile=profile, mode=domain, query_text=question, qtype=qtype)
        print(f"Found {len(results)} relevant chunks for profile '{profile}' mode '{domain}'")
        
        # Debug: Print the sources of the results
        for i, result in enumerate(results):
            print(f"Result {i+1}: Source={result.get('source', 'Unknown')}, Persona={result.get('metadata', {}).get('persona', 'Unknown')}")
        
        # Build context safely with tighter length limits for speed
        if not results:
            context = ""
        else:
            parts = []
            total = 0
            for r in results:
                chunk = r["content"]
                # Reduced chunk size for faster processing
                if len(chunk) > 600: 
                    chunk = chunk[:600] + "..."
                frag = f"[{r['source']}] {chunk}"
                # Reduced total context to 1800 chars
                if total + len(frag) > 1800: 
                    break
                parts.append(frag)
                total += len(frag)
            context = "\n\n".join(parts)
        
        # Debug: Print context preview
        print(f"Context preview (first 500 chars): {context[:500]}...")
        
        # Get prompts for the selected profile (legacy system)
        from api.utils import PROMPTS
        profile_prompts = PROMPTS.get(profile, PROMPTS["krishna"])
        print(f"Debug: Profile='{profile}', Domain='{domain}', QType='{qtype}'")
        
        # Select system and user prompt based on domain and question type
        if profile == "krishna":
            # Select system prompt based on domain
            if domain == "ai":
                system_prompt = profile_prompts["system_ai"]
            elif domain == "plsql":
                system_prompt = profile_prompts["system_plsql"]
            else:
                system_prompt = profile_prompts["system_de"]
            
            if domain == "ai":
                # AI/ML/GenAI Mode
                if qtype == "intro":
                    user_prompt = profile_prompts["user_intro_ai"]
                elif qtype == "interview":
                    user_prompt = profile_prompts["user_interview_ai"]
                elif qtype == "ml":
                    user_prompt = profile_prompts["user_ml_ai"]
                elif qtype == "deeplearning":
                    user_prompt = profile_prompts["user_deeplearning_ai"]
                elif qtype == "genai":
                    user_prompt = profile_prompts["user_genai_ai"]
                elif qtype == "code":
                    user_prompt = profile_prompts["user_code_ai"]
                else:
                    user_prompt = profile_prompts["user_ai"]
            elif domain == "plsql":
                # PL/SQL Mode
                if qtype == "intro":
                    user_prompt = profile_prompts["user_intro_plsql"]
                elif qtype == "code" or qtype == "sql":
                    user_prompt = profile_prompts["user_code_plsql"]
                else:
                    user_prompt = profile_prompts["user_plsql"]
            else:  # de
                # Data Engineering Mode
                if qtype == "intro":
                    user_prompt = profile_prompts["user_intro_de"]
                elif qtype == "interview":
                    user_prompt = profile_prompts["user_interview_de"]
                elif qtype == "sql":
                    user_prompt = profile_prompts["user_sql_de"]
                elif qtype == "pipeline":
                    user_prompt = profile_prompts["user_pipeline_de"]
                elif qtype == "code":
                    user_prompt = profile_prompts["user_code_de"]
                else:
                    user_prompt = profile_prompts["user_de"]
        
        elif profile == "tejuu":
            system_prompt = profile_prompts["system_bi"] if domain == "bi" else profile_prompts["system_ae"]
            
            if domain == "bi":
                # Business Intelligence Mode
                if qtype == "intro":
                    user_prompt = profile_prompts["user_intro_bi"]
                elif qtype == "interview":
                    user_prompt = profile_prompts["user_interview_bi"]
                elif qtype == "dashboard":
                    user_prompt = profile_prompts["user_dashboard_bi"]
                elif qtype == "dax":
                    user_prompt = profile_prompts["user_dax_bi"]
                elif qtype == "code":
                    user_prompt = profile_prompts["user_code_bi"]
                else:
                    user_prompt = profile_prompts["user_bi"]
            else:  # ae
                # Analytics Engineering Mode
                if qtype == "intro":
                    user_prompt = profile_prompts["user_intro_ae"]
                elif qtype == "interview":
                    user_prompt = profile_prompts["user_interview_ae"]
                elif qtype == "dbt":
                    user_prompt = profile_prompts["user_dbt_ae"]
                elif qtype == "pipeline":
                    user_prompt = profile_prompts["user_pipeline_ae"]
                elif qtype == "code":
                    user_prompt = profile_prompts["user_code_ae"]
                else:
                    user_prompt = profile_prompts["user_ae"]
        
        # Format user prompt with context
        user_prompt = user_prompt.format(question=question, context=context)
        
        # Generate response using OpenAI
        from api.utils import _get_client
        client = _get_client()
        print("Generating response with OpenAI...")
        
        max_tokens = 1000 if qtype == "intro" else 800
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            top_p=0.92,
            frequency_penalty=0.3,
            presence_penalty=0.0,
            max_tokens=max_tokens,
            timeout=15.0,
            stream=False
        )
        print("Response generated successfully")
        
        # Apply humanization post-processor (pass domain for PL/SQL-specific stripping)
        raw_answer = response.choices[0].message.content
        final_answer = humanize(raw_answer, qtype=qtype, domain=domain, question=question)
        print(f"Answer humanized: {len(raw_answer)} -> {len(final_answer)} chars")
        
        return {
            "answer": final_answer,
            "domain_used": domain,
            "qtype_used": qtype,
            "auto_detected": auto_detected,
            "profile_used": profile,
            "profile_auto_detected": profile_auto_detected,
            "template_used": "legacy",
            "intent": "legacy",
            "confidence": 1.0,
            "template": "legacy",
            "latency_ms": 0,  # TODO: measure actual latency
            "sources": [
                {
                    "title": r["source"],
                    "snippet": r["content"][:200] + "..." if len(r["content"]) > 200 else r["content"],
                    "path": r.get("metadata", {}).get("file_path") or r["source"],
                    "score": round(r["score"], 4)
                } for r in results
            ],
            "citations": []
        }
        
    except Exception as e:
        print(f"Error in answer_question_enhanced: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
