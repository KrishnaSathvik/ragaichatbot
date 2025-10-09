from utils_simple import answer_question
import json

def handler_response(data, status_code=200):
    """Simple response handler for Vercel."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS'
        },
        'body': json.dumps(data)
    }

def handler(event, context):
    """Handle chat requests."""
    try:
        # Handle CORS preflight
        if event['httpMethod'] == 'OPTIONS':
            return handler_response({}, 200)
        
        if event['httpMethod'] != 'POST':
            return handler_response({'error': 'Method not allowed'}, 405)
        
        # Parse request body
        body = json.loads(event['body'])
        query = body.get('message', '').strip()
        mode = body.get('mode', 'auto')
        profile = body.get('profile', 'krishna')  # Get profile parameter
        
        if not query:
            return handler_response({'error': 'Message is required'}, 400)
        
        # Use the answer_question function with profile and mode
        result = answer_question(query, mode=mode, profile=profile)
        
        if 'error' in result:
            return handler_response({'error': result['error']}, 400)
        
        # Return clean answer
        return handler_response({
            'answer': result.get('answer', 'No response generated'),
            'sources': [],  # No sources shown to user
            'mode_used': mode,
            'profile_used': profile
        })
        
    except Exception as e:
        print(f"Error in chat handler: {e}")
        return handler_response({'error': f'Error generating response: {str(e)}'}, 500)
