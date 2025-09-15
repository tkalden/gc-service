#!/bin/bash

# Vercel Deployment Script for GC-Service
echo "🚀 Starting Vercel deployment for GC-Service..."

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo "❌ Vercel CLI not found. Installing..."
    npm install -g vercel
fi

# Check if we're logged in to Vercel
echo "🔐 Checking Vercel authentication..."
vercel whoami || vercel login

# Set environment variables for Vercel
echo "⚙️  Setting up environment variables..."

# You'll need to set these in Vercel dashboard or via CLI
echo "📝 Please ensure these environment variables are set in Vercel:"
echo "   - SUPABASE_URL"
echo "   - SUPABASE_SERVICE_KEY"
echo "   - BACKEND_URL (optional, will use Vercel URL)"
echo "   - ALLOWED_ORIGINS (optional, will use defaults)"

# Deploy to Vercel
echo "📦 Deploying to Vercel..."
vercel --prod

echo "✅ Deployment completed!"
echo "📱 Your API will be available at the provided Vercel URL"
echo "🔗 Update your frontend configuration to use the new API URL"
