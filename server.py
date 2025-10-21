#!/usr/bin/env python3
"""
RAG Chatbot Server with dual persona support (AI/ML + Data Engineering).
Provides /chat and /transcribe endpoints.
"""

import os
import json
import numpy as np
import faiss
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="RAG Chatbot", version="1.0.0")

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files will be mounted at the end after API routes

# Global variables for loaded index and metadata
faiss_index: Optional[faiss.Index] = None
metadata_list: List[Dict[str, Any]] = []
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.get("/")
async def read_root():
    """Serve the main HTML file."""
    return FileResponse("frontend/build/index.html")

# Request/Response models
class ChatRequest(BaseModel):
    message: str
    mode: str = "auto"  # "auto", "ai", "de", "bi", "ae"
    profile: str = "auto"  # "auto", "krishna", "tejuu"
    session_id: str = "default"  # Session ID for conversation memory

class ChatResponse(BaseModel):
    answer: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    template_used: Optional[str] = None
    latency_ms: Optional[int] = None
    sources: Optional[List[Dict[str, Any]]] = None
    citations: Optional[List[int]] = None
    timings: Optional[Dict[str, int]] = None

class TranscribeResponse(BaseModel):
    transcript: str

# Note: All prompt logic is in api/utils.py
# This server delegates to answer_question() from api.utils

@app.on_event("startup")
async def startup_event():
    """Initialize on startup."""
    print("RAG Chatbot Server starting up...")

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"message": "RAG Chatbot Server", "status": "running"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with RAG - delegates to api.utils.answer_question()."""
    try:
        from api.utils import answer_question
        
        # Call answer_question with auto-detection support and session_id
        result = answer_question(request.message, mode=request.mode, profile=request.profile, session_id=request.session_id)
        
        return ChatResponse(
            answer=result.get('answer', 'No response generated'),
            intent=result.get('intent'),
            confidence=result.get('confidence'),
            template_used=result.get('template_used'),
            latency_ms=result.get('latency_ms'),
            sources=result.get('sources'),
            citations=result.get('citations'),
            timings=result.get('timings')
        )
        
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe(data: dict):
    """Transcribe audio to text using OpenAI Whisper"""
    try:
        audio_data = data.get('audio_data')
        
        if not audio_data:
            raise HTTPException(status_code=400, detail="No audio data provided")
        
        # Decode base64 audio data
        import base64
        import io
        audio_bytes = base64.b64decode(audio_data)
        
        # Create audio file object for OpenAI Whisper
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "recording.webm"  # OpenAI API expects a file-like object with a name
        
        # Transcribe using OpenAI Whisper
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
        
        return TranscribeResponse(transcript=transcript.strip())
        
    except Exception as e:
        print(f"Error in transcribe endpoint: {e}")
        return TranscribeResponse(transcript="")

# Mount static files at the end (after API routes)
app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")
app.mount("/", StaticFiles(directory="frontend/build", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
