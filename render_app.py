#!/usr/bin/env python3
"""
Render deployment version of the RAG chatbot.
This uses FastAPI for Render's web service deployment.
"""

import json
import os
import tempfile
from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, StreamingResponse
from api.utils_simple import answer_question, health_check
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI(title="RAG AI Chatbot", version="1.0.0")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Check if frontend build exists
FRONTEND_BUILD_DIR = "frontend/build"
FRONTEND_STATIC_DIR = os.path.join(FRONTEND_BUILD_DIR, "static")
FRONTEND_EXISTS = os.path.exists(FRONTEND_BUILD_DIR) and os.path.exists(FRONTEND_STATIC_DIR)

if FRONTEND_EXISTS:
    # Mount static files for production build (CSS, JS, etc.)
    app.mount("/static", StaticFiles(directory=FRONTEND_STATIC_DIR), name="static")
    
    # Serve individual static files (logo, favicon, etc.)
    @app.get("/logo.png")
    async def serve_logo():
        return FileResponse(os.path.join(FRONTEND_BUILD_DIR, "logo.png"))
    
    @app.get("/favicon.ico")
    async def serve_favicon():
        return FileResponse(os.path.join(FRONTEND_BUILD_DIR, "favicon.ico"))
    
    @app.get("/favicon.svg")
    async def serve_favicon_svg():
        return FileResponse(os.path.join(FRONTEND_BUILD_DIR, "favicon.svg"))
    
    @app.get("/android-chrome-192x192.png")
    async def serve_android_chrome_192():
        return FileResponse(os.path.join(FRONTEND_BUILD_DIR, "android-chrome-192x192.png"))
    
    @app.get("/android-chrome-512x512.png")
    async def serve_android_chrome_512():
        return FileResponse(os.path.join(FRONTEND_BUILD_DIR, "android-chrome-512x512.png"))
    
    @app.get("/apple-touch-icon.png")
    async def serve_apple_touch_icon():
        return FileResponse(os.path.join(FRONTEND_BUILD_DIR, "apple-touch-icon.png"))
    
    @app.get("/site.webmanifest")
    async def serve_manifest():
        return FileResponse(os.path.join(FRONTEND_BUILD_DIR, "site.webmanifest"))
    
    @app.get("/")
    async def serve_frontend():
        """Serve the frontend HTML file"""
        return FileResponse(os.path.join(FRONTEND_BUILD_DIR, "index.html"))
else:
    print("⚠️  Frontend build not found. Running in API-only mode.")
    
    @app.get("/")
    async def root():
        """Root endpoint - API only mode"""
        return {
            "message": "RAG AI Chatbot API",
            "status": "running",
            "mode": "api-only",
            "note": "Frontend not built. Access API endpoints at /api/*"
        }

@app.get("/api/health")
async def health():
    """Health check endpoint"""
    try:
        result = health_check()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debug")
async def debug():
    """Debug endpoint to check environment variables"""
    return {
        "openai_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "openai_key_length": len(os.getenv("OPENAI_API_KEY", "")),
        "python_version": os.sys.version,
        "openai_version": "1.40.0"  # From requirements.txt
    }

@app.post("/api/chat")
async def chat(data: dict):
    """Chat endpoint with optional streaming and profile selection"""
    try:
        message = data.get("message", "").strip()
        mode = data.get("mode", "auto")
        profile = data.get("profile", "krishna")
        stream = data.get("stream", False)
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        result = answer_question(message, mode=mode, profile=profile, stream=stream)
        
        if "error" in result:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/transcribe")
async def transcribe(audio: UploadFile = File(...)):
    """Transcribe audio to text using OpenAI Whisper"""
    try:
        # Create a temporary file to store the uploaded audio
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as temp_file:
            # Read the uploaded file and write to temp file
            contents = await audio.read()
            temp_file.write(contents)
            temp_file_path = temp_file.name
        
        try:
            # Use OpenAI Whisper API to transcribe
            with open(temp_file_path, "rb") as audio_file:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    response_format="text"
                )
            
            # transcript is already a string when response_format="text"
            print(f"Transcription result: {repr(transcript)}")
            print(f"Transcription type: {type(transcript)}")
            return {"transcript": transcript}
            
        finally:
            # Clean up the temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)
                
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
