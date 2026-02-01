# GC-Service - Closet App Backend

A production-ready FastAPI backend for the Closet App with advanced virtual try-on capabilities, organized structure, and comprehensive security features.

## 🚀 Features

- 🎨 **AI-Powered Virtual Try-On** - Replicate API integration with IDM-VTON for realistic results
- 👤 **Avatar Processing** - MediaPipe pose estimation and body segmentation
- 🗄️ **Supabase Integration** - Secure database and storage with RLS
- 📸 **Advanced Image Processing** - Background removal, cloth segmentation, pose detection
- 🔒 **Security First** - JWT authentication, rate limiting, input validation
- 📚 **Auto Documentation** - Swagger UI included
- 🌐 **CORS Support** - Ready for React Native app
- ⚡ **High Performance** - Supports 1000+ concurrent users
- 🏗️ **Organized Structure** - Clean, maintainable codebase

## 🏗️ Project Structure

```
gc-service/
├── app/                          # Application code
│   ├── api/                      # API endpoints
│   │   └── v1/                   # API version 1
│   │       ├── auth/             # Authentication endpoints
│   │       ├── clothes/          # Clothing items endpoints
│   │       ├── outfits/          # Outfits endpoints
│   │       ├── avatar/           # Avatar endpoints
│   │       ├── upload/           # File upload endpoints
│   │       └── admin/            # Admin endpoints
│   ├── core/                     # Core functionality
│   │   ├── logging.py           # Logging configuration
│   │   ├── security.py          # Security middleware
│   │   └── exceptions.py        # Custom exceptions
│   ├── models/                   # Pydantic models
│   ├── services/                 # Business logic services
│   ├── middleware/               # Custom middleware
│   └── utils/                    # Utility functions
├── config/                       # Configuration management
│   ├── settings.py              # Main settings
│   └── environments/            # Environment-specific configs
├── tests/                        # Test files
├── scripts/                      # Deployment scripts
├── docs/                         # Documentation
├── logs/                         # Log files (created at runtime)
├── requirements.txt              # Dependencies
├── vercel.json                  # Vercel deployment config
├── main.py                      # FastAPI application
└── api/index.py                 # Vercel entry point
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp env.example .env

# Edit .env with your actual values
nano .env
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Run the Application

```bash


# Or using the shell script
./startbackend.sh
```

The API will be available at:
- **API**: http://localhost:8000
- **Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## 🔧 Configuration

### Environment Variables

| Variable                 | Description                                  | Required | Default           |
| ------------------------ | -------------------------------------------- | -------- | ----------------- |
| `ENVIRONMENT`            | Environment (development/staging/production) | Yes      | development       |
| `SUPABASE_URL`           | Supabase project URL                         | Yes      | -                 |
| `SUPABASE_SERVICE_KEY`   | Supabase service key                         | Yes      | -                 |
| `SECRET_KEY`             | JWT secret key                               | Yes      | -                 |
| `REPLICATE_API_TOKEN`    | Replicate API token for virtual try-on       | No*      | -                 |
| `REPLICATE_TRYON_MODEL`  | Replicate model version                      | No       | IDM-VTON default  |
| `ALLOWED_ORIGINS`        | CORS allowed origins                         | No       | localhost origins |
| `LOG_LEVEL`              | Logging level                                | No       | INFO              |
| `RATE_LIMIT_REQUESTS`    | Rate limit per minute                        | No       | 100               |

*Required for virtual try-on functionality

### Getting Your Supabase Keys

1. Go to [Supabase Dashboard](https://app.supabase.com)
2. Select your project
3. Go to Settings > API
4. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **Service role key** → `SUPABASE_SERVICE_KEY` (⚠️ Keep this secret!)

### Getting Your Replicate API Token

1. Sign up at [Replicate](https://replicate.com)
2. Go to your [Account Settings](https://replicate.com/account)
3. Copy your API token
4. Add to `.env`: `REPLICATE_API_TOKEN=your-token-here`

**Note**: Virtual try-on will fall back to basic overlay if Replicate is not configured.

For detailed Replicate integration documentation, see [docs/REPLICATE_INTEGRATION.md](docs/REPLICATE_INTEGRATION.md)

### Security Checklist

- [ ] Never commit `.env` files to git
- [ ] Use different keys for development/production
- [ ] Regularly rotate API keys
- [ ] Use service role keys only on server-side
- [ ] Enable Row Level Security (RLS) in Supabase

## 🔍 API Documentation

### Interactive Documentation

- **Swagger UI**: `/docs` (development only)
- **ReDoc**: `/redoc` (development only)
- **OpenAPI Schema**: `/openapi.json`

### API Endpoints

#### Authentication (`/api/v1/auth/`)
- `POST /register` - User registration
- `POST /login` - User login
- `POST /logout` - User logout
- `GET /me` - Get current user
- `POST /reset-password` - Password reset
- `POST /refresh` - Refresh token

#### Clothing Items (`/api/v1/clothes/`)
- `GET /` - Get all clothing items
- `POST /` - Create clothing item
- `GET /{id}` - Get specific item
- `PUT /{id}` - Update item
- `DELETE /{id}` - Delete item
- `GET /category/{category}` - Get items by category
- `GET /season/{season}` - Get items by season

#### Outfits (`/api/v1/outfits/`)
- `GET /` - Get user outfits (with filtering)
- `POST /` - Create outfit
- `POST /upload` - Create outfit with images
- `POST /generate` - Generate outfit from clothing items
- `GET /{id}` - Get specific outfit
- `GET /{id}/details` - Get outfit with clothing items
- `PUT /{id}` - Update outfit
- `DELETE /{id}` - Delete outfit
- `POST /filter` - Advanced outfit filtering

#### Avatar (`/api/v1/avatar/`)
- `POST /upload` - Upload avatar
- `GET /` - Get user avatar
- `GET /{id}` - Get avatar by ID
- `POST /try-on` - Virtual try-on
- `GET /try-on/history` - Get try-on history
- `GET /service/status` - Get service status

#### File Upload (`/api/v1/upload/`)
- `POST /unified` - Upload images
- `GET /images/{path}` - Serve images

#### Admin (`/api/v1/admin/`)
- `POST /remove-background/url` - Remove background from URL
- `POST /remove-background/base64` - Remove background from base64
- `GET /remove-background/status` - Get background removal status
- `POST /crop-image/url` - Crop cloth image from URL
- `POST /crop-image/base64` - Crop cloth image from base64

## 📊 Data Models

### ClothingItem

```json
{
  "id": "uuid",
  "name": "T-Shirt",
  "category": "tops",
  "seasons": ["spring", "summer"],
  "image_path": "user-clothes/image.jpg",
  "is_user_added": true,
  "added_date": "2025-01-01T00:00:00Z",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z",
  "metadata": {}
}
```

### Categories

- `tops`
- `bottoms`
- `shoes`
- `accessories`
- `dresses`
- `outerwear`

### Seasons

- `spring`
- `summer`
- `fall`
- `winter`

## 🛡️ Security Features

### Implemented Security Measures

1. **Authentication & Authorization**
   - JWT-based authentication
   - Role-based access control
   - Token refresh mechanism

2. **Input Validation**
   - Pydantic model validation
   - File type and size validation
   - SQL injection prevention

3. **Security Headers**
   - X-Content-Type-Options
   - X-Frame-Options
   - X-XSS-Protection
   - HSTS (production)

4. **Rate Limiting**
   - Per-IP rate limiting
   - Configurable limits
   - Automatic cleanup

5. **Error Handling**
   - Structured error responses
   - No sensitive data exposure
   - Comprehensive logging

## 📈 Performance Optimization

### Implemented Optimizations

1. **Database**
   - Connection pooling
   - Query optimization
   - Indexed queries

2. **Caching**
   - Response caching
   - Database query caching
   - Static file caching

3. **File Handling**
   - Streaming uploads
   - Image optimization
   - CDN integration

4. **API Design**
   - Pagination
   - Field selection
   - Compression

## 🚀 Deployment

### Vercel Deployment

#### Prerequisites
1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Vercel CLI**: Install globally with `npm install -g vercel`
3. **Environment Variables**: Have your Supabase credentials ready

#### Quick Deployment

**Option 1: Using the Deployment Script**
```bash
# Make the script executable
chmod +x deploy-vercel.sh

# Run the deployment script
./deploy-vercel.sh
```

**Option 2: Manual Deployment**
```bash
# Install Vercel CLI if not already installed
npm install -g vercel

# Login to Vercel
vercel login

# Deploy to Vercel
vercel --prod
```

#### Environment Variables in Vercel

Set these in your Vercel dashboard:

**Required Variables:**
- `SUPABASE_URL`: Your Supabase project URL
- `SUPABASE_SERVICE_KEY`: Your Supabase service role key
- `SECRET_KEY`: JWT secret key
- `ENVIRONMENT`: Set to "production"

**Optional Variables:**
- `BACKEND_URL`: Your Vercel deployment URL (auto-generated)
- `ALLOWED_ORIGINS`: Comma-separated list of allowed origins
- `DEBUG`: Set to "false" for production

**Setting Environment Variables:**

Via Vercel Dashboard:
1. Go to your project in Vercel dashboard
2. Navigate to Settings → Environment Variables
3. Add each variable with appropriate values

Via Vercel CLI:
```bash
vercel env add SUPABASE_URL
vercel env add SUPABASE_SERVICE_KEY
vercel env add ALLOWED_ORIGINS
```

#### Post-Deployment Steps

1. **Update Frontend Configuration**: Update your React Native app's API URL to point to your Vercel deployment
2. **Test Endpoints**: Verify all API endpoints work correctly
3. **Monitor Logs**: Check Vercel function logs for any issues

#### Troubleshooting

**Common Issues:**
1. **Function Timeout**: Increase timeout in vercel.json if needed
2. **Memory Issues**: Some ML operations might need more memory
3. **Cold Starts**: First request might be slower due to serverless nature

**Performance Optimization:**
1. **Keep Functions Light**: Avoid heavy imports in global scope
2. **Use Connection Pooling**: For database connections
3. **Cache Results**: Implement caching for expensive operations

#### Cost Considerations

- **Free Tier**: 100GB-hours of serverless function execution
- **Pro Tier**: $20/month for additional resources
- **Enterprise**: Custom pricing for high-volume usage

#### Monitoring

- **Vercel Dashboard**: Monitor function performance and errors
- **Logs**: Check function logs for debugging
- **Analytics**: Use Vercel Analytics for usage insights

### Docker Deployment (Optional)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Security Checklist

- [ ] Use production Supabase instance with separate credentials
- [ ] Set `DEBUG=False` in production
- [ ] Use secrets management (AWS Secrets Manager, etc.)
- [ ] Enable HTTPS only
- [ ] Restrict CORS origins to your domain
- [ ] Set up proper monitoring and logging
- [ ] Use environment-specific configuration
- [ ] Regularly update dependencies for security patches

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

## 🛠️ Development

### Code Quality

```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint code
flake8 app/ tests/
```

### Pre-commit Hooks

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install
```

## 📝 Example Usage

### Create a clothing item

```bash
curl -X POST "http://localhost:8000/api/v1/clothes" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "Blue Jeans",
    "category": "bottoms",
    "seasons": ["spring", "summer", "fall"],
    "is_user_added": true
  }'
```

### Upload an image

```bash
curl -X POST "http://localhost:8000/api/v1/upload/unified" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@image.jpg" \
  -F "bucket_name=clothing-image"
```

### Get all clothes

```bash
curl "http://localhost:8000/api/v1/clothes" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🔄 Integration with React Native App

The backend is designed to replace direct Supabase client calls in your React Native app. Update your app to call these API endpoints instead of directly accessing Supabase.

### Example Integration

```javascript
// Instead of direct Supabase calls
const response = await fetch('http://localhost:8000/api/v1/clothes', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    name: 'T-Shirt',
    category: 'tops',
    seasons: ['spring', 'summer'],
    is_user_added: true
  })
});
```

## 📊 Monitoring & Logging

### Logging Configuration

- **Structured Logging**: JSON format in production
- **Log Levels**: DEBUG, INFO, WARNING, ERROR
- **Log Rotation**: 10MB files, 5 backups
- **Separate Error Logs**: Dedicated error.log file

### Health Checks

- **Basic Health**: `/health` endpoint
- **Database Health**: Connection status
- **Service Health**: External service status

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For support and questions:

1. Check the documentation
2. Review the logs
3. Check the health endpoints
4. Contact the development team

## 🔄 Updates

### Version 1.0.0
- Initial production-ready release
- Organized project structure
- Comprehensive security features
- Production deployment configurations
- Monitoring and logging setup
- Clean, maintainable codebase with no duplicate endpoints