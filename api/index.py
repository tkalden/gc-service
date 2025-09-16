"""
Vercel serverless function entry point - Simple ASGI approach
"""

# Import the FastAPI app from main.py
from main import app

# Export the ASGI app directly for Vercel
handler = app