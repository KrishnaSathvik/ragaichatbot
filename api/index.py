from http.server import BaseHTTPRequestHandler
import json
import os
from urllib.parse import urlparse
from utils import handler_response, load_knowledge_base, openai_client

# Load knowledge base on startup
load_knowledge_base()

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def do_GET(self):
        # Parse the URL to determine the endpoint
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/api' or path == '/api/':
            response = {"message": "RAG Chatbot API", "status": "running", "endpoints": ["/api/health", "/api/chat"]}
        elif path == '/api/health':
            response = {"message": "RAG Chatbot Server", "status": "running"}
        else:
            response = {"message": "API is working!", "status": "success"}
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def do_POST(self):
        # Parse the URL to determine the endpoint
        parsed_url = urlparse(self.path)
        path = parsed_url.path
        
        if path == '/api/chat':
            self.handle_chat()
        elif path == '/api/transcribe':
            self.handle_transcribe()
        else:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            response = {"message": "API POST is working!", "status": "success"}
            self.wfile.write(json.dumps(response).encode())
    
    def handle_chat(self):
        try:
            # Import chat logic
            from utils import detect_question_style, clean_answer_format, retrieve_relevant_chunks, build_chat_prompt
            
            # Read request body
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            body = json.loads(post_data.decode('utf-8'))
            
            query = body.get('message', '').strip()
            mode = body.get('mode', 'auto')
            conversation_history = body.get('conversation_history', [])
            style = body.get('style', 'standard')
            tone = body.get('tone', 'confident')
            depth = body.get('depth', 'mid')
            
            if not query:
                self.send_error_response(400, {'error': 'Message is required'})
                return
            
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
            response_data = {
                'answer': answer,
                'sources': [],  # No sources shown to user
                'mode_used': persona
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            print(f"Error in chat handler: {e}")
            self.send_error_response(500, {'error': f'Error generating response: {str(e)}'})
    
    def handle_transcribe(self):
        try:
            # For now, return a simple response since multipart parsing is complex in Vercel
            # The frontend will show this message instead of crashing
            response_data = {
                'transcript': 'Audio transcription is temporarily disabled. Please type your message instead.'
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode())
            
        except Exception as e:
            print(f"Error in transcribe handler: {e}")
            self.send_error_response(500, {'error': f'Transcription error: {str(e)}'})
    
    def send_error_response(self, status_code, error_data):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(error_data).encode())
