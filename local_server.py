from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import json
import os
from openai import OpenAI
from api.utils import answer_question
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Initialize FastAPI app
app = FastAPI(title="RAG Chatbot API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY', 'sk-test-key'))

@app.get("/")
async def root():
    return {
        "message": "RAG Chatbot API",
        "status": "running",
        "endpoints": ["/api/health", "/api/chat", "/api/transcribe"]
    }

@app.get("/api/health")
async def health_check():
    return {
        "message": "RAG Chatbot Server",
        "status": "running",
        "api_key_configured": bool(os.getenv('OPENAI_API_KEY'))
    }

@app.post("/api/chat")
async def chat(request: dict):
    try:
        query = request.get('message', '').strip()
        profile = request.get('profile', 'krishna')
        mode = request.get('mode', 'de')
        conversation_history = request.get('conversation_history', [])
        
        if not query:
            raise HTTPException(status_code=400, detail="Message is required")
        
        # Use the utils_simple.py function
        result = answer_question(
            question=query,
            profile=profile,
            mode=mode
        )
        
        return {
            "answer": result['answer'],
            "sources": result.get('sources', []),
            "mode_used": mode,
            "profile_used": profile
        }
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")

@app.post("/api/transcribe")
async def transcribe(request: Request):
    try:
        body = await request.json()
        audio_data = body.get('audio_data')
        
        if not audio_data:
            raise HTTPException(status_code=400, detail="No audio data provided")
        
        # Decode base64 audio data
        import base64
        import io
        audio_bytes = base64.b64decode(audio_data)
        
        # Create audio file object for OpenAI Whisper
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "recording.webm"  # OpenAI API expects a file-like object with a name
        
        print(f"Audio file size: {len(audio_bytes)} bytes")
        print(f"Audio file first 50 bytes: {audio_bytes[:50]}")
        
        # Transcribe using OpenAI Whisper
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
        
        return {"transcript": transcript.strip()}
        
    except Exception as e:
        print(f"Error in transcribe endpoint: {e}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
