from utils import handler_response, openai_client
import json
import base64
import io

def handler(event, context):
    """Handle audio transcription requests."""
    try:
        # Handle CORS preflight
        if event['httpMethod'] == 'OPTIONS':
            return handler_response({}, 200)
        
        if event['httpMethod'] != 'POST':
            return handler_response({'error': 'Method not allowed'}, 405)
        
        # Parse multipart form data
        content_type = event.get('headers', {}).get('content-type', '')
        
        if 'multipart/form-data' not in content_type:
            return handler_response({'error': 'Content-Type must be multipart/form-data'}, 400)
        
        # Extract audio file from request body
        # Note: Vercel handles multipart parsing differently
        # For now, we'll expect base64 encoded audio data
        body = json.loads(event['body']) if event['body'] else {}
        audio_data = body.get('audio_data')
        
        if not audio_data:
            return handler_response({'error': 'No audio file provided'}, 400)
        
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(audio_data)
        except Exception as e:
            return handler_response({'error': 'Invalid audio data format'}, 400)
        
        # Create audio file object
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "recording.webm"
        
        # Transcribe using OpenAI Whisper
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="text"
        )
        
        return handler_response({
            'transcript': transcript.strip()
        })
        
    except Exception as e:
        print(f"Error in transcribe handler: {e}")
        return handler_response({'error': f'Transcription failed: {str(e)}'}, 500)
