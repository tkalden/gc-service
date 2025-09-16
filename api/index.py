"""
Vercel serverless function entry point
"""

from http.server import BaseHTTPRequestHandler
import json
import os

class handler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        """Send CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
    
    def _send_json_response(self, data, status_code=200):
        """Send JSON response with CORS headers"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/':
            response = {
                "message": "Closet App API is running", 
                "status": "ok",
                "version": "1.0.0",
                "endpoints": {
                    "health": "/health",
                    "auth": "/api/v1/auth",
                    "clothes": "/api/v1/clothes",
                    "outfits": "/api/v1/outfits",
                    "upload": "/api/v1/upload"
                }
            }
            self._send_json_response(response)
            
        elif self.path == '/health':
            response = {
                "status": "healthy", 
                "service": "closet-app-api",
                "environment": os.getenv("ENVIRONMENT", "production")
            }
            self._send_json_response(response)
            
        elif self.path.startswith('/api/v1/auth'):
            # Auth endpoints
            if self.path == '/api/v1/auth/me':
                self._send_json_response({"message": "Auth endpoint - requires authentication"})
            else:
                self._send_json_response({"message": "Auth endpoints available", "endpoints": ["/register", "/login", "/me"]})
                
        elif self.path.startswith('/api/v1/clothes'):
            # Clothes endpoints
            self._send_json_response({"message": "Clothes endpoints available", "endpoints": ["GET /", "POST /", "PUT /{id}", "DELETE /{id}"]})
            
        elif self.path.startswith('/api/v1/outfits'):
            # Outfits endpoints
            self._send_json_response({"message": "Outfits endpoints available", "endpoints": ["GET /", "POST /", "PUT /{id}", "DELETE /{id}"]})
            
        else:
            self._send_json_response({"error": "Not found", "path": self.path}, 404)
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests for CORS"""
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path.startswith('/api/v1/auth'):
            if self.path == '/api/v1/auth/register':
                self._send_json_response({"message": "Registration endpoint - requires implementation"})
            elif self.path == '/api/v1/auth/login':
                self._send_json_response({"message": "Login endpoint - requires implementation"})
            else:
                self._send_json_response({"message": "Auth POST endpoint", "path": self.path})
                
        elif self.path.startswith('/api/v1/clothes'):
            self._send_json_response({"message": "Clothes POST endpoint", "path": self.path})
            
        elif self.path.startswith('/api/v1/outfits'):
            self._send_json_response({"message": "Outfits POST endpoint", "path": self.path})
            
        elif self.path.startswith('/api/v1/upload'):
            self._send_json_response({"message": "Upload POST endpoint", "path": self.path})
            
        else:
            self._send_json_response({"message": "POST request received", "path": self.path})