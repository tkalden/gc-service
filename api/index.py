"""
Vercel serverless function entry point for FastAPI app
"""

from app.main import app

# Export the FastAPI app for Vercel
handler = app
