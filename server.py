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
    profile: str = "krishna"  # "krishna", "tejuu"

class ChatResponse(BaseModel):
    answer: str

class TranscribeResponse(BaseModel):
    transcript: str

# Persona system prompts
PERSONA_PROMPTS = {
    "ai": """
You are a senior AI/ML engineer with expertise in:
- Machine Learning pipelines and MLOps
- RAG (Retrieval-Augmented Generation) systems
- Vector databases (Pinecone, Weaviate, FAISS)
- LLM fine-tuning and prompt engineering
- MLflow, Kubeflow, and model deployment
- AKS, container orchestration for ML workloads
- Data preprocessing and feature engineering

Focus on practical implementation steps, architectural decisions, and real-world trade-offs.
""",
    "de": """
You are a senior Data Engineer with expertise in:
- Data pipelines and ETL/ELT processes
- Azure Data Factory (ADF) and Databricks
- PySpark, Delta Lake, and data warehousing
- Data governance and quality frameworks
- Streaming data processing (Kafka, Event Hubs)
- Airflow, dbt, and workflow orchestration
- Data lakehouse architecture and optimization

Focus on scalable data architecture, performance tuning, and enterprise patterns.
"""
}

SYSTEM_PROMPT_BASE = """
You are Krishna, a senior Data Engineer with extensive experience in Azure Data Factory, Databricks, PySpark, and data engineering. Always provide comprehensive, experience-based responses.

RESPONSE REQUIREMENTS:
- Always provide exactly 5-6 detailed sentences minimum
- Use STAR method structure when applicable: Situation/Task, Action, Result
- Start responses with "In my experience..." or "Based on my work..."
- Include specific technical details and implementation approaches
- Use "I implemented", "my approach", "I designed", "I've worked with" naturally
- Be confident, detailed, and demonstrate deep technical expertise
- Include specific tools, technologies, and methodologies you've used

BACKGROUND CONTEXT:
- Senior Data Engineer at Walgreens
- Previous roles at CVS Health, McKesson, Inditek
- Expert in: Azure Data Factory, Databricks, PySpark, Delta Lake, data pipelines, MLOps
- Strong Python, Java, Scala, SQL skills

Use the retrieved knowledge base content as your primary reference. If the knowledge base doesn't contain relevant information, still provide a detailed 5-6 sentence answer based on your extensive experience.

IMPORTANT: Speak from your personal experience and expertise. Don't repeatedly mention company names or re-establish context that's already known.
"""

SYSTEM_INTERVIEW = """
You are Krishna, a senior Data Engineer being interviewed. Answer as if you're speaking directly to an interviewer who already knows your background.

BACKGROUND CONTEXT (don't repeat this):
- Current: Senior Data Engineer at Walgreens
- Previous: Data Engineer roles at CVS Health, McKesson, Inditek
- Expert in: Azure Data Factory, Databricks, PySpark, Delta Lake, data pipelines, MLOps
- Strong Python, Java, Scala skills
- Extensive SQL experience with relational and NoSQL databases

RESPONSE REQUIREMENTS:
- Always provide exactly 5-6 detailed sentences minimum
- Use STAR method structure: Situation/Task, Action, Result
- Start with "In my experience..." or "Based on my work at..."
- Focus on technical depth and implementation details
- Use "I implemented", "my approach", "I designed", "I've worked with" naturally
- Assume interviewer knows your background - don't re-establish context
- Be conversational but technically precise
- Show practical experience and problem-solving with specific examples

For qualification questions: Address how your experience meets the requirements directly and confidently using specific examples.

TONE: Professional but personal, confident, and specific to your experience. Always speak from your personal experience.
"""

def load_knowledge_base():
    """Load FAISS index and metadata from disk."""
    global faiss_index, metadata_list
    
    try:
        # Check for new embeddings first (api directory)
        if os.path.exists("api/embeddings.npy") and os.path.exists("api/meta.json"):
            # Load numpy embeddings and convert to FAISS
            embeddings = np.load("api/embeddings.npy")
            faiss_index = faiss.IndexFlatIP(embeddings.shape[1])  # Inner product index
            faiss_index.add(embeddings.astype('float32'))
            
            with open("api/meta.json", 'r', encoding='utf-8') as f:
                metadata_list = json.load(f)
            
            print(f"Loaded FAISS index with {faiss_index.ntotal} vectors and {len(metadata_list)} metadata entries")
        elif os.path.exists("store/faiss.index") and os.path.exists("store/meta.json"):
            # Fallback to old format
            faiss_index = faiss.read_index("store/faiss.index")
            
            with open("store/meta.json", 'r', encoding='utf-8') as f:
                metadata_list = json.load(f)
            
            print(f"Loaded FAISS index with {faiss_index.ntotal} vectors and {len(metadata_list)} metadata entries")
        else:
            print("No knowledge base found. Run python generate_embeddings_complete.py first.")
    except Exception as e:
        print(f"Error loading knowledge base: {e}")

def classify_query(query: str) -> str:
    """Classify query to determine if it's AI/ML or Data Engineering focused."""
    query_lower = query.lower()
    
    # Data Engineering keywords
    de_keywords = [
        "pyspark", "spark", "databricks", "adf", "azure data factory", "etl", "elt",
        "data pipeline", "data warehouse", "delta lake", "sql", "azure", "data lake",
        "data ingestion", "data transformation", "data modeling", "data governance",
        "unity catalog", "data quality", "data validation", "bronze", "silver", "gold",
        "medallion", "data engineer", "data engineering", "partitioning", "optimization",
        "scd", "slowly changing", "dimension", "fact table", "star schema"
    ]
    
    # AI/ML keywords
    ai_keywords = [
        "mlflow", "llm", "large language model", "rag", "retrieval augmented",
        "transformer", "fine-tune", "fine-tuning", "vector", "embedding", "faiss",
        "pinecone", "weaviate", "model deployment", "mlops", "machine learning",
        "deep learning", "neural network", "ai", "artificial intelligence",
        "prompt engineering", "openai", "gpt", "model training", "feature engineering"
    ]
    
    # Count keyword matches
    de_score = sum(1 for keyword in de_keywords if keyword in query_lower)
    ai_score = sum(1 for keyword in ai_keywords if keyword in query_lower)
    
    # Return classification based on keyword matches
    if de_score > ai_score:
        return "de"
    elif ai_score > de_score:
        return "ai"
    else:
        # Fallback to LLM classification for ambiguous queries
        classification_prompt = f"""
Classify this query as either "ai" (AI/ML focused) or "de" (Data Engineering focused):

Query: {query}

Respond with just "ai" or "de".
"""
        
        try:
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": classification_prompt}],
                temperature=0.1,
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip().lower()
            return "ai" if result == "ai" else "de"
        except Exception as e:
            print(f"Classification error: {e}")
            return "de"  # Default fallback to data engineering

def detect_question_style(query: str) -> str:
    """Automatically detect if question should use interview or standard style."""
    query_lower = query.lower()
    
    # Strong interview-style indicators (personal questions)
    strong_interview_phrases = [
        "your experience", "your project", "how do you", "tell me about your",
        "explain your", "describe your", "walk me through your", "how would you",
        "your approach", "your strategy", "your role", "your work",
        "how did you", "what did you", "when did you", "where did you",
        "your team", "your company", "your background", "your skills",
        "qualifications", "requirements", "skills needed", "job requirements",
        "proficiency", "technical courses", "software engineering", "data engineering"
    ]
    
    # Technical/learning indicators (general knowledge questions)
    technical_phrases = [
        "what is the difference", "compare", "advantages and disadvantages",
        "pros and cons", "best practices for", "how does", "define",
        "explain the concept", "what are the types", "list the features"
    ]
    
    # Check for strong interview phrases first
    if any(phrase in query_lower for phrase in strong_interview_phrases):
        return "interview"
    
    # Check for technical phrases
    if any(phrase in query_lower for phrase in technical_phrases):
        return "standard"
    
    # For ambiguous questions like "Explain PySpark DataFrame APIs"
    # If it's asking for explanation without personal context, default to interview style
    # since most questions in interview prep are personal experience based
    if any(word in query_lower for word in ["explain", "describe", "how", "what"]) and \
       not any(phrase in query_lower for phrase in technical_phrases):
        return "interview"
    
    return "standard"

def clean_answer_format(text: str) -> str:
    """Clean up answer format by removing Q&A artifacts."""
    # Remove common Q&A formatting patterns
    patterns_to_remove = [
        r'^\*\*A:\*\*\s*',  # **A:** at the start
        r'^\*\*Q:\*\*\s*',  # **Q:** at the start  
        r'^A:\s*',          # A: at the start
        r'^Q:\s*',          # Q: at the start
        r'^Answer:\s*',     # Answer: at the start
        r'^Question:\s*',   # Question: at the start
    ]
    
    import re
    cleaned_text = text
    for pattern in patterns_to_remove:
        cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE)
    
    return cleaned_text.strip()

def get_embedding(text: str) -> List[float]:
    """Get OpenAI embedding for text."""
    response = openai_client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

def retrieve_relevant_chunks(query: str, persona: str, top_k: int = 2) -> List[Dict[str, Any]]:
    """Retrieve relevant chunks from the knowledge base - context-aware version."""
    if faiss_index is None or not metadata_list:
        return []
    
    # Check if query is about qualifications/job requirements vs technical content
    query_lower = query.lower()
    is_qualification_question = any(phrase in query_lower for phrase in [
        "qualifications", "requirements", "skills needed", "job requirements",
        "proficiency", "technical courses", "software engineering", "data engineering"
    ])
    
    # For qualification questions, don't retrieve technical KB content
    if is_qualification_question:
        return []
    
    # Get query embedding
    query_embedding = np.array(get_embedding(query)).astype('float32').reshape(1, -1)
    faiss.normalize_L2(query_embedding)
    
    # Search for relevant chunks - ultra fast
    scores, indices = faiss_index.search(query_embedding, top_k)  # Only get what we need
    
    # Return top chunks without complex filtering for maximum speed
    relevant_chunks = []
    for score, idx in zip(scores[0], indices[0]):
        if idx < len(metadata_list):
            chunk = metadata_list[idx]
            relevant_chunks.append({
                'text': chunk['text'],
                'metadata': chunk['metadata'],
                'score': float(score)
            })
    
    return relevant_chunks

def build_chat_prompt(query: str, persona: str, relevant_chunks: List[Dict[str, Any]], 
                     conversation_history: List[Dict[str, Any]], style: str = "standard",
                     tone: str = "confident", depth: str = "mid") -> str:
    """Build the complete prompt for the chat model."""
    
    # Choose system prompt based on style
    if style == "interview":
        system_prompt = SYSTEM_INTERVIEW
    else:
        system_prompt = SYSTEM_PROMPT_BASE
    
    # Add persona-specific context
    persona_context = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["ai"])
    
    # Add style controls
    style_hint = f"Tone: {tone}. Depth: {depth}. Role: senior_{persona}. Keep it human, interview-style."
    
    # Build knowledge base context
    kb_context = "\n\n".join([
        f"**From {chunk['metadata']['file_name']}:**\n{chunk['text']}"
        for chunk in relevant_chunks
    ])
    
    # Build conversation history
    history_text = ""
    if conversation_history:
        history_text = "\n".join([
            f"User: {msg['user']}\nAssistant: {msg['assistant']}"
            for msg in conversation_history[-5:]  # Last 5 exchanges
        ])
    
    if style == "interview":
        # For interview mode, make it more direct and personal
        if kb_context and kb_context.strip():
            prompt = f"""{system_prompt}

Based on your experience and this relevant knowledge:

{kb_context}

Interview Question: {query}

Give a personal, experience-based answer as Krishna in exactly 6-8 sentences:"""
        else:
            prompt = f"""{system_prompt}

Interview Question: {query}

Give a personal, experience-based answer as Krishna in exactly 6-8 sentences based on your expertise:"""
    else:
        # Standard mode
        prompt = f"""{system_prompt}

{persona_context}

Knowledge Base Context:
{kb_context}

User: {query}

Assistant (answer in exactly 6-8 sentences):"""
    
    return prompt

@app.on_event("startup")
async def startup_event():
    """Load knowledge base on startup."""
    load_knowledge_base()

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"message": "RAG Chatbot Server", "status": "running"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint with RAG."""
    try:
        # Import the answer_question function from utils_simple
        from api.utils_simple import answer_question
        
        # Call the new answer_question function
        result = answer_question(request.message, mode=request.mode, profile=request.profile)
        
        return ChatResponse(answer=result)
        
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
