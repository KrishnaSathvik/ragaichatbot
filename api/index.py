import json
import os
import base64

# Single entry file for Vercel: exports `handler(event, context)`

# --- Shared response helper ---
def handler_response(data: dict, status_code: int = 200):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type"
        },
        "body": json.dumps(data)
    }

# --- Safe JSON body parsing (handles base64 for some edge runtimes) ---
def _parse_json_body(event) -> dict:
    raw = event.get("body", "")
    if not raw:
        return {}
    if event.get("isBase64Encoded"):
        try:
            raw = base64.b64decode(raw).decode("utf-8", errors="ignore")
        except Exception:
            return {}
    try:
        return json.loads(raw)
    except Exception:
        return {}

# --- Normalizers ---
_ALLOWED_PROFILES = {"auto", "krishna", "tejuu"}
_ALLOWED_MODES    = {"auto", "ai", "de", "ae", "bi"}

def _cap(s: str, n: int = 4000) -> str:
    s = (s or "").strip()
    return s[:n]

# --- Router ---
def handler(event, context):
    try:
        # CORS preflight
        if event.get("httpMethod") == "OPTIONS":
            return handler_response({}, 200)

        path = (event.get("path") or "").rstrip("/")
        if path.endswith("/chat"):
            return handle_chat(event, context)
        if path.endswith("/health"):
            return handle_health(event, context)
        if path.endswith("/transcribe"):
            return handle_transcribe(event, context)

        # Root
        return handler_response({
            "message": "RAG Chatbot API",
            "status": "running",
            "endpoints": ["/api/health", "/api/chat", "/api/transcribe"]
        })

    except Exception as e:
        print(f"[handler] error: {e}")
        return handler_response({"error": f"Server error: {str(e)}"}, 500)

# --- Health ---
def handle_health(event, context):
    try:
        from utils import health_check  # uses your store loader
        hc = health_check()  # {"ok":bool,"embeddings":bool,"error":str|None}
        return handler_response({
            "message": "RAG Chatbot Server",
            "status": "running" if hc.get("ok") else "degraded",
            "embeddings_loaded": bool(hc.get("embeddings")),
            "error": hc.get("error")
        })
    except Exception as e:
        print(f"[health] error: {e}")
        return handler_response({
            "message": "RAG Chatbot Server",
            "status": "unknown",
            "embeddings_loaded": False,
            "error": str(e)
        }, 500)

# --- Chat ---
def handle_chat(event, context):
    try:
        if event.get("httpMethod") != "POST":
            return handler_response({"error": "Method not allowed"}, 405)

        body = _parse_json_body(event)
        query: str   = _cap(body.get("message", ""))
        mode: str    = (body.get("mode") or "auto").lower()
        profile: str = (body.get("profile") or "auto").lower()
        session_id: str = _cap(body.get("session_id") or body.get("sid") or "default", 200)

        if not query:
            return handler_response({"error": "Message is required"}, 400)
        if profile not in _ALLOWED_PROFILES:
            profile = "auto"
        if mode not in _ALLOWED_MODES:
            mode = "auto"

        # Phase-2 aware answerer (falls back internally if needed)
        from utils import answer_question

        result = answer_question(
            question=query,
            mode=mode,
            profile=profile,
            session_id=session_id
        )

        if not isinstance(result, dict):
            return handler_response({"error": "Invalid result from answerer"}, 500)
        if "error" in result:
            return handler_response({"error": result["error"]}, 400)

        # Standardize payload (Phase 2 + back-compat)
        payload = {
            "answer": result.get("answer", "No response generated"),
            "sources": result.get("sources", []),

            # Phase-2 metadata if present
            "intent": result.get("intent"),
            "confidence": result.get("confidence"),
            "template_used": result.get("template_used"),
            "latency_ms": result.get("latency_ms"),
            "timings": result.get("timings"),
            "citations": result.get("citations", []),

            # Routing decisions
            "domain_used": result.get("domain_used", mode),
            "qtype_used": result.get("qtype_used", "general"),
            "profile_used": result.get("profile_used", profile),
            "profile_auto_detected": bool(result.get("profile_auto_detected")),
            "auto_detected": bool(result.get("auto_detected")),

            # Backward-compat name
            "mode_used": result.get("domain_used", mode),
            # Echo
            "session_id": session_id
        }

        return handler_response(payload)

    except Exception as e:
        print(f"[chat] error: {e}")
        import traceback; traceback.print_exc()
        return handler_response({"error": f"Error generating response: {str(e)}"}, 500)

# --- Transcribe (stub) ---
def handle_transcribe(event, context):
    try:
        if event.get("httpMethod") != "POST":
            return handler_response({"error": "Method not allowed"}, 405)
        return handler_response({
            "transcript": "Audio transcription is temporarily disabled. Please type your message instead."
        })
    except Exception as e:
        print(f"[transcribe] error: {e}")
        return handler_response({"error": f"Transcription error: {str(e)}"}, 500)
