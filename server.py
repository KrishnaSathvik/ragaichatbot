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
from fastapi import FastAPI, HTTPException, UploadFile, File
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

class ChatResponse(BaseModel):
    answer: str

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
        
        # Call answer_question with auto-detection support
        result = answer_question(request.message, mode=request.mode, profile=request.profile)
        
        return ChatResponse(answer=result.get('answer', 'No response generated'))
        
    except Exception as e:
        print(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@app.post("/api/transcribe", response_model=TranscribeResponse)
async def transcribe(audio_file: UploadFile = File(...)):
    """Transcribe audio using OpenAI Whisper - optimized for speed."""
    try:
        # Save uploaded file temporarily
        temp_path = f"temp_{audio_file.filename}"
        with open(temp_path, "wb") as buffer:
            content = await audio_file.read()
            buffer.write(content)
        
        # Transcribe with Whisper - optimized for speed
        with open(temp_path, "rb") as audio_file_obj:
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file_obj,
                response_format="text",  # Faster than JSON
                temperature=0.0,         # Deterministic
                language="en"            # Specify language for speed
            )
        
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)
        
        # Handle both string and object responses
        if isinstance(transcript, str):
            transcript_text = transcript
        else:
            transcript_text = transcript.text
        
        return TranscribeResponse(transcript=transcript_text)
        
    except Exception as e:
        # Clean up temp file on error
        if 'temp_path' in locals() and os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Transcription error: {str(e)}")

# Mount static files at the end (after API routes)
app.mount("/static", StaticFiles(directory="frontend/build/static"), name="static")
app.mount("/", StaticFiles(directory="frontend/build", html=True), name="frontend")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
