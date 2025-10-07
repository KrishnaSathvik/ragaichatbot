from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        response = {
            "message": "RAG AI Chatbot API is working!",
            "status": "success",
            "timestamp": "2024-01-01T00:00:00Z"
        }
        
        self.wfile.write(json.dumps(response).encode())
        return
