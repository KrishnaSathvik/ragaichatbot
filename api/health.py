from utils import handler_response

def handler(event, context):
    """Health check endpoint."""
    return handler_response({
        'message': 'RAG Chatbot Server',
        'status': 'running'
    })
