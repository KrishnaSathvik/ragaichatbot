def handler(event, context):
    """Simple test function to verify deployment."""
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': '{"message": "RAG AI Chatbot API is working!", "status": "success"}'
    }
