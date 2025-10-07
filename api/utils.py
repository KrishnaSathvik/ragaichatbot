import os
import json
import numpy as np
import faiss
from typing import List, Dict, Any
from openai import OpenAI

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Global variables for knowledge base
faiss_index = None
metadata_list = []

# Persona definitions
PERSONAS = {
    "ai": "AI/ML Expert",
    "de": "Data Engineering Expert", 
    "auto": "Auto-detect based on question"
}

SYSTEM_PROMPT_BASE = """
You are a senior technical expert providing concise, focused guidance. Always give exactly 6-8 sentences that demonstrate deep understanding.

RESPONSE REQUIREMENTS:
- Exactly 6-8 sentences maximum
- Focus on practical implementation and experience
- Give specific, actionable insights
- Use "I implemented", "my approach", "I designed" naturally
- Be confident and direct

Use the retrieved knowledge base content as your primary reference. If the knowledge base doesn't contain relevant information, still provide a concise 6-8 sentence answer based on your expertise.

IMPORTANT: Don't repeatedly mention company names or re-establish context that's already known. Give direct, confident answers as if speaking to someone familiar with your background.
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
- Exactly 6-8 sentences maximum
- Give direct, confident answers without repeating company names
- Focus on technical depth and implementation details
- Use "I implemented", "my approach", "I designed" naturally
- Assume interviewer knows your background - don't re-establish context
- Be conversational but technically precise
- Show practical experience and problem-solving

For qualification questions: Address how your experience meets the requirements directly and confidently.

TONE: Professional but personal, confident, and specific to your experience.
"""

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
    
    # For ambiguous questions, default to interview style since most questions 
    # in interview prep are personal experience based
    if any(word in query_lower for word in ["explain", "describe", "how", "what"]):
        return "interview"
    
    return "interview"  # Default to interview style for better personal responses

def clean_answer_format(text: str) -> str:
    """Clean up answer format by removing Q&A artifacts."""
    import re
    patterns_to_remove = [
        r'^\*\*A:\*\*\s*',  # **A:** at the start
        r'^\*\*Q:\*\*\s*',  # **Q:** at the start  
        r'^A:\s*',          # A: at the start
        r'^Q:\s*',          # Q: at the start
        r'^Answer:\s*',     # Answer: at the start
        r'^Question:\s*',   # Question: at the start
    ]
    
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

def load_knowledge_base():
    """Load FAISS index and metadata from disk."""
    global faiss_index, metadata_list
    try:
        # Load FAISS index - try multiple possible locations
        index_paths = ["store/faiss.index", "faiss.index", "kb_index.faiss"]
        metadata_paths = ["store/meta.json", "meta.json", "kb_metadata.json"]
        
        faiss_index = None
        metadata_list = []
        
        for index_path in index_paths:
            try:
                faiss_index = faiss.read_index(index_path)
                print(f"Loaded FAISS index from {index_path}")
                break
            except:
                continue
                
        for metadata_path in metadata_paths:
            try:
                with open(metadata_path, "r") as f:
                    metadata_list = json.load(f)
                print(f"Loaded metadata from {metadata_path}")
                break
            except:
                continue
        
        if faiss_index and metadata_list:
            print(f"Successfully loaded FAISS index with {faiss_index.ntotal} vectors and {len(metadata_list)} metadata entries")
        else:
            print("Warning: Could not load knowledge base files")
            faiss_index = None
            metadata_list = []
            
    except Exception as e:
        print(f"Error loading knowledge base: {e}")
        faiss_index = None
        metadata_list = []

def build_chat_prompt(query: str, persona: str, relevant_chunks: List[Dict[str, Any]], 
                     conversation_history: List[Dict[str, Any]], style: str = "standard",
                     tone: str = "confident", depth: str = "mid") -> str:
    """Build the complete prompt for the chat model."""
    
    # Determine system prompt based on style
    if style == "interview":
        system_prompt = SYSTEM_INTERVIEW
    else:
        system_prompt = SYSTEM_PROMPT_BASE
    
    # Build persona context
    persona_context = PERSONAS.get(persona, "Technical Expert")
    
    # Build knowledge base context
    kb_context = ""
    if relevant_chunks:
        kb_context = "\n\n".join([chunk['text'] for chunk in relevant_chunks])
    else:
        kb_context = "No specific knowledge base content available for this query."
    
    # Build conversation history
    history_text = ""
    if conversation_history:
        history_text = "\n\n".join([
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

def handler_response(data: dict, status_code: int = 200):
    """Create a proper Vercel response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization'
        },
        'body': json.dumps(data)
    }
