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
        
        # Parse JSON request with base64 audio data
        try:
            body = json.loads(event['body']) if event['body'] else {}
        except json.JSONDecodeError:
            return handler_response({'error': 'Invalid JSON in request body'}, 400)
        
        audio_data = body.get('audio_data')
        
        if not audio_data:
            return handler_response({'error': 'No audio data provided'}, 400)
        
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(audio_data)
        except Exception as e:
            return handler_response({'error': f'Invalid audio data format: {str(e)}'}, 400)
        
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
