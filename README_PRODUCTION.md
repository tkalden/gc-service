# GC-Service - Production Ready Backend

A production-ready FastAPI backend for the Closet App with proper organization, security, and deployment configurations.

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
│   ├── utils/                    # Utility functions
│   └── main.py                  # Application factory
├── config/                       # Configuration management
│   ├── settings.py              # Main settings
│   └── environments/            # Environment-specific configs
├── tests/                        # Test files
├── scripts/                      # Deployment scripts
├── docs/                         # Documentation
├── logs/                         # Log files (created at runtime)
├── requirements-production.txt   # Production dependencies
├── vercel.json                  # Vercel deployment config
└── main_new.py                  # New entry point
```

## 🚀 Quick Start

### 1. Environment Setup

```bash
# Copy environment template
cp env.production .env

# Edit .env with your actual values
nano .env
```

### 2. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install production dependencies
pip install -r requirements-production.txt
```

### 3. Run the Application

```bash
# Development
python main_new.py

# Or with uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `ENVIRONMENT` | Environment (development/staging/production) | Yes | development |
| `SUPABASE_URL` | Supabase project URL | Yes | - |
| `SUPABASE_SERVICE_KEY` | Supabase service key | Yes | - |
| `SECRET_KEY` | JWT secret key | Yes | - |
| `ALLOWED_ORIGINS` | CORS allowed origins | No | localhost origins |
| `LOG_LEVEL` | Logging level | No | INFO |
| `RATE_LIMIT_REQUESTS` | Rate limit per minute | No | 100 |

### Environment-Specific Settings

- **Development**: Debug enabled, verbose logging, relaxed CORS
- **Staging**: Debug disabled, info logging, restricted CORS
- **Production**: Debug disabled, warning logging, strict CORS, rate limiting

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

### Metrics (Optional)

- Request/response times
- Error rates
- Rate limit hits
- Custom business metrics

## 🚀 Deployment

### Vercel Deployment

```bash
# Install Vercel CLI
npm install -g vercel

# Login to Vercel
vercel login

# Deploy
vercel --prod
```

### Environment Variables in Vercel

Set these in your Vercel dashboard:

```
SUPABASE_URL=your-supabase-url
SUPABASE_SERVICE_KEY=your-service-key
SECRET_KEY=your-secret-key
ENVIRONMENT=production
ALLOWED_ORIGINS=your-frontend-domain
```

### Docker Deployment (Optional)

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements-production.txt .
RUN pip install -r requirements-production.txt

COPY . .
EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 🧪 Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/

# Run with coverage
pytest --cov=app tests/
```

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

## 🔍 API Documentation

### Interactive Documentation

- **Swagger UI**: `/docs` (development only)
- **ReDoc**: `/redoc` (development only)
- **OpenAPI Schema**: `/openapi.json`

### API Endpoints

#### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/logout` - User logout
- `GET /api/v1/auth/me` - Get current user

#### Clothing Items
- `GET /api/v1/clothes` - Get all clothing items
- `POST /api/v1/clothes` - Create clothing item
- `GET /api/v1/clothes/{id}` - Get specific item
- `PUT /api/v1/clothes/{id}` - Update item
- `DELETE /api/v1/clothes/{id}` - Delete item

#### Outfits
- `GET /api/v1/outfits` - Get user outfits
- `POST /api/v1/outfits` - Create outfit
- `GET /api/v1/outfits/{id}` - Get specific outfit
- `PUT /api/v1/outfits/{id}` - Update outfit
- `DELETE /api/v1/outfits/{id}` - Delete outfit

#### File Upload
- `POST /api/v1/upload/unified` - Upload images
- `GET /api/v1/upload/images/{path}` - Serve images

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

## 📝 Migration Guide

### From Old Structure

1. **Update Imports**: Change imports to use new structure
2. **Environment Variables**: Use new environment variable names
3. **Configuration**: Use new settings system
4. **Error Handling**: Use new exception system

### Breaking Changes

- API prefix changed to `/api/v1`
- Some endpoint paths updated
- Response format standardized
- Error response format changed

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
