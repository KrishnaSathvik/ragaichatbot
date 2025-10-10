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
    """Handle chat requests - uses api/utils.py for all logic."""
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
        profile = body.get('profile', 'auto')  # Support auto profile detection
        
        if not query:
            return handler_response({'error': 'Message is required'}, 400)
        
        # Import and use the improved answer_question function
        from utils import answer_question
        
        result = answer_question(
            question=query,
            mode=mode,
            profile=profile
        )
        
        if 'error' in result:
            return handler_response({'error': result['error']}, 400)
        
        # Return response with new format
        return handler_response({
            'answer': result.get('answer', 'No response generated'),
            'sources': result.get('sources', []),
            'domain_used': result.get('domain_used', mode),
            'qtype_used': result.get('qtype_used', 'general'),
            'profile_used': result.get('profile_used', profile),
            'profile_auto_detected': result.get('profile_auto_detected', False),
            'auto_detected': result.get('auto_detected', False),
            # Backward compatibility
            'mode_used': result.get('domain_used', mode)
        })
        
    except Exception as e:
        print(f"Error in chat handler: {e}")
        import traceback
        traceback.print_exc()
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
