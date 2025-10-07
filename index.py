import json, os
from api.utils import answer_question, health_check

ALLOWED_ORIGIN = os.getenv("ALLOWED_ORIGIN", "*")


def _resp(body: dict | str, status=200, headers=None):
    base = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,Authorization"
    }
    if headers:
        base.update(headers)
    return {
        "statusCode": status,
        "headers": base,
        "body": body if isinstance(body, str) else json.dumps(body)
    }


def handler(event, context):
    try:
        path = event.get("path", "")
        method = event.get("httpMethod", "GET").upper()

        if method == "OPTIONS":
            return _resp("", 204)

        if path.endswith("/api/health") and method == "GET":
            return _resp(health_check(), 200)

        if path.endswith("/api/chat") and method == "POST":
            body = json.loads(event.get("body") or "{}")
            message = (body.get("message") or "").strip()
            mode = body.get("mode")
            if not message:
                return _resp({"error": "message is required"}, 400)
            result = answer_question(message, mode=mode)
            if "error" in result:
                return _resp(result, 400)
            return _resp(result, 200)

        # Optional placeholder; wire multipart if needed later
        if path.endswith("/api/transcribe") and method == "POST":
            return _resp({"error": "transcribe not implemented in serverless adapter"}, 501)

        return _resp({"error": "Not Found"}, 404)

    except Exception as e:
        # surface error in logs but keep response shape stable
        print("[handler-error]", repr(e))
        return _resp({"error": str(e)}, 500)