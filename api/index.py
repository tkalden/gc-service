"""
Vercel serverless function entry point
"""

import asyncio
import json
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# Import the FastAPI app from main.py
from main import app


class VercelHandler(BaseHTTPRequestHandler):
    """HTTP handler that delegates to FastAPI app"""
    
    def do_GET(self):
        self._handle_request()
    
    def do_POST(self):
        self._handle_request()
    
    def do_PUT(self):
        self._handle_request()
    
    def do_DELETE(self):
        self._handle_request()
    
    def do_OPTIONS(self):
        self._handle_request()
    
    def _handle_request(self):
        """Handle HTTP request by delegating to FastAPI"""
        try:
            # Parse the request
            parsed_url = urlparse(self.path)
            path = parsed_url.path
            query_params = parse_qs(parsed_url.query)
            
            # Get request body for POST/PUT requests
            content_length = int(self.headers.get('Content-Length', 0))
            body = None
            if content_length > 0:
                body = self.rfile.read(content_length)
            
            # Create ASGI scope
            scope = {
                "type": "http",
                "method": self.command,
                "path": path,
                "query_string": parsed_url.query.encode(),
                "headers": [(k.lower().encode(), v.encode()) for k, v in self.headers.items()],
                "body": body or b"",
            }
            
            # Create ASGI message
            message = {
                "type": "http.request",
                "body": body or b"",
                "more_body": False,
            }
            
            # Run the FastAPI app
            response = asyncio.run(self._run_fastapi(scope, message))
            
            # Send response
            self._send_response(response)
            
        except Exception as e:
            self._send_error_response(str(e))
    
    async def _run_fastapi(self, scope, message):
        """Run FastAPI app and get response"""
        response_data = {}
        
        async def receive():
            return message
        
        async def send(message):
            if message["type"] == "http.response.start":
                response_data["status"] = message["status"]
                response_data["headers"] = message["headers"]
            elif message["type"] == "http.response.body":
                response_data["body"] = message.get("body", b"")
        
        await app(scope, receive, send)
        return response_data
    
    def _send_response(self, response_data):
        """Send HTTP response"""
        status = response_data.get("status", 200)
        headers = response_data.get("headers", [])
        body = response_data.get("body", b"")
        
        # Send status
        self.send_response(status)
        
        # Send headers
        for header_name, header_value in headers:
            self.send_header(header_name.decode(), header_value.decode())
        
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        
        self.end_headers()
        
        # Send body
        if body:
            self.wfile.write(body)
    
    def _send_error_response(self, error_message):
        """Send error response"""
        self.send_response(500)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        error_response = {
            "error": "Internal Server Error",
            "message": error_message
        }
        self.wfile.write(json.dumps(error_response).encode())


# Export the handler class for Vercel
handler = VercelHandler