# Security Setup Guide

## Environment Variables Setup

### 1. Backend (gc-service)

Create a `.env` file in the `gc-service` directory:

```bash
cp env.example .env
```

Then edit `.env` with your actual values:

```env
# Supabase Configuration (REQUIRED)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8081,http://localhost:8082
```

### 2. Frontend (gc-ui)

Create a `.env` file in the `gc-ui` directory:

```bash
cp env.example .env
```

Then edit `.env` with your actual values:

```env
# Weather API (Optional)
EXPO_PUBLIC_WEATHER_API_KEY=your-openweathermap-api-key-here

# Backend API URL
EXPO_PUBLIC_API_URL=http://localhost:8000
```

## Getting Required Keys

### Supabase Keys

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to Settings > API
4. Copy:
   - Project URL → `SUPABASE_URL`
   - Service role key → `SUPABASE_SERVICE_KEY`

### Weather API Key (Optional)

1. Go to [OpenWeatherMap](https://openweathermap.org/api)
2. Sign up for free account
3. Get your API key
4. Add to `EXPO_PUBLIC_WEATHER_API_KEY`

## Security Checklist

- [ ] Never commit `.env` files to git
- [ ] Use different keys for development/production
- [ ] Regularly rotate API keys
- [ ] Use service role keys only on server-side
- [ ] Use anon keys for client-side (when needed)
- [ ] Enable Row Level Security (RLS) in Supabase
- [ ] Validate all environment variables on startup

## Production Deployment

For production:

1. Set environment variables in your deployment platform
2. Use secrets management (AWS Secrets Manager, etc.)
3. Enable HTTPS only
4. Restrict CORS origins to your domain
5. Use production Supabase instance
