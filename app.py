#!/usr/bin/env python3
"""
Render deployment version of the RAG chatbot.
This uses FastAPI for Render's web service deployment.
"""

import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from api.utils_simple import answer_question, health_check

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
async def transcribe():
    """Transcribe endpoint (placeholder)"""
    return {"error": "Transcription not implemented yet"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
