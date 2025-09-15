"""
Vercel serverless function entry point for FastAPI app
"""

from main import app

# Export the FastAPI app for Vercel
handler = app
