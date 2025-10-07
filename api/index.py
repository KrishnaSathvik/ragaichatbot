from http.server import BaseHTTPRequestHandler
import json

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>RAG AI Chatbot - Testing</title>
        </head>
        <body>
            <h1>RAG AI Chatbot is Working!</h1>
            <p>Deployment successful. The API is functioning.</p>
            <p><a href="/api/test">Test API</a></p>
            <p><a href="/api/health">Health Check</a></p>
        </body>
        </html>
        """
        
        self.wfile.write(html_content.encode())
        return
