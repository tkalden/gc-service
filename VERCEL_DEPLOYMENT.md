# Vercel Deployment Guide for GC-Service

This guide will help you deploy your FastAPI backend to Vercel.

## Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI**: Install globally with `npm install -g vercel`
3. **Environment Variables**: Have your Supabase credentials ready

## Quick Deployment

### Option 1: Using the Deployment Script

```bash
# Make the script executable (already done)
chmod +x deploy-vercel.sh

# Run the deployment script
./deploy-vercel.sh
```

### Option 2: Manual Deployment

```bash
# Install Vercel CLI if not already installed
npm install -g vercel

# Login to Vercel
vercel login

# Deploy to Vercel
vercel --prod
```

## Environment Variables Setup

You need to set these environment variables in Vercel:

### Required Variables
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_KEY`: Your Supabase service role key

### Optional Variables
- `BACKEND_URL`: Your Vercel deployment URL (auto-generated)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins
- `DEBUG`: Set to "false" for production

### Setting Environment Variables

#### Via Vercel Dashboard:
1. Go to your project in Vercel dashboard
2. Navigate to Settings → Environment Variables
3. Add each variable with appropriate values

#### Via Vercel CLI:
```bash
vercel env add SUPABASE_URL
vercel env add SUPABASE_SERVICE_KEY
vercel env add ALLOWED_ORIGINS
```

## Project Structure

The following files are created for Vercel deployment:

```
gc-service/
├── vercel.json              # Vercel configuration
├── api/
│   └── index.py            # Serverless function entry point
├── main-vercel.py          # Vercel-optimized main file
├── vercel-config.py        # Vercel-specific configuration
├── requirements-vercel.txt # Optimized requirements
├── .vercelignore          # Files to ignore during deployment
└── deploy-vercel.sh       # Deployment script
```

## Configuration Details

### vercel.json
- Configures the Python runtime
- Sets up routing for all requests to the FastAPI app
- Defines environment variables
- Sets function timeout to 30 seconds

### requirements-vercel.txt
- Optimized for serverless deployment
- Excludes heavy ML dependencies by default
- Includes only essential packages

### .vercelignore
- Excludes development files, checkpoints, and large files
- Reduces deployment size and time

## Post-Deployment

1. **Update Frontend Configuration**: Update your React Native app's API URL to point to your Vercel deployment
2. **Test Endpoints**: Verify all API endpoints work correctly
3. **Monitor Logs**: Check Vercel function logs for any issues

## Troubleshooting

### Common Issues

1. **Function Timeout**: Increase timeout in vercel.json if needed
2. **Memory Issues**: Some ML operations might need more memory
3. **Cold Starts**: First request might be slower due to serverless nature

### Performance Optimization

1. **Keep Functions Light**: Avoid heavy imports in global scope
2. **Use Connection Pooling**: For database connections
3. **Cache Results**: Implement caching for expensive operations

## Monitoring

- **Vercel Dashboard**: Monitor function performance and errors
- **Logs**: Check function logs for debugging
- **Analytics**: Use Vercel Analytics for usage insights

## Cost Considerations

- **Free Tier**: 100GB-hours of serverless function execution
- **Pro Tier**: $20/month for additional resources
- **Enterprise**: Custom pricing for high-volume usage

## Security

- **Environment Variables**: Never commit sensitive data
- **CORS**: Configure allowed origins properly
- **Rate Limiting**: Consider implementing rate limiting
- **Authentication**: Ensure proper JWT validation

## Next Steps

1. Deploy to Vercel using the provided script
2. Update your frontend to use the new API URL
3. Test all functionality
4. Set up monitoring and alerts
5. Configure custom domain if needed
