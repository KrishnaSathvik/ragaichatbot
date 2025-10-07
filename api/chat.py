from utils import (
    detect_question_style, clean_answer_format, retrieve_relevant_chunks,
    load_knowledge_base, build_chat_prompt, handler_response, openai_client
)
import json

# Load knowledge base on module import
load_knowledge_base()

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
        conversation_history = body.get('conversation_history', [])
        style = body.get('style', 'standard')
        tone = body.get('tone', 'confident')
        depth = body.get('depth', 'mid')
        
        if not query:
            return handler_response({'error': 'Message is required'}, 400)
        
        # Auto-detect style if not specified
        if style == 'standard':
            style = detect_question_style(query)
        
        # Determine persona based on mode
        persona = mode if mode in ['ai', 'de'] else 'de'  # Default to DE for auto
        
        # Retrieve relevant chunks
        relevant_chunks = retrieve_relevant_chunks(query, persona, top_k=2)
        
        # Build prompt
        prompt = build_chat_prompt(query, persona, relevant_chunks, conversation_history,
                                 style, tone, depth)
        
        # Generate response
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=600,
            timeout=8,
            stream=False
        )
        
        answer = response.choices[0].message.content.strip()
        
        # Clean up answer format - remove Q&A artifacts
        answer = clean_answer_format(answer)
        
        # Return clean answer without sources for better readability
        return handler_response({
            'answer': answer,
            'sources': [],  # No sources shown to user
            'mode_used': persona
        })
        
    except Exception as e:
        print(f"Error in chat handler: {e}")
        return handler_response({'error': f'Error generating response: {str(e)}'}, 500)
