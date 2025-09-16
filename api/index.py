"""
Vercel serverless function entry point
"""

# Import the FastAPI app
from app.main import app

# Export the FastAPI app for Vercel
handler = app