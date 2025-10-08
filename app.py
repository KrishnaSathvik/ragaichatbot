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
from fastapi.responses import FileResponse
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

# Mount static files (for the frontend)
app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def serve_frontend():
    """Serve the frontend HTML file"""
    return FileResponse("index.html")

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
    """Chat endpoint"""
    try:
        message = data.get("message", "").strip()
        mode = data.get("mode", "auto")
        
        if not message:
            raise HTTPException(status_code=400, detail="Message is required")
        
        result = answer_question(message, mode=mode)
        
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
