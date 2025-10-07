import json
import os
from openai import OpenAI

# Initialize OpenAI client
openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

def handler_response(data: dict, status_code: int = 200):
    """Create a standardized response for Vercel."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        },
        'body': json.dumps(data)
    }

def handler(event, context):
    """Handle all API requests - consolidated endpoint."""
    try:
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return handler_response({}, 200)
        
        # Get the path from the event
        path = event.get('path', '')
        
        # Route to appropriate handler based on path
        if path == '/api/chat' or path.endswith('/chat'):
            return handle_chat(event, context)
        elif path == '/api/health' or path.endswith('/health'):
            return handle_health(event, context)
        elif path == '/api/transcribe' or path.endswith('/transcribe'):
            return handle_transcribe(event, context)
        elif path == '/api' or path.endswith('/api') or path == '/api/':
            return handler_response({
                "message": "RAG Chatbot API", 
                "status": "running", 
                "endpoints": ["/api/health", "/api/chat", "/api/transcribe"]
            })
        else:
            return handler_response({"message": "API is working!", "status": "success"})
        
    except Exception as e:
        print(f"Error in main handler: {e}")
        return handler_response({'error': f'Server error: {str(e)}'}, 500)

def handle_health(event, context):
    """Health check endpoint."""
    return handler_response({
        'message': 'RAG Chatbot Server',
        'status': 'running'
    })

def handle_chat(event, context):
    """Handle chat requests."""
    try:
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return handler_response({}, 200)
        
        if event.get('httpMethod') != 'POST':
            return handler_response({'error': 'Method not allowed'}, 405)
        
        # Parse request body
        body = json.loads(event.get('body', '{}'))
        query = body.get('message', '').strip()
        mode = body.get('mode', 'auto')
        conversation_history = body.get('conversation_history', [])
        
        if not query:
            return handler_response({'error': 'Message is required'}, 400)
        
        # Determine persona based on mode
        persona = mode if mode in ['ai', 'de'] else 'de'  # Default to DE for auto
        
        # Build a simple prompt without knowledge base for now
        system_prompt = """You are Krishna, a senior Data Engineer with extensive experience in:
- Azure Data Factory, Databricks, PySpark, Delta Lake
- Data pipelines, MLOps, and data warehousing
- Previous roles at Walgreens, CVS Health, McKesson, Inditek
- Strong Python, Java, Scala skills

Answer questions as if you're speaking from personal experience. Be specific about implementations, challenges, and solutions you've worked on. Keep responses concise but detailed (6-8 sentences)."""
        
        # Build conversation context
        context = ""
        if conversation_history:
            context = "\n\nPrevious conversation:\n"
            for msg in conversation_history[-3:]:  # Last 3 exchanges
                context += f"User: {msg.get('user', '')}\nAssistant: {msg.get('assistant', '')}\n"
        
        prompt = f"{system_prompt}\n\n{context}\n\nCurrent question: {query}\n\nAnswer as Krishna based on your experience:"
        
        # Generate response
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{context}\n\nCurrent question: {query}"}
            ],
            temperature=0.1,
            max_tokens=600,
            timeout=10
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Return clean answer
        return handler_response({
            'answer': answer,
            'sources': [],
            'mode_used': persona
        })
        
    except Exception as e:
        print(f"Error in chat handler: {e}")
        return handler_response({'error': f'Error generating response: {str(e)}'}, 500)

def handle_transcribe(event, context):
    """Handle audio transcription requests."""
    try:
        # Handle CORS preflight
        if event.get('httpMethod') == 'OPTIONS':
            return handler_response({}, 200)
        
        if event.get('httpMethod') != 'POST':
            return handler_response({'error': 'Method not allowed'}, 405)
        
        # For now, return a simple response since multipart parsing is complex in Vercel
        # The frontend will show this message instead of crashing
        return handler_response({
            'transcript': 'Audio transcription is temporarily disabled. Please type your message instead.'
        })
        
    except Exception as e:
        print(f"Error in transcribe handler: {e}")
        return handler_response({'error': f'Transcription error: {str(e)}'}, 500)
